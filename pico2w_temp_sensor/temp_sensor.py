import machine
import time

# Initialize the ADC for the internal temperature sensor
temp_sensor = machine.ADC(4)  # Channel 4 is the internal temperature sensor

def read_temperature():
    """
    Read temperature from Raspberry Pico 2W internal temperature sensor.
    Returns temperature in Celsius.
    """
    # Read raw ADC value (0-4095)
    adc_value = temp_sensor.read_u16()
    
    # Convert to voltage (0-3.3V)
    voltage = adc_value * 3.3 / 65535
    
    # Convert voltage to temperature (from datasheet formula)
    # Temperature = 27 - (V - 0.706) / 0.001721
    temperature_celsius = 27 - (voltage - 0.706) / 0.001721
    
    return temperature_celsius

def main():
    """Main loop to continuously read and print temperature."""
    print("Raspberry Pico 2W Temperature Sensor")
    print("=" * 40)
    
    try:
        while True:
            temp = read_temperature()
            temp_fahrenheit = (temp * 9/5) + 32
            
            print(f"Temperature: {temp:.2f} C / {temp_fahrenheit:.2f} F")
            
            # Wait 1 second before next reading
            time.sleep(2)
    
    except KeyboardInterrupt:
        print("\nProgram stopped by user")

if __name__ == "__main__":
    main()
