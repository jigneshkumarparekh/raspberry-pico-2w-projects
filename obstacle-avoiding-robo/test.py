"""
Combined single-file version for testing on the Pico.

This merges `pins.py`, `drive_and_avoid.py` and the `main.py` launcher
into one self-contained script named `test.py`.

Adjust pin constants below if your wiring differs before running.
"""

from machine import Pin, PWM
import time

# --- pins.py content ---
# H-Bridge (TB6612FNG) standby
STBY_PIN = 12  # GPIO12 (Pin 18)

# Left motor (Channel A)
LEFT_PWM = 15  # GPIO15 (Pin 22)
LEFT_IN1 = 14  # GPIO14 (Pin 20)
LEFT_IN2 = 13  # GPIO13 (Pin 19)

# Right motor (Channel B)
RIGHT_PWM = 18  # GPIO18 (Pin 24)
RIGHT_IN1 = 19  # GPIO19 (Pin 25)
RIGHT_IN2 = 20  # GPIO20 (Pin 26)

# Ultrasonic sensor pins
TRIG_PIN = 16  # GPIO16 (Pin 21)
ECHO_PIN = 17  # GPIO17 (Pin 22)

# Behavior tuning constants
THRESHOLD_CM = 30        # distance (cm) to trigger avoidance
CRUISE_SPEED = 60        # percent (0-100)
REVERSE_MS = 350         # how long to reverse when obstacle found (ms)
TURN_MS = 400            # how long to turn to avoid obstacle (ms)
LOOP_DELAY_MS = 60       # main loop delay (ms)


# --- drive_and_avoid.py content (adapted to use local constants) ---
# PWM configuration
PWM_FREQ = 10000
MAX_DUTY = 65535


# Simple logger helper
def _log(tag, msg=""):
    try:
        ts = time.ticks_ms()
    except Exception:
        # fallback for non-MicroPython environments
        ts = int(time.time() * 1000)
    print("[{}ms] {}: {}".format(ts, tag, msg))


class Motor:
    def __init__(self, pwm_pin, in1, in2):
        _log("Motor.__init__", "pwm=%s in1=%s in2=%s" % (pwm_pin, in1, in2))
        self.pwm = PWM(Pin(pwm_pin))
        self.pwm.freq(PWM_FREQ)
        self.pwm.duty_u16(0)
        self.in1 = Pin(in1, Pin.OUT)
        self.in2 = Pin(in2, Pin.OUT)
        self.in1.off()
        self.in2.off()

    def forward(self, speed=100):
        speed = max(0, min(100, speed))
        _log("Motor.forward", "speed=%s" % speed)
        self.in1.on()
        self.in2.off()
        duty = int((speed / 100) * MAX_DUTY)
        self.pwm.duty_u16(duty)

    def reverse(self, speed=100):
        speed = max(0, min(100, speed))
        _log("Motor.reverse", "speed=%s" % speed)
        self.in1.off()
        self.in2.on()
        duty = int((speed / 100) * MAX_DUTY)
        self.pwm.duty_u16(duty)

    def stop(self):
        _log("Motor.stop", "")
        self.pwm.duty_u16(0)
        self.in1.off()
        self.in2.off()

    def brake(self):
        _log("Motor.brake", "")
        self.in1.on()
        self.in2.on()
        self.pwm.duty_u16(0)


class HBridge:
    def __init__(self, stby_pin):
        _log("HBridge.__init__", "stby=%s" % stby_pin)
        self.stby = Pin(stby_pin, Pin.OUT)
        self.enable()

    def enable(self):
        _log("HBridge.enable", "")
        self.stby.on()

    def disable(self):
        _log("HBridge.disable", "")
        self.stby.off()


class HCSR04:
    def __init__(self, trigger_pin, echo_pin):
        _log("HCSR04.__init__", "trig=%s echo=%s" % (trigger_pin, echo_pin))
        self.trigger = Pin(trigger_pin, Pin.OUT)
        self.echo = Pin(echo_pin, Pin.IN)
        self.trigger.value(0)

    def distance_cm(self):
        _log("HCSR04.distance_cm", "triggering")
        self.trigger.value(0)
        time.sleep_us(2)
        self.trigger.value(1)
        time.sleep_us(10)
        self.trigger.value(0)

        timeout = time.ticks_us() + 50000

        while self.echo.value() == 0:
            if time.ticks_us() > timeout:
                _log("HCSR04.distance_cm", "timeout waiting for echo high")
                return None

        start = time.ticks_us()

        while self.echo.value() == 1:
            if time.ticks_us() > timeout:
                _log("HCSR04.distance_cm", "timeout waiting for echo low")
                return None

        end = time.ticks_us()
        duration = end - start
        distance = (duration * 0.0343) / 2
        _log("HCSR04.distance_cm", "distance_cm=%.2f" % distance)
        return distance


# Initialize hardware
hbridge = HBridge(STBY_PIN)
left = Motor(LEFT_PWM, LEFT_IN1, LEFT_IN2)
right = Motor(RIGHT_PWM, RIGHT_IN1, RIGHT_IN2)
sensor = HCSR04(TRIG_PIN, ECHO_PIN)


def forward(speed=None):
    s = CRUISE_SPEED if speed is None else speed
    _log("forward", "speed=%s" % s)
    left.forward(s)
    right.forward(s)


def stop():
    _log("stop", "")
    left.stop()
    right.stop()


def reverse(duration_ms, speed=60):
    _log("reverse", "duration_ms=%s speed=%s" % (duration_ms, speed))
    left.reverse(speed)
    right.reverse(speed)
    time.sleep_ms(duration_ms)
    stop()


def turn_left(duration_ms, speed=60):
    # left wheel reverse, right wheel forward -> rotate left
    _log("turn_left", "duration_ms=%s speed=%s" % (duration_ms, speed))
    left.reverse(speed)
    right.forward(speed)
    time.sleep_ms(duration_ms)
    stop()


def turn_right(duration_ms, speed=60):
    _log("turn_right", "duration_ms=%s speed=%s" % (duration_ms, speed))
    left.forward(speed)
    right.reverse(speed)
    time.sleep_ms(duration_ms)
    stop()


def avoid_if_needed(threshold_cm=None):
    thresh = THRESHOLD_CM if threshold_cm is None else threshold_cm
    dist = sensor.distance_cm()
    _log("avoid_if_needed", "measured=%s thresh=%s" % (dist, thresh))
    if dist is None:
        return False
    if dist < thresh:
        # Basic avoidance: stop, reverse briefly, turn, then resume
        _log("avoid_if_needed", "obstacle detected %.2f cm" % dist)
        stop()
        time.sleep_ms(50)
        reverse(REVERSE_MS, speed=60)
        # Alternate turns to avoid getting stuck
        turn_left(TURN_MS, speed=55)
        forward(CRUISE_SPEED)
        return True
    return False


def run_forever():
    try:
        _log("run_forever", "Starting cruising at %s%%" % CRUISE_SPEED)
        forward(CRUISE_SPEED)
        while True:
            avoided = avoid_if_needed()
            if avoided:
                _log("run_forever", "performed avoidance")
            # keep loop responsive
            time.sleep_ms(LOOP_DELAY_MS)

    except KeyboardInterrupt:
        _log("run_forever", "Stopping—keyboard interrupt")
        stop()
        hbridge.disable()


if __name__ == "__main__":
    run_forever()
