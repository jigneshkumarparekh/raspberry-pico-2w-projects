"""
Simplified test script: start motors; if obstacle detected, reverse and resume;
stop after 3 seconds total runtime.

Designed for quick testing on the Pico. Keep wiring constants in the
pins section in sync with your hardware.
"""

from machine import Pin, PWM
import utime
from utime import sleep, sleep_us


# --- MOTOR PINS ---
STBY_PIN = 12
LEFT_PWM = 15
LEFT_IN1 = 14
LEFT_IN2 = 13

# NOT USING RIGHT MOTOR
# RIGHT_PWM = 18
# RIGHT_IN1 = 19
# RIGHT_IN2 = 20

# HSR04
TRIG_PIN = 16
ECHO_PIN = 17

# behavior
THRESHOLD_CM = 50
CRUISE_SPEED = 60
REVERSE_MS = 1000
LOOP_DELAY_MS = 60

# PWM
PWM_FREQ = 10000
MAX_DUTY = 65535


def _log(tag, msg=""):
    try:
        ts = utime.ticks_ms()
    except Exception:
        ts = int(utime.time() * 1000)
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
        # Trigger pulse
        self.trigger.low()
        sleep_us(200)
        self.trigger.high()
        sleep_us(10)
        self.trigger.low()

        # Wait for echo HIGH
        start_wait = utime.ticks_us()
        while self.echo.value() == 0:
            if utime.ticks_diff(utime.ticks_us(), start_wait) > 30000:
                return None

        start = utime.ticks_us()

        # Wait for echo LOW
        while self.echo.value() == 1:
            if utime.ticks_diff(utime.ticks_us(), start) > 30000:
                return None

        end = utime.ticks_us()

        duration = utime.ticks_diff(end, start)
        distance = (duration * 0.0343) / 2
        if distance > 300:
            return None
        return distance



# initialize
hbridge = HBridge(STBY_PIN)
left = Motor(LEFT_PWM, LEFT_IN1, LEFT_IN2)
# right = Motor(RIGHT_PWM, RIGHT_IN1, RIGHT_IN2)
sensor = HCSR04(TRIG_PIN, ECHO_PIN)
led = Pin("LED", Pin.OUT)


def blink_led(times=3, delay=0.5):
    """Blink the onboard LED as a startup indicator."""
    _log("blink_led", "starting with %d blinks" % times)
    for _ in range(times):
        led.on()
        sleep(delay)
        led.off()
        sleep(delay)
    _log("blink_led", "finished")


def forward(speed=None):
    s = CRUISE_SPEED if speed is None else speed
    _log("forward", "speed=%s" % s)
    left.forward(s)
    # right.forward(s)


def stop():
    _log("stop", "")
    left.stop()
    # right.stop()


def reverse(duration_ms, speed=60):
    _log("reverse", "duration_ms=%s speed=%s" % (duration_ms, speed))
    left.reverse(speed)
    # right.reverse(speed)
    utime.sleep_ms(duration_ms)
    stop()


def simplified_run(total_ms=3000):
    _log("simplified_run", "start total_ms=%s" % total_ms)
    blink_led(times=3, delay=0.5)
    start = utime.ticks_ms()
    forward(CRUISE_SPEED)
    try:
        while utime.ticks_diff(utime.ticks_ms(), start) < total_ms:
            dist = sensor.distance_cm()
            if dist is None:
                # sensor timed out — just continue
                utime.sleep_ms(LOOP_DELAY_MS)
                continue
            _log("simplified_run", "measured=%.2fcm" % dist)
            if dist < THRESHOLD_CM:
                _log("simplified_run", "obstacle detected %.2fcm — stopping and reversing" % dist)
                stop()
                utime.sleep_ms(1000)
                reverse(REVERSE_MS, CRUISE_SPEED)
            utime.sleep_ms(LOOP_DELAY_MS)
    except KeyboardInterrupt:
        _log("simplified_run", "keyboard interrupt")
    finally:
        stop()
        led.off()
        hbridge.disable()
        _log("simplified_run", "finished")


if __name__ == "__main__":
    simplified_run(total_ms=20000)
