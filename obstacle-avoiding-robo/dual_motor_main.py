"""
Dual-motor obstacle-avoiding robot: left and right wheels, turn-based avoidance.
Start motors; if obstacle detected, ramp stop, reverse until safe, turn (left or right), then resume forward.
Pin and behavior constants at the top should match your hardware.
"""

from machine import Pin, PWM
import utime
from utime import sleep, sleep_us


# --- MOTOR GPIO PINS ---
STBY_PIN = 12
LEFT_PWM = 15
LEFT_IN1 = 14
LEFT_IN2 = 13

RIGHT_PWM = 8 # GPIO8 (Pin 11)
RIGHT_IN1 = 7 # GPIO7 (Pin 10)
RIGHT_IN2 = 6 # GPIO6 (Pin 9)

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
MAX_REVERSE_MS = 3000  # Maximum reverse duration as safety timeout

# dual-motor: turn in place
TURN_MS = 400  # Duration of turn in place
TURN_SPEED = 55  # Speed during turn

# PWM
PWM_FREQ = 10000
MAX_DUTY = 65535

# Turn validation constants
TURN_VALIDATION_PAUSE_MS = 100  # Pause for stable sensor reading after turn
TURN_MAX_RETRIES = 2  # Max retry attempts for single turn direction

# Smoothness tuning
PRE_RAMP_DELAY_MS = 20  # Reduced from 50ms for snappier transitions
TURN_SETTLE_MS = 80  # Brief settle after stop before turning
TURN_RAMP_MS = 100  # Shorter ramp for turns (more responsive)
CRUISE_HYSTERESIS_FACTOR = 0.8  # Only re-ramp when duty below 80% of cruise


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


def _smoothstep(t):
    """Ease-in/ease-out: slow start and slow end for smoother perceived motion."""
    t = max(0, min(1, t))
    return t * t * (3 - 2 * t)


