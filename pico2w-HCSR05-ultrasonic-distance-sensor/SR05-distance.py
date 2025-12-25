import machine
import time

class HCSR04:
    """
    Driver for HC-SR04/HC-SR05 Ultrasonic Distance Sensor
    Works with Raspberry Pi Pico 2W
    """
    
    def __init__(self, trigger_pin, echo_pin):
        """
        Initialize the ultrasonic sensor
        
        Args:
            trigger_pin (int): GPIO pin number for TRIG pin
            echo_pin (int): GPIO pin number for ECHO pin
        """
        self.trigger = machine.Pin(trigger_pin, machine.Pin.OUT)
        self.echo = machine.Pin(echo_pin, machine.Pin.IN)
        
        # Ensure trigger pin is low initially
        self.trigger.value(0)
        
    def distance_cm(self):
        """
        Calculate distance in centimeters
        
        Returns:
            float: Distance in centimeters
        """
        # Send a 10 microsecond pulse to trigger the sensor
        self.trigger.value(0)
        time.sleep_us(2)
        self.trigger.value(1)
        time.sleep_us(10)
        self.trigger.value(0)
        
        # Measure the time the echo pin is high
        timeout = time.ticks_us() + 50000  # 50ms timeout to prevent hanging
        
        # Wait for echo pin to go high
        while self.echo.value() == 0:
            if time.ticks_us() > timeout:
                return None
        
        pulse_start = time.ticks_us()
        
        # Wait for echo pin to go low
        while self.echo.value() == 1:
            if time.ticks_us() > timeout:
                return None
        
        pulse_end = time.ticks_us()
        
        # Calculate pulse duration in microseconds
        pulse_duration = pulse_end - pulse_start
        
        # Speed of sound = 343 m/s = 0.0343 cm/us
        # Distance = (pulse_duration * 0.0343) / 2
        # We divide by 2 because the sound travels to the object and back
        distance = (pulse_duration * 0.0343) / 2
        
        return distance
    
    def distance_inches(self):
        """
        Calculate distance in inches
        
        Returns:
            float: Distance in inches
        """
        distance_cm = self.distance_cm()
        if distance_cm is None:
            return None
        return distance_cm / 2.54


# Example usage
if __name__ == "__main__":
    # Configure pins - adjust these based on your wiring
    TRIGGER_PIN = 16  # GPIO16 (Pin 21)
    ECHO_PIN = 17     # GPIO17 (Pin 22)
    
    # Create sensor instance
    sensor = HCSR04(TRIGGER_PIN, ECHO_PIN)
    
    print("HC-SR04 Ultrasonic Distance Sensor")
    print("=" * 40)
    
    try:
        while True:
            distance_cm = sensor.distance_cm()
            
            if distance_cm is not None:
                distance_inches = distance_cm / 2.54
                print(f"Distance: {distance_cm:.1f} cm ({distance_inches:.1f} inches)")
            else:
                print("Waiting for sensor to get a reading. Place an object in front of the sensor.")
            
            time.sleep(0.5)  # Wait 0.5 seconds before next measurement
    
    except KeyboardInterrupt:
        print("\nMeasurement stopped by user")
