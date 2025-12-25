# HC-SR04/HC-SR05 Ultrasonic Distance Sensor - Raspberry Pi Pico 2W

## Overview

This project demonstrates how to interface an HC-SR04 (or HC-SR05) ultrasonic distance sensor with a **Raspberry Pi Pico 2W** using MicroPython. The sensor measures distance by emitting ultrasonic sound waves and measuring the time for the echo to return.

## Hardware Components

- Raspberry Pi Pico 2W
- HC-SR04 or HC-SR05 Ultrasonic Distance Sensor
- Jumper wires
- Breadboard (optional)
- USB cable for programming

## Sensor Specifications

| Parameter         | Value         |
| ----------------- | ------------- |
| Operating Voltage | 5V            |
| Measurement Range | 2 cm - 400 cm |
| Measurement Angle | 15°           |
| Frequency         | 40 kHz        |
| Accuracy          | ±3 mm         |
| Power Consumption | <2 mA         |

## Pinout

### HC-SR04/HC-SR05 Sensor Pins:

- **VCC** - Power supply (5V)
- **GND** - Ground
- **TRIG** - Trigger pin (input)
- **ECHO** - Echo pin (output)

### Default Pico 2W Connections:

```
HC-SR04/HC-SR05     Raspberry Pi Pico 2W
─────────────────────────────────────────
VCC         ───────→ VBUS (Pin 40) or 5V rail
GND         ───────→ GND (Pin 38, 43, etc.)
TRIG        ───────→ GPIO16 (Pin 21)
ECHO        ───────→ GPIO17 (Pin 22)
```

**⚠️ IMPORTANT:**: Purposefully skipped connecting `OUT` pin on SR-05 as we don't need it. It's mainly use to start sensor in "mode 2" - which usually is not the case for us.

## Wiring Diagram

```
Raspberry Pi Pico 2W
┌─────────────────────────────────┐
│ ┌─ 40 VBUS (5V)              ──┐│
│ │                              ││
│ │ Pin 21 GPIO16 ──TRIG──────┐  ││
│ │                            │  ││
│ │ Pin 22 GPIO17 ──ECHO───┐  │  ││
│ │                        │  │  ││
│ │ Pin 38 GND ────────────┼──┼──┘│
└────────────────────────┼──┼─────┘
                         │  │
                    ┌────┴──┴───┐
                    │ HC-SR04    │
                    │ Sensor     │
                    │            │
                    │ VCC  GND   │
                    │ TRIG ECHO  │
                    └────────────┘
```

## Installation

### 1. Flash MicroPython on Raspberry Pi Pico 2W

- Download the latest Pico W firmware from [micropython.org](https://micropython.org/download/rp2-pico-w/)
- Use `rshell` or the official Pico programming method to flash it
- Or use Thonny IDE for easier flashing

### 2. Upload the Script

- Connect your Pico 2W to your computer via USB
- Use Thonny IDE, rshell, or VS Code + PyMakr extension to upload `SR05-distance.py`
- Alternatively, copy it to the Pico as a script to run at startup

## Usage

### Basic Usage

```python
from SR05_distance import HCSR04

# Initialize the sensor (adjust pins as needed)
sensor = HCSR04(trigger_pin=16, echo_pin=17)

# Get distance in centimeters
distance_cm = sensor.distance_cm()
print(f"Distance: {distance_cm:.1f} cm")

# Get distance in inches
distance_inches = sensor.distance_inches()
print(f"Distance: {distance_inches:.1f} inches")
```

### Run the Example

Execute the script directly:

```bash
python SR05-distance.py
```

The sensor will continuously measure distance and display results every 0.5 seconds.

### Stop Measurement

Press `Ctrl+C` to stop the program.

## Customizing GPIO Pins

If you're using different GPIO pins, modify the pin numbers in the script:

```python
TRIGGER_PIN = 16  # Change this to your TRIG pin
ECHO_PIN = 17     # Change this to your ECHO pin
```

Raspberry Pi Pico 2W has 26 GPIO pins (GPIO0-GPIO25) available.

## How It Works

1. **Trigger**: Send a 10 microsecond pulse to the TRIG pin
2. **Echo Wait**: The sensor emits a 40 kHz ultrasonic wave
3. **Measurement**: Count the time until the ECHO pin goes low
4. **Calculation**:
   - Distance = (pulse_duration × speed_of_sound) / 2
   - Speed of sound ≈ 343 m/s = 0.0343 cm/microsecond
   - We divide by 2 because sound travels to object and back

## Troubleshooting

### No Readings / Timeout Errors

- Check all wire connections are secure
- Verify correct GPIO pins are used
- Ensure sensor has stable 5V power supply
- Test with a known working setup

### Inaccurate Readings

- The sensor requires a clear line of sight
- Soft surfaces (foam, cloth) absorb ultrasonic waves
- Temperature affects sound speed (code assumes ~20°C)
- Ensure measurement objects are not too close (<2 cm)

### One Pin Reads Correctly, Other Doesn't

- Swap the pin assignments to identify if it's a hardware or software issue
- Check if the GPIO pin is functional by toggling it

## Code Features

- **HCSR04 Class**: Object-oriented design for easy reuse
- **Error Handling**: Timeout mechanism to prevent hanging
- **Dual Units**: Returns distance in both cm and inches
- **Accurate Timing**: Uses microsecond-precision timing
- **Comments**: Well-documented for learning purposes

## Temperature Compensation

For more accurate readings at different temperatures, modify the distance calculation:

```python
# Temperature-adjusted speed of sound
# Formula: speed = 331.3 + 0.606 * temperature (in m/s)
temperature = 20  # in Celsius
speed_of_sound = (331.3 + 0.606 * temperature) * 10000  # in cm/s
# Then adjust the distance calculation accordingly
```

## Resources

- [Raspberry Pi Pico 2W Official Documentation](https://www.raspberrypi.com/documentation/microcontrollers/pico.html)
- [MicroPython Documentation](https://docs.micropython.org/)
- [HC-SR04 Datasheet](https://cdn.sparkfun.com/datasheets/Sensors/Proximity/HC-SR04.pdf)

## License

Free to use and modify for educational and personal projects.

## Author Notes

- Always power the sensor from a reliable 5V source
- Use a breadboard for clean connections
- Keep wires short to minimize noise
- Test with Thonny IDE for debugging (built-in REPL)

---

**Happy Measuring! 🎯📏**