def ramp_both(left_motor, right_motor, target_speed, ramp_time_ms, ease=True):
    """
    Ramp both motors in sync to avoid drift. Uses ease-in/ease-out for smoother
    acceleration/deceleration. Both motors step together each interval.
    """
    target_speed = max(0, min(100, target_speed))
    left_target = int((target_speed / 100) * MAX_DUTY)
    right_target = left_target
    left_start = left_motor.current_duty
    right_start = right_motor.current_duty

    steps = max(1, ramp_time_ms // 20)
    step_time = ramp_time_ms // steps

    for i in range(steps):
        t = (i + 1) / steps
        t_eased = _smoothstep(t) if ease else t
        left_duty = left_start + int((left_target - left_start) * t_eased)
        right_duty = right_start + int((right_target - right_start) * t_eased)
        left_motor.pwm.duty_u16(left_duty)
        right_motor.pwm.duty_u16(right_duty)
        left_motor.current_duty = left_duty
        right_motor.current_duty = right_duty
        utime.sleep_ms(step_time)

    left_motor.current_duty = left_target
    right_motor.current_duty = right_target
    left_motor.pwm.duty_u16(left_target)
    right_motor.pwm.duty_u16(right_target)


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
        self.reading_buffer = []  # Moving-average filter buffer
        self.buffer_size = 5  # Larger buffer for smoother readings
        self.last_valid_cm = None  # Use when sensor returns None (with timeout)
        self.last_valid_time_ms = 0
        self.NONE_TIMEOUT_MS = 500  # Max age of last_valid before treating as unknown

    def _fallback_distance(self):
        """Return last valid distance if recent, else None."""
        if self.last_valid_cm is None:
            return None
        age = utime.ticks_diff(utime.ticks_ms(), self.last_valid_time_ms)
        if age <= self.NONE_TIMEOUT_MS:
            return self.last_valid_cm
        return None

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
                return self._fallback_distance()

        start = utime.ticks_us()

        # Wait for echo LOW
        while self.echo.value() == 1:
            if utime.ticks_diff(utime.ticks_us(), start) > 30000:
                return self._fallback_distance()

        end = utime.ticks_us()

        duration = utime.ticks_diff(end, start)
        distance = (duration * 0.0343) / 2
        if distance > 300:
            return self._fallback_distance()
        
        # Add to moving-average buffer
        self.reading_buffer.append(distance)
        if len(self.reading_buffer) > self.buffer_size:
            self.reading_buffer.pop(0)

        # Return average of buffered readings
        avg_distance = sum(self.reading_buffer) / len(self.reading_buffer)
        self.last_valid_cm = avg_distance
        self.last_valid_time_ms = utime.ticks_ms()
        return avg_distance


# initialize
hbridge = HBridge(STBY_PIN)
left = Motor(LEFT_PWM, LEFT_IN1, LEFT_IN2)
right = Motor(RIGHT_PWM, RIGHT_IN1, RIGHT_IN2)
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
    both_moving = left.current_duty > 0 or right.current_duty > 0
    if ramp and both_moving:
        left.in1.on()
        left.in2.off()
        right.in1.on()
        right.in2.off()
        ramp_both(left, right, s, RAMP_TIME_MS)
    else:
        left.forward(0)
        right.forward(0)
        ramp_both(left, right, s, RESUME_RAMP_MS)


def stop():
    _log("stop", "")
    left.stop()
    right.stop()


def reverse(duration_ms, speed=None):
    if speed is None:
        speed = REVERSE_SPEED
    _log("reverse", "duration_ms=%s speed=%s" % (duration_ms, speed))
    utime.sleep_ms(PRE_RAMP_DELAY_MS)
    left.reverse(0)
    right.reverse(0)
    ramp_both(left, right, speed, RAMP_TIME_MS)
    utime.sleep_ms(duration_ms)
    ramp_both(left, right, 0, DECEL_RAMP_MS)
    stop()


def reverse_until_safe(speed=None):
    """
    Reverse until distance > THRESHOLD_CM or MAX_REVERSE_MS timeout.
    Returns final distance (None if sensor timeout).
    """
    if speed is None:
        speed = REVERSE_SPEED
    _log("reverse_until_safe", "speed=%s" % speed)

    utime.sleep_ms(PRE_RAMP_DELAY_MS)
    left.reverse(0)
    right.reverse(0)
    ramp_both(left, right, speed, RAMP_TIME_MS)

    reverse_start = utime.ticks_ms()
    final_dist = None

    while True:
        elapsed = utime.ticks_diff(utime.ticks_ms(), reverse_start)
        if elapsed >= MAX_REVERSE_MS:
            _log("reverse_until_safe", "timeout after %dms" % elapsed)
            break

        dist = sensor.distance_cm()
        if dist is not None:
            final_dist = dist
            _log("reverse_until_safe", "distance=%.2fcm" % dist)
            if dist > THRESHOLD_CM:
                _log("reverse_until_safe", "safe distance reached: %.2fcm > %dcm" % (dist, THRESHOLD_CM))
                break

        utime.sleep_ms(LOOP_DELAY_MS)

    ramp_both(left, right, 0, DECEL_RAMP_MS)
    stop()

    return final_dist


def ramp_both_stop(ramp_time_ms=DECEL_RAMP_MS):
    """Synchronized ramp-down of both motors to stop."""
    ramp_both(left, right, 0, ramp_time_ms)
    stop()


def turn_left(duration_ms=None, speed=None):
    """Left reverse, right forward -> rotate left."""
    dur = TURN_MS if duration_ms is None else duration_ms
    spd = TURN_SPEED if speed is None else speed
    _log("turn_left", "duration_ms=%s speed=%s" % (dur, spd))
    utime.sleep_ms(PRE_RAMP_DELAY_MS)
    left.reverse(0)
    right.forward(0)
    ramp_both(left, right, spd, TURN_RAMP_MS)
    utime.sleep_ms(dur)
    ramp_both(left, right, 0, TURN_RAMP_MS)
    stop()


def turn_right(duration_ms=None, speed=None):
    """Left forward, right reverse -> rotate right."""
    dur = TURN_MS if duration_ms is None else duration_ms
    spd = TURN_SPEED if speed is None else speed
    _log("turn_right", "duration_ms=%s speed=%s" % (dur, spd))
    utime.sleep_ms(PRE_RAMP_DELAY_MS)
    left.forward(0)
    right.reverse(0)
    ramp_both(left, right, spd, TURN_RAMP_MS)
    utime.sleep_ms(dur)
    ramp_both(left, right, 0, TURN_RAMP_MS)
    stop()


def turn_with_validation(side='left', max_retries=2):
    """Turn until obstacle no longer directly ahead, with retry logic."""
    retry_count = 0
    
    while retry_count < max_retries:
        if side == 'left':
            turn_left(TURN_MS, TURN_SPEED)
        else:
            turn_right(TURN_MS, TURN_SPEED)
        
        utime.sleep_ms(100)  # Brief pause for stable reading
        dist = sensor.distance_cm()
        
        if dist is not None and dist >= THRESHOLD_CM:
            _log("turn_with_validation", "%s turn successful: dist=%.2fcm" % (side, dist))
            return True
        
        retry_count += 1
        _log("turn_with_validation", "turn incomplete, retrying: attempt %d/%d" % (retry_count, max_retries))
    
    _log("turn_with_validation", "%s turn exhausted retries" % side)
    return False


def simplified_run(total_ms=3000):
    _log("simplified_run", "start total_ms=%s" % total_ms)
    blink_led(times=3, delay=0.5)
    start = utime.ticks_ms()
    turn_alternate = False  # alternate turn_left / turn_right per obstacle
    forward(CRUISE_SPEED, ramp=True)
    try:
        while utime.ticks_diff(utime.ticks_ms(), start) < total_ms:
            dist = sensor.distance_cm()
            if dist is None:
                utime.sleep_ms(LOOP_DELAY_MS)
                continue
            _log("simplified_run", "measured=%.2fcm" % dist)

            adaptive_threshold = THRESHOLD_CM * ADAPTIVE_THRESHOLD_MULT
            if dist < adaptive_threshold and dist >= THRESHOLD_CM:
                distance_range = adaptive_threshold - THRESHOLD_CM
                distance_from_threshold = dist - THRESHOLD_CM
                t = distance_from_threshold / distance_range
                speed_factor = _smoothstep(t)  # Gentler curve for gradual slowdown
                adaptive_speed = int(CRUISE_SPEED * speed_factor)
                adaptive_speed = max(20, min(CRUISE_SPEED, adaptive_speed))
                _log("simplified_run", "adaptive slowdown: dist=%.2fcm speed=%d%%" % (dist, adaptive_speed))
                forward(adaptive_speed, ramp=True)
            elif dist < THRESHOLD_CM:
                _log("simplified_run", "obstacle detected %.2fcm — stop, reverse, turn with validation, resume" % dist)
                ramp_both_stop(DECEL_RAMP_MS)
                utime.sleep_ms(TURN_SETTLE_MS)
                reverse_until_safe(REVERSE_SPEED)
                
                # Try primary turn direction with validation
                primary_side = 'right' if turn_alternate else 'left'
                success = turn_with_validation(side=primary_side, max_retries=2)
                
                if not success:
                    _log("simplified_run", "primary turn direction failed, trying opposite")
                    secondary_side = 'left' if turn_alternate else 'right'
                    turn_with_validation(side=secondary_side, max_retries=1)
                
                turn_alternate = not turn_alternate
                forward(CRUISE_SPEED, ramp=True)
            elif dist >= adaptive_threshold:
                cruise_duty = int((CRUISE_SPEED / 100) * MAX_DUTY * CRUISE_HYSTERESIS_FACTOR)
                if left.current_duty < cruise_duty or right.current_duty < cruise_duty:
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
