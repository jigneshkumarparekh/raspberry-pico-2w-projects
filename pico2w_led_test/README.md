# Pico 2w LED Test

This project provides basic LED testing examples for the Raspberry Pi Pico 2w, including on-board LED blink and external LED control.

## Overview

LED control is one of the most fundamental operations with microcontrollers. This project demonstrates how to:

- Blink the built-in LED on the Pico 2w
- Control external LEDs via GPIO pins
- Manage LED brightness with PWM (Pulse Width Modulation)

## Components Required

- Raspberry Pi Pico 2w
- External LEDs (optional)
- Current-limiting resistors (220Ω - 1kΩ for LEDs)
- Breadboard and jumper wires
- USB cable for power and programming

## Files

- `blink.py` - Built-in LED blink example
- `external_led.py` - External LED control examples
- `README.md` - This file

## Wiring Diagram

```
                 Raspberry Pi Pico 2W
    ┌─────────────────────────────────┐
    │                                 │
    │  GP15 (Pin 20) ────────────┐    │
    │                            │    │
    │                           ┌┴─────────────┐
    │                           │   220Ω       │
    │                           │   Resistor   │
    │                           └┬─────────────┘
    │                            │
    │                            │ (+) LED Anode (long leg)
    │                            │/
    │                            │──  (LED)
    │                             \
    │                            │ (-) LED Cathode (short leg)
    │                            │
    │  GND (any GND pin) ────────┴
    │                                 │
    └─────────────────────────────────┘
```

## Setup Instructions

1. **Wire the LED:**

   - Connect the LED anode (long leg) → 220Ω resistor → GPIO 15 (Pin 20)
   - Connect the LED cathode (short leg) → GND

2. **Copy the program to Pico:**

   - Use Thonny IDE or `mpremote` to copy the Python files to the device

3. **Run the program:**
   - Via Thonny: Open the file and press "Run" or F5
   - Via REPL: `import blink` or `import external_led`
   - Via CLI: `mpremote run external_led.py`

## Usage

The program toggles the LED every 2 seconds indefinitely. Press `Ctrl+C` to stop.

To change the pin or timing, edit these lines in `external_led.py`:

```python
pin = Pin(15, Pin.OUT)    # Change 15 to your GPIO number
sleep(2)                  # Change 2 to desired delay (seconds)
```

## Troubleshooting

- **LED not lighting:** Check polarity (anode to resistor, cathode to GND)
- **LED too bright/dim:** Adjust the resistor value (higher = dimmer)
- **Script won't run:** Ensure MicroPython is flashed on the Pico (use latest firmware from raspberrypi.com)
