# External LED Control for Raspberry Pi Pico 2W

## Wiring Diagram

```
                 Raspberry Pi Pico 2W
    ┌─────────────────────────────────┐
    │                                 │
    │  GP15 (Pin 20) ────────────┐    │
    │                            │    │
    │                           ┌┴─────────────┐
    │                           │   100Ω       │
    │                           │   Resistor   │
    │                           └┬─────────────┘
    │                            │
    │                            │ (+) LED Anode (long leg)
    │                            │/
    │                            │──  (yellow/red LED example)
    │                             \
    │                            │ (-) LED Cathode (short leg)
    │                            │
    │  GND (any GND pin) ────────┴
    │                                 │
    └─────────────────────────────────┘
```

## Components Required

- 1× Raspberry Pi Pico 2W
- 1× LED (any color, standard 5mm or 3mm)
- 1× Resistor (100Ω–1kΩ recommended; 220Ω for typical brightness)
- Jumper wires or breadboard connections

## Setup Instructions

1. **Wire the LED:**

   - Connect the LED anode (long leg) → 220Ω resistor → GPIO 15 (Pin 20)
   - Connect the LED cathode (short leg) → GND

2. **Copy the program to Pico:**

   - Use Thonny IDE or `mpremote` to copy `external_led.py` to the device

3. **Run the program:**
   - Via Thonny: Open the file and press "Run" or F5
   - Via REPL: `import external_led` (will auto-run the loop)
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
