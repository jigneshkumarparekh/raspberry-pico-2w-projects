# Obstacle-Avoiding Robot with Raspberry Pi Pico

A simple obstacle-avoiding robot project using a Raspberry Pi Pico microcontroller, TB6612FNG H-Bridge motor driver, and HC-SR04 ultrasonic sensor. The robot moves forward at a cruise speed, detects obstacles within a threshold distance, reverses briefly, and resumes forward motion.

## Features

- **Obstacle Detection**: Uses ultrasonic sensor to measure distance and avoid collisions.
- **Motor Control**: Single motor setup (left motor) with PWM speed control via TB6612FNG H-Bridge.
- **Simple Behavior**: Forward movement with automatic reverse on obstacle detection.
- **LED Indicator**: Onboard LED blinks on startup and can be used for status.
- **MicroPython-Based**: Runs on Raspberry Pi Pico with MicroPython firmware.

## Hardware Requirements

- **Raspberry Pi Pico** (with MicroPython installed)
- **TB6612FNG H-Bridge Motor Driver**
- **DC Motor** (e.g., 6V-12V geared motor for the left wheel)
- **HC-SR04 Ultrasonic Sensor**
- **Power Supply**: Suitable for motors (e.g., 6V-12V battery pack) and Pico (5V via USB or regulator)
- **Wires and Breadboard** for connections
- **Optional**: Wheels, chassis, and additional components for full robot assembly

## Pin Mappings

The following GPIO pins are used on the Raspberry Pi Pico. Ensure your wiring matches these assignments.

### Motor Control (TB6612FNG H-Bridge)
- **GPIO 12 (STBY_PIN)**: Connected to STBY (Standby) pin on TB6612FNG. Enables/disables the H-Bridge.
- **GPIO 15 (LEFT_PWM)**: Connected to PWMA (PWM input for motor A) on TB6612FNG. Controls speed of the left motor.
- **GPIO 14 (LEFT_IN1)**: Connected to AIN1 on TB6612FNG. Direction control for left motor.
- **GPIO 13 (LEFT_IN2)**: Connected to AIN2 on TB6612FNG. Direction control for left motor.

**Note**: Only the left motor is implemented in the code. For a full robot, you can add a right motor using similar pins (commented out in the code).

### Ultrasonic Sensor (HC-SR04)
- **GPIO 16 (TRIG_PIN)**: Connected to Trig (Trigger) pin on HC-SR04. Sends ultrasonic pulses.
- **GPIO 17 (ECHO_PIN)**: Connected to Echo pin on HC-SR04. Receives echo signals.

### Other
- **Onboard LED**: GPIO "LED" (built-in Pico LED). Used for startup blinking and status indication.

### Wiring Diagram (Text-Based)

```
Raspberry Pi Pico          TB6612FNG H-Bridge          HC-SR04 Sensor          DC Motor (Left)
-----------------          -------------------          --------------          -------------
GPIO 12 (STBY)  ---------> STBY                      Trig Pin     ---------> GPIO 16 (TRIG)
GPIO 15 (PWM)   ---------> PWMA                      Echo Pin     ---------> GPIO 17 (ECHO)
GPIO 14 (IN1)   ---------> AIN1                      VCC          ---------> 5V (Pico/External)
GPIO 13 (IN2)   ---------> AIN2                      GND          ---------> GND
GND            ---------> GND                       Motor +      ---------> Motor Terminal +
5V             ---------> VM (Motor Power)          Motor -      ---------> Motor Terminal -
                          AO1/AO2 (Outputs) ---------> Left Motor Wires

Power Connections:
- Pico: USB power or 5V regulator.
- TB6612FNG: VM connected to motor battery (6V-12V), VCC to 5V.
- HC-SR04: Powered from Pico's 5V/GND.
- Motors: Ensure polarity matches direction (swap wires if needed).
```

**Important**: Double-check the TB6612FNG datasheet for pinouts. The H-Bridge requires proper power sequencing (VM before VCC). Use decoupling capacitors if motors cause noise.

## Software Requirements

- **MicroPython**: Install MicroPython firmware on your Raspberry Pi Pico.
  - Download from [micropython.org](https://micropython.org/download/rp2-pico/).
  - Flash using Thonny or another tool.
- **Thonny IDE** (recommended for uploading code and testing).

## Installation and Setup

1. **Flash MicroPython**: Boot your Pico in bootloader mode (hold BOOTSEL while plugging in) and flash the UF2 file.
2. **Upload Code**: Copy `main.py` (or other scripts) to the Pico using Thonny or `ampy`.
3. **Wire Hardware**: Follow the pin mappings above.
4. **Power On**: Connect power to the Pico and motors.
5. **Run**: The robot will blink the LED 3 times on startup, then begin moving forward.

## Usage

- **Default Run**: Execute `main.py` for a 20-second test run.
- **Customization**:
  - Adjust `THRESHOLD_CM` for obstacle detection distance (default: 30cm).
  - Change `CRUISE_SPEED` for motor speed (0-100, default: 80).
  - Modify `REVERSE_MS` for reverse duration (default: 550ms).
- **Testing**: Use `test.py` for individual component tests.

## Code Structure

- `main.py`: Main script with simplified obstacle-avoiding logic.
- `main_original.py`: Original version (backup).
- `drive_and_avoid.py`: Core driving and avoidance functions.
- `pins.py`: Pin definitions (if separated).
- `test.py`: Test scripts for motors and sensors.

## Behavior Details

- **Startup**: LED blinks 3 times.
- **Movement**: Moves forward continuously.
- **Obstacle Detection**: If distance < 30cm, stops, reverses for 550ms, then resumes forward.
- **Timeout**: Runs for 20 seconds total, then stops and disables H-Bridge.
- **Error Handling**: Handles sensor timeouts gracefully.

## Troubleshooting

- **Motor Not Moving**: Check H-Bridge power (VM), STBY pin, and PWM/direction pins.
- **Sensor Not Detecting**: Verify Trig/Echo wiring and power. Test with `test.py`.
- **Code Upload Issues**: Ensure MicroPython is flashed and use Thonny for serial connection.
- **Power Issues**: Motors may draw high current; use adequate battery and check for voltage drops.

## Contributing

Feel free to modify and improve! Add right motor support, PID control, or additional sensors.

## License

This project is open-source. Use at your own risk.