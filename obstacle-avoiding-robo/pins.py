"""
Central pin configuration for obstacle-avoiding robot.
Update pins to match your wiring before deploying to the Pico.
"""

# H-Bridge (TB6612FNG) standby
STBY_PIN = 12 # GPIO12 (Pin 18)

# Left motor (Channel A) - default values taken from existing motor.py
LEFT_PWM = 15 # GPIO15 (Pin 22)
LEFT_IN1 = 14 # GPIO14 (Pin 20)
LEFT_IN2 = 13 # GPIO13 (Pin 19)

# Right motor (Channel B) - choose free GPIOs (adjust if needed)
RIGHT_PWM = 18 # GPIO18 (Pin 24)
RIGHT_IN1 = 19 # GPIO19 (Pin 25)
RIGHT_IN2 = 20 # GPIO20 (Pin 26)

# Ultrasonic sensor pins (avoid conflicts with motor pins)
TRIG_PIN = 16 # GPIO16 (Pin 21)
ECHO_PIN = 17 # GPIO17 (Pin 22)

# Behavior tuning constants
THRESHOLD_CM = 30        # distance (cm) to trigger avoidance
CRUISE_SPEED = 60        # percent (0-100)
REVERSE_MS = 350         # how long to reverse when obstacle found (ms)
TURN_MS = 400            # how long to turn to avoid obstacle (ms)
LOOP_DELAY_MS = 60       # main loop delay (ms)
