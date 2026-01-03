"""
Integration of H-bridge motor control and HC-SR0x ultrasonic sensor.
Self-contained: minimal Motor and HCSR04 classes included so this file
can be copied to the Pico without relying on package imports.

Adjust `pins.py` to match your wiring before running.
"""

from machine import Pin, PWM
import time
import pins

# PWM configuration (match motor.py defaults)
PWM_FREQ = 10000
MAX_DUTY = 65535


class Motor:
    def __init__(self, pwm_pin, in1, in2):
        self.pwm = PWM(Pin(pwm_pin))
        self.pwm.freq(PWM_FREQ)
        self.pwm.duty_u16(0)
        self.in1 = Pin(in1, Pin.OUT)
        self.in2 = Pin(in2, Pin.OUT)
        self.in1.off()
        self.in2.off()

    def forward(self, speed=100):
        speed = max(0, min(100, speed))
        self.in1.on()
        self.in2.off()
        duty = int((speed / 100) * MAX_DUTY)
        self.pwm.duty_u16(duty)

    def reverse(self, speed=100):
        speed = max(0, min(100, speed))
        self.in1.off()
        self.in2.on()
        duty = int((speed / 100) * MAX_DUTY)
        self.pwm.duty_u16(duty)

    def stop(self):
        self.pwm.duty_u16(0)
        self.in1.off()
        self.in2.off()

    def brake(self):
        self.in1.on()
        self.in2.on()
        self.pwm.duty_u16(0)


class HBridge:
    def __init__(self, stby_pin):
        self.stby = Pin(stby_pin, Pin.OUT)
        self.enable()

    def enable(self):
        self.stby.on()

    def disable(self):
        self.stby.off()


class HCSR04:
    def __init__(self, trigger_pin, echo_pin):
        self.trigger = Pin(trigger_pin, Pin.OUT)
        self.echo = Pin(echo_pin, Pin.IN)
        self.trigger.value(0)

    def distance_cm(self):
        self.trigger.value(0)
        time.sleep_us(2)
        self.trigger.value(1)
        time.sleep_us(10)
        self.trigger.value(0)

        timeout = time.ticks_us() + 50000

        while self.echo.value() == 0:
            if time.ticks_us() > timeout:
                return None

        start = time.ticks_us()

        while self.echo.value() == 1:
            if time.ticks_us() > timeout:
                return None

        end = time.ticks_us()
        duration = end - start
        distance = (duration * 0.0343) / 2
        return distance


# Initialize hardware
hbridge = HBridge(pins.STBY_PIN)
left = Motor(pins.LEFT_PWM, pins.LEFT_IN1, pins.LEFT_IN2)
right = Motor(pins.RIGHT_PWM, pins.RIGHT_IN1, pins.RIGHT_IN2)
sensor = HCSR04(pins.TRIG_PIN, pins.ECHO_PIN)


def forward(speed=None):
    s = pins.CRUISE_SPEED if speed is None else speed
    left.forward(s)
    right.forward(s)


def stop():
    left.stop()
    right.stop()


def reverse(duration_ms, speed=60):
    left.reverse(speed)
    right.reverse(speed)
    time.sleep_ms(duration_ms)
    stop()


def turn_left(duration_ms, speed=60):
    # left wheel reverse, right wheel forward -> rotate left
    left.reverse(speed)
    right.forward(speed)
    time.sleep_ms(duration_ms)
    stop()


def turn_right(duration_ms, speed=60):
    left.forward(speed)
    right.reverse(speed)
    time.sleep_ms(duration_ms)
    stop()


def avoid_if_needed(threshold_cm=None):
    thresh = pins.THRESHOLD_CM if threshold_cm is None else threshold_cm
    dist = sensor.distance_cm()
    if dist is None:
        return False
    if dist < thresh:
        # Basic avoidance: stop, reverse briefly, turn, then resume
        stop()
        time.sleep_ms(50)
        reverse(pins.REVERSE_MS, speed=60)
        # Alternate turns to avoid getting stuck
        turn_left(pins.TURN_MS, speed=55)
        forward(pins.CRUISE_SPEED)
        return True
    return False


def run_forever():
    try:
        print("Starting obstacle-avoidance: cruising at {}%".format(pins.CRUISE_SPEED))
        forward(pins.CRUISE_SPEED)
        while True:
            avoided = avoid_if_needed()
            # keep loop responsive
            time.sleep_ms(pins.LOOP_DELAY_MS)

    except KeyboardInterrupt:
        print("Stopping—keyboard interrupt")
        stop()
        hbridge.disable()


if __name__ == "__main__":
    run_forever()
