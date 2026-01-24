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
REVERSE_MS = 350
LOOP_DELAY_MS = 60
RAMP_TIME_MS = 200
REVERSE_SPEED = 50  # Lower speed for smoother reverse
DECEL_RAMP_MS = 150  # Faster deceleration when obstacle detected
RESUME_RAMP_MS = 250  # Slower ramp when resuming forward
ADAPTIVE_THRESHOLD_MULT = 1.5  # Start slowing at 1.5x threshold
MAX_REVERSE_MS = 3000  # Maximum reverse duration as safety timeout (2 seconds)

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
        self.current_duty = 0
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
        self.current_duty = duty

    def reverse(self, speed=100):
        speed = max(0, min(100, speed))
        _log("Motor.reverse", "speed=%s" % speed)
        self.in1.off()
        self.in2.on()
        duty = int((speed / 100) * MAX_DUTY)
        self.pwm.duty_u16(duty)
        self.current_duty = duty

    def stop(self):
        _log("Motor.stop", "")
        self.pwm.duty_u16(0)
        self.current_duty = 0
        self.in1.off()
        self.in2.off()

    def ramp_stop(self, ramp_time_ms=200):
        """Gradually reduce speed to zero before stopping."""
        _log("Motor.ramp_stop", "ramp_time_ms=%s" % ramp_time_ms)
        self.ramp_speed(0, ramp_time_ms)
        self.stop()

    def ramp_speed(self, target_speed, ramp_time_ms=200):
        target_speed = max(0, min(100, target_speed))
        target_duty = int((target_speed / 100) * MAX_DUTY)
        steps = max(1, ramp_time_ms // 20)
        step_time = ramp_time_ms // steps
        duty_step = (target_duty - self.current_duty) // steps
        for _ in range(steps):
            self.current_duty += duty_step
            self.pwm.duty_u16(self.current_duty)
            utime.sleep_ms(step_time)
        self.current_duty = target_duty
        self.pwm.duty_u16(self.current_duty)


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


def forward(speed=None, ramp=True):
    s = CRUISE_SPEED if speed is None else speed
    _log("forward", "speed=%s ramp=%s" % (s, ramp))
    if ramp and left.current_duty > 0:
        # Already moving, preserve current duty and ramp to new speed
        # Set direction pins without resetting duty
        left.in1.on()
        left.in2.off()
        left.ramp_speed(s, RAMP_TIME_MS)
    else:
        # Starting from stop, ramp up
        left.forward(0)  # Set direction
        left.ramp_speed(s, RESUME_RAMP_MS)
    # right.forward(s)


def stop():
    _log("stop", "")
    left.stop()
    # right.stop()


def reverse(duration_ms, speed=None):
    if speed is None:
        speed = REVERSE_SPEED
    _log("reverse", "duration_ms=%s speed=%s" % (duration_ms, speed))
    # Brief pause before direction change for smoother transition
    utime.sleep_ms(50)
    left.reverse(0)  # set direction
    left.ramp_speed(speed, RAMP_TIME_MS)
    utime.sleep_ms(duration_ms)
    left.ramp_speed(0, RAMP_TIME_MS)
    stop()


def reverse_until_safe(speed=None):
    """
    Reverse until distance > THRESHOLD_CM or MAX_REVERSE_MS timeout.
    Returns final distance (None if sensor timeout).
    """
    if speed is None:
        speed = REVERSE_SPEED
    _log("reverse_until_safe", "speed=%s" % speed)
    
    # Brief pause before direction change for smoother transition
    utime.sleep_ms(50)
    left.reverse(0)  # set direction
    left.ramp_speed(speed, RAMP_TIME_MS)
    
    reverse_start = utime.ticks_ms()
    final_dist = None
    
    while True:
        # Check if timeout reached
        elapsed = utime.ticks_diff(utime.ticks_ms(), reverse_start)
        if elapsed >= MAX_REVERSE_MS:
            _log("reverse_until_safe", "timeout after %dms" % elapsed)
            break
        
        # Check distance
        dist = sensor.distance_cm()
        if dist is not None:
            final_dist = dist
            _log("reverse_until_safe", "distance=%.2fcm" % dist)
            if dist > THRESHOLD_CM:
                _log("reverse_until_safe", "safe distance reached: %.2fcm > %dcm" % (dist, THRESHOLD_CM))
                break
        
        # Small delay between distance checks
        utime.sleep_ms(LOOP_DELAY_MS)
    
    # Ramp down reverse speed to stop
    left.ramp_speed(0, RAMP_TIME_MS)
    stop()
    
    return final_dist


def simplified_run(total_ms=3000):
    _log("simplified_run", "start total_ms=%s" % total_ms)
    blink_led(times=3, delay=0.5)
    start = utime.ticks_ms()
    forward(CRUISE_SPEED, ramp=True)
    try:
        while utime.ticks_diff(utime.ticks_ms(), start) < total_ms:
            dist = sensor.distance_cm()
            if dist is None:
                # sensor timed out — just continue
                utime.sleep_ms(LOOP_DELAY_MS)
                continue
            _log("simplified_run", "measured=%.2fcm" % dist)
            
            # Adaptive speed reduction: slow down as obstacle approaches
            adaptive_threshold = THRESHOLD_CM * ADAPTIVE_THRESHOLD_MULT
            if dist < adaptive_threshold and dist >= THRESHOLD_CM:
                # Calculate proportional speed reduction
                # At adaptive_threshold, speed = CRUISE_SPEED
                # At THRESHOLD_CM, speed approaches 0
                distance_range = adaptive_threshold - THRESHOLD_CM
                distance_from_threshold = dist - THRESHOLD_CM
                speed_factor = distance_from_threshold / distance_range
                adaptive_speed = int(CRUISE_SPEED * speed_factor)
                adaptive_speed = max(20, min(CRUISE_SPEED, adaptive_speed))  # Clamp between 20% and cruise
                _log("simplified_run", "adaptive slowdown: dist=%.2fcm speed=%d%%" % (dist, adaptive_speed))
                forward(adaptive_speed, ramp=True)
            elif dist < THRESHOLD_CM:
                # Obstacle detected - smooth avoidance sequence
                _log("simplified_run", "obstacle detected %.2fcm — stopping and reversing" % dist)
                # 1. Decelerate gradually (ramp down instead of abrupt stop)
                left.ramp_stop(DECEL_RAMP_MS)
                # 2. Brief pause after stopping
                utime.sleep_ms(100)
                # 3. Reverse until safe distance reached
                final_dist = reverse_until_safe(REVERSE_SPEED)
                # 4. Stop at safe distance (robot already stopped by reverse_until_safe)
                if final_dist is not None and final_dist > THRESHOLD_CM:
                    _log("simplified_run", "stopped at safe distance: %.2fcm" % final_dist)
                    # Not forcing forward here, let the robot maintain its position after reverse
                elif final_dist is not None:
                    _log("simplified_run", "reverse timeout, stopped anyway (dist=%.2fcm)" % final_dist)
                    # Not forcing forward here, let the robot maintain its position after reverse
                else:
                    _log("simplified_run", "reverse timeout, stopped (sensor timeout)")
                    # Not forcing forward here, let the robot maintain its position after reverse
            elif dist >= adaptive_threshold:
                # No obstacle nearby, maintain cruise speed
                if left.current_duty < int((CRUISE_SPEED / 100) * MAX_DUTY * 0.9):
                    # Only ramp if we're not already at cruise speed
                    forward(CRUISE_SPEED, ramp=True)
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
