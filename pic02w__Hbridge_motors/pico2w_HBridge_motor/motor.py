from machine import Pin, PWM
from utime import sleep

# ============================================================================
# TB6612FNG H-Bridge Motor Driver Configuration
# ============================================================================

# Motor Control Pins
STBY_PIN = 17        # Standby pin (enable/disable driver)
PWM_PIN = 16         # PWM speed control
IN1_PIN = 14         # Direction control 1 (forward)
IN2_PIN = 15         # Direction control 2 (reverse)

# PWM Configuration
PWM_FREQ = 10000     # 10 kHz PWM frequency (TB6612FNG supports up to 100 kHz)
MAX_DUTY = 65535     # Maximum PWM duty cycle value (16-bit)

# ============================================================================
# Motor Class - Controls a single DC motor via TB6612FNG
# ============================================================================

class Motor:
    """
    Control a DC motor using TB6612FNG H-bridge driver.
    """
    
    def __init__(self, pwm_pin, dir_pin1, dir_pin2):
        """
        Initialize motor with GPIO pins.
        
        Args:
            pwm_pin: Pin number for PWM speed control
            dir_pin1: Pin number for direction control 1
            dir_pin2: Pin number for direction control 2
        """
        self.current_speed = 0
        
        # Initialize PWM for speed control
        self.pwm = PWM(Pin(pwm_pin))
        self.pwm.freq(PWM_FREQ)
        self.pwm.duty_u16(0)  # Start at 0 speed
        
        # Initialize direction control pins
        self.dir1 = Pin(dir_pin1, Pin.OUT)
        self.dir2 = Pin(dir_pin2, Pin.OUT)
        self.dir1.off()
        self.dir2.off()
        
        print("Motor initialized")
    
    def forward(self, speed=100):
        """
        Drive motor forward at specified speed.
        
        Args:
            speed: Speed percentage (0-100, default 100)
        """
        speed = max(0, min(100, speed))  # Clamp speed to 0-100
        self.current_speed = speed
        
        # Direction: IN1=1, IN2=0 for forward
        self.dir1.on()
        self.dir2.off()
        
        # Set PWM speed
        duty = int((speed / 100) * MAX_DUTY)
        self.pwm.duty_u16(duty)
        
        print(f"Motor forward at {speed}%")
    
    def reverse(self, speed=100):
        """
        Drive motor in reverse at specified speed.
        
        Args:
            speed: Speed percentage (0-100, default 100)
        """
        speed = max(0, min(100, speed))  # Clamp speed to 0-100
        self.current_speed = speed
        
        # Direction: IN1=0, IN2=1 for reverse
        self.dir1.off()
        self.dir2.on()
        
        # Set PWM speed
        duty = int((speed / 100) * MAX_DUTY)
        self.pwm.duty_u16(duty)
        
        print(f"Motor reverse at {speed}%")
    
    def stop(self):
        """
        Stop motor immediately (coast to stop).
        """
        self.current_speed = 0
        self.pwm.duty_u16(0)
        print("Motor stopped")
    
    def brake(self):
        """
        Brake motor hard (both direction pins on for holding torque).
        """
        self.current_speed = 0
        self.dir1.on()
        self.dir2.on()
        self.pwm.duty_u16(0)
        print("Motor braked")
    
    def set_speed(self, speed):
        """
        Change motor speed while maintaining current direction.
        
        Args:
            speed: Speed percentage (0-100)
        """
        speed = max(0, min(100, speed))  # Clamp speed to 0-100
        self.current_speed = speed
        
        duty = int((speed / 100) * MAX_DUTY)
        self.pwm.duty_u16(duty)
        
        print(f"Motor speed set to {speed}%")

# ============================================================================
# H-Bridge Driver Class - Manages TB6612FNG
# ============================================================================

class HBridge:
    """
    Control TB6612FNG H-bridge driver standby pin.
    """
    
    def __init__(self, stby_pin, motor):
        """
        Initialize H-bridge driver.
        
        Args:
            stby_pin: Pin number for standby enable
            motor: Motor instance to control
        """
        self.stby = Pin(stby_pin, Pin.OUT)
        self.stby.on()  # Enable driver on startup
        self.motor = motor
        print("H-Bridge driver enabled")
    
    def enable(self):
        """Enable the H-bridge driver."""
        self.stby.on()
        print("H-Bridge enabled")
    
    def disable(self):
        """Disable the H-bridge driver (standby mode)."""
        self.stby.off()
        print("H-Bridge disabled (standby)")

# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    # Initialize motor
    motor = Motor(PWM_PIN, IN1_PIN, IN2_PIN)
    
    # Initialize H-bridge driver
    driver = HBridge(STBY_PIN, motor)
    
    print("\n=== DC Motor Control Demo ===\n")
    
    try:
        # Test forward
        print("--- Forward ---")
        motor.forward(100)
        sleep(2)
        motor.forward(50)
        sleep(2)
        
        # Test reverse
        print("\n--- Reverse ---")
        motor.reverse(100)
        sleep(2)
        motor.reverse(50)
        sleep(2)
        
        # Test stop
        print("\n--- Stop ---")
        motor.stop()
        sleep(1)
        
        # Test speed adjustment
        print("\n--- Speed Adjustment ---")
        motor.forward(100)
        sleep(1)
        
        for speed in [75, 50, 25, 0]:
            motor.set_speed(speed)
            sleep(1)
        
        # Test brake
        print("\n--- Testing Brake ---")
        motor.forward(100)
        sleep(1)
        motor.brake()
        sleep(1)
        
    except KeyboardInterrupt:
        print("\n\nInterrupt received - stopping motor...")
        motor.stop()
        driver.disable()
    
    print("Motor control demo finished.")
