"""
Servo Motor Control for Raspberry Pi Pico 2w
Controls a micro servo motor using PWM on a specified GPIO pin.
Designed for standard 50Hz servos (e.g., SG90, MG90S).
"""

from machine import Pin, PWM

class Servo:
    """
    Control a micro servo motor via PWM.
    
    Standard servo expects:
    - 50Hz frequency
    - 1000μs pulse width = 0° (minimum angle)
    - 1500μs pulse width = 90° (center)
    - 2000μs pulse width = 180° (maximum angle)
    """
    
    def __init__(self, pin, min_angle=0, max_angle=180, min_pulse=1000, max_pulse=2000):
        """
        Initialize the servo controller.
        
        Args:
            pin (int): GPIO pin number connected to servo signal line
            min_angle (int): Minimum servo angle in degrees (default: 0)
            max_angle (int): Maximum servo angle in degrees (default: 180)
            min_pulse (int): Pulse width in microseconds for min_angle (default: 1000)
            max_pulse (int): Pulse width in microseconds for max_angle (default: 2000)
        """
        self.pin = Pin(pin, Pin.OUT)
        self.pwm = PWM(self.pin)
        self.pwm.freq(50)  # Standard servo frequency: 50Hz
        
        self.min_angle = min_angle
        self.max_angle = max_angle
        self.min_pulse = min_pulse
        self.max_pulse = max_pulse
        self.current_angle = None
        
        # Calculate conversion factor (pulse width change per degree)
        self.pulse_range = max_pulse - min_pulse
        self.angle_range = max_angle - min_angle
    
    def _angle_to_duty_cycle(self, angle):
        """
        Convert angle (degrees) to duty cycle (0-65535).
        
        PWM duty cycle calculation:
        - For 50Hz: period = 20000μs
        - duty_cycle = (pulse_width / 20000) * 65535
        
        Args:
            angle (float): Desired servo angle in degrees
            
        Returns:
            int: PWM duty cycle value (0-65535)
        """
        # Clamp angle to valid range
        angle = max(self.min_angle, min(self.max_angle, angle))
        
        # Linear interpolation from angle to pulse width
        pulse_width = self.min_pulse + (angle - self.min_angle) * (self.pulse_range / self.angle_range)
        
        # Convert pulse width (μs) to duty cycle
        # 50Hz = 20000μs period, duty cycle range is 0-65535
        duty_cycle = int((pulse_width / 20000) * 65535)
        
        return duty_cycle
    
    def set_angle(self, angle):
        """
        Set servo to specified angle.
        
        Args:
            angle (float): Desired angle in degrees (min_angle to max_angle)
        """
        duty = self._angle_to_duty_cycle(angle)
        self.pwm.duty_u16(duty)
        self.current_angle = angle
    
    def get_angle(self):
        """
        Get the last set angle.
        
        Returns:
            float: Current angle in degrees, or None if not yet set
        """
        return self.current_angle
    
    def center(self):
        """Move servo to center position (90°)."""
        self.set_angle(90)
    
    def min_position(self):
        """Move servo to minimum position."""
        self.set_angle(self.min_angle)
    
    def max_position(self):
        """Move servo to maximum position."""
        self.set_angle(self.max_angle)
    
    def deinit(self):
        """Clean up PWM and pin resources."""
        self.pwm.deinit()


if __name__ == "__main__":
    # Minimal example moved from main.py
    import time

    servo = Servo(pin=0)

    try:
        # Move to minimum position
        servo.min_position()
        time.sleep(1)

        # Move to center position
        servo.center()
        time.sleep(1)

        # Move to maximum position
        servo.max_position()
        time.sleep(1)

        # Move to 45 degrees
        servo.set_angle(45)
        time.sleep(1)
        
        # Sweep from 0 to 180 degrees
        for angle in range(0, 181, 10):
            servo.set_angle(angle)
            time.sleep(0.2)

        print("Servo movement complete")

    except KeyboardInterrupt:
        print("Stopped by user")

    finally:
        servo.deinit()
