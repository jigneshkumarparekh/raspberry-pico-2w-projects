"""
PIR Motion Sensor Integration for Raspberry Pi Pico 2w
Detects motion using a PIR sensor and controls an LED accordingly.
"""

from machine import Pin
from utime import sleep, ticks_ms

# GPIO Pin Configuration
PIR_SENSOR_PIN = 28  # GPIO pin connected to PIR sensor (adjust as needed)
LED_PIN = "LED"      # Built-in LED on Pico 2w

# Timing Configuration (in milliseconds)
DEBOUNCE_TIME = 100      # Debounce time to filter false positives
MOTION_TIMEOUT = 5000    # LED stays on for 5 seconds after last motion detected
PIR_WARMUP_TIME = 2      # PIR sensor warmup time in seconds (30-60 seconds recommended)

# Initialize GPIO pins
pir_sensor = Pin(PIR_SENSOR_PIN, Pin.IN)
led = Pin(LED_PIN, Pin.OUT)

# State variables
motion_detected = False
last_motion_time = 0
last_state = 0
last_debounce_time = 0


def initialize_sensor():
    """Initialize PIR sensor with warmup time."""
    print("Initializing PIR motion sensor...")
    print(f"Warming up PIR sensor for {PIR_WARMUP_TIME} seconds...")
    led.on()  # Indicate warmup phase
    sleep(PIR_WARMUP_TIME)
    led.off()
    print("PIR sensor ready. Starting motion detection...")


def is_motion_detected():
    """
    Read PIR sensor with debouncing to filter false positives.
    Returns True if motion is detected, False otherwise.
    """
    global last_state, last_debounce_time
    
    current_time = ticks_ms()
    current_state = pir_sensor.value()
    
    # Debounce: only register state change if time has passed
    if current_state != last_state:
        last_debounce_time = current_time
        last_state = current_state
        return False
    
    # If state is stable and debounce time has passed, return the state
    if current_time - last_debounce_time >= DEBOUNCE_TIME:
        return current_state == 1
    
    return False


def handle_motion_event(motion_state):
    """
    Handle motion detection events.
    motion_state: True if motion detected, False if motion stopped.
    """
    global motion_detected, last_motion_time
    
    if motion_state and not motion_detected:
        # Motion just started
        motion_detected = True
        last_motion_time = ticks_ms()
        led.on()
        print("[MOTION DETECTED] - LED ON")
    
    elif motion_state:
        # Motion still happening, update timestamp
        last_motion_time = ticks_ms()
    
    elif not motion_state and motion_detected:
        # Motion has stopped
        motion_detected = False
        led.off()
        print("[MOTION STOPPED] - LED OFF")


def main():
    """Main loop for motion sensor monitoring."""
    global motion_detected, last_motion_time
    
    initialize_sensor()
    
    print("LED starts monitoring motion...")
    try:
        while True:
            # Check for motion
            pir_value = pir_sensor.value()
            
            # Motion currently detected (sensor reading high)
            if pir_value == 1:
                handle_motion_event(True)
            else:
                # Check if motion timeout has elapsed
                current_time = ticks_ms()
                if motion_detected and current_time - last_motion_time >= MOTION_TIMEOUT:
                    handle_motion_event(False)
            
            sleep(0.1)  # Check sensor every 100ms
    
    except KeyboardInterrupt:
        print("\nShutting down...")
        led.off()
        print("Finished.")


if __name__ == "__main__":
    main()
