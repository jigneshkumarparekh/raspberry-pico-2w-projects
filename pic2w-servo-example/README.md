# Raspberry Pi Pico 2w Servo Motor Control

This project demonstrates how to control a micro servo motor with a Raspberry Pi Pico 2w using MicroPython.

## Hardware Requirements

- **Raspberry Pi Pico 2w**
- **Micro Servo Motor** (e.g., SG90, MG90S, MG995)
- **Jumper Wires** (3x recommended)
- **External Power Supply** (servo typically requires 5V, 1A+)
- **Breadboard** (optional, for easier connections)

## Wiring Diagram

### Standard 3-Wire Servo Connection

```
Servo Motor Pins:
  - Signal (Orange/Yellow) → GPIO pin on Pico (e.g., GPIO0)
  - Power (Red)            → +5V (external power supply)
  - Ground (Brown/Black)   → GND (common with Pico)

Pico Pin Layout (top-down):
  ┌─────────────────────────┐
  │ GPIO0  GPIO1  GPIO2  ...│
  │ GND    GND    GND   ...│
  └─────────────────────────┘

GPIO0 → Servo Signal (Orange Wire)
GND   → Servo Ground (Brown Wire) + External Power Ground
5V External → Servo Power (Red Wire)
```

**Important**: Do NOT power the servo directly from Pico's 3.3V output—use an external 5V power supply.

## Installation

1. Copy `servo.py` to your Raspberry Pi Pico 2w using:

   - **Thonny IDE** (File → Open → Device → Upload to /servo.py)
   - **ampy** CLI tool: `ampy --port /dev/ttyUSB0 put servo.py`
   - **Micropython WebREPL** or manual copy

2. Ensure your Pico is running **MicroPython firmware**. Download from [micropython.org](https://micropython.org/download/rp2-pico2/).

## Usage

### Basic Example

```python
from servo import Servo
import time

# Initialize servo on GPIO 0
servo = Servo(pin=0)

# Move to center (90°)
servo.center()
time.sleep(1)

# Move to minimum (0°)
servo.min_position()
time.sleep(1)

# Move to maximum (180°)
servo.max_position()
time.sleep(1)

# Sweep through angles
for angle in range(0, 181, 10):
    servo.set_angle(angle)
    time.sleep(0.1)

# Cleanup
servo.deinit()
```

### Sweep Example

```python
from servo import Servo
import time

servo = Servo(pin=0)

# Continuous sweep
try:
    while True:
        # Sweep left to right
        for angle in range(0, 181, 5):
            servo.set_angle(angle)
            time.sleep(0.05)

        # Sweep right to left
        for angle in range(180, -1, -5):
            servo.set_angle(angle)
            time.sleep(0.05)
except KeyboardInterrupt:
    print("Stopped")
    servo.deinit()
```

### Custom Servo Configuration

If your servo has different pulse width ranges:

```python
from servo import Servo

# SG90 standard (1000-2000μs)
servo = Servo(pin=0, min_pulse=1000, max_pulse=2000)

# Or for a servo with different range
servo = Servo(pin=0, min_pulse=600, max_pulse=2400)

servo.set_angle(90)
```

## API Reference

### Servo Class

#### `__init__(pin, min_angle=0, max_angle=180, min_pulse=1000, max_pulse=2000)`

Initialize servo controller.

- **pin**: GPIO pin number (0-28)
- **min_angle**: Minimum angle in degrees (default: 0)
- **max_angle**: Maximum angle in degrees (default: 180)
- **min_pulse**: Pulse width for min_angle in microseconds (default: 1000)
- **max_pulse**: Pulse width for max_angle in microseconds (default: 2000)

#### `set_angle(angle)`

Set servo to specified angle (clamped to min/max range).

- **angle**: Angle in degrees (float or int)

#### `get_angle()`

Returns the last set angle or `None` if not yet configured.

#### `center()`

Move servo to center position (90°).

#### `min_position()`

Move servo to minimum position (0°).

#### `max_position()`

Move servo to maximum position (180°).

#### `deinit()`

Clean up PWM resources before exit.

## Troubleshooting

| Issue                   | Solution                                                                |
| ----------------------- | ----------------------------------------------------------------------- |
| Servo doesn't move      | Check GPIO pin number and wiring; verify external 5V power is connected |
| Servo jitters           | Servo signal wire may be too long; add ferrite core or shielding        |
| Servo moves erratically | Adjust `min_pulse` and `max_pulse` for your specific servo model        |
| Connection lost         | Ensure GND from external power is connected to Pico GND                 |

## Technical Details

### PWM Configuration

- **Frequency**: 50 Hz (standard for hobby servos)
- **Period**: 20,000 microseconds
- **Pulse Width Range**: 1000-2000 μs (SG90)
  - 1000 μs = 0° (minimum)
  - 1500 μs = 90° (center)
  - 2000 μs = 180° (maximum)

### Servo Models

Common servo pulse width ranges:

| Model | Min Pulse | Max Pulse | Notes                     |
| ----- | --------- | --------- | ------------------------- |
| SG90  | 1000 μs   | 2000 μs   | Most common, budget servo |
| MG90S | 1000 μs   | 2000 μs   | Metal geared SG90 upgrade |
| MG995 | 600 μs    | 2400 μs   | Larger servo, wider range |

## Related Files

- [blink.py](blink.py) - Basic LED blinking example
- [servo.py](servo.py) - Servo control module

## References

- [MicroPython PWM Documentation](https://docs.micropython.org/en/latest/library/machine.PWM.html)
- [Raspberry Pi Pico Pinout](https://datasheets.raspberrypi.com/pico/Pico-R3_A4_Pinout.pdf)
- [SG90 Servo Datasheet](https://www.electronicoscope.com/download/sg90-servo.pdf)

## License

Open source - feel free to modify and reuse for your projects.
