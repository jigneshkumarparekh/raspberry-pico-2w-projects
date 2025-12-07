# TB6612FNG H-Bridge Motor Control - Wiring Guide

## Overview

This guide covers connecting a single DC motor to a Raspberry Pi Pico 2W using the TB6612FNG H-bridge driver.

---

## Pin Configuration

### Logic Power & Ground

Connect the TB6612FNG logic power to Pico 3.3V and ground:

| TB6612FNG Pin | Pico 2W Pin   | Description        |
| ------------- | ------------- | ------------------ |
| VCC           | Pin 36 (3.3V) | Logic power supply |
| GND           | Pin 38 (GND)  | Logic ground       |

### Motor Power Supply

Connect a separate external power supply (4.5V - 13.5V) for the motor:

| TB6612FNG Pin | Power Supply        | Description                            |
| ------------- | ------------------- | -------------------------------------- |
| VMOT          | + (Positive)        | Motor power supply (4.5V - 13.5V)      |
| GND           | - (Negative/Ground) | **Must share common ground with Pico** |

**⚠️ IMPORTANT:** The power supply ground must be connected to Pico GND for proper logic reference.

### Control Signal Pins

Connect motor control signals from Pico GPIO to TB6612FNG:

| TB6612FNG Pin | Pico 2W GPIO | Pico Pin # | Function                               |
| ------------- | ------------ | ---------- | -------------------------------------- |
| STBY          | GP15         | 20         | Standby/Enable (HIGH to enable driver) |
| PWM           | GP16         | 21         | Speed control (PWM signal)             |
| IN1           | GP17         | 22         | Direction control 1 (forward)          |
| IN2           | GP18         | 24         | Direction control 2 (reverse)          |

### Motor Connection

Connect your DC motor to the TB6612FNG output pins:

| TB6612FNG Pin | Connection   |
| ------------- | ------------ |
| AO1           | Motor lead 1 |
| AO2           | Motor lead 2 |

**Note:** Motor leads can be connected either way. If rotation is opposite of desired, swap the leads.

---

## Pico 2W Pinout Reference

```
          USB
        +---------+
        | 1 GP0   | 2 GP1
        | 3 GND   | 4 GP2
        | 5 GP3   | 6 GP4
        | 7 GP5   | 8 GP6
        | 9 GP7   | 10 GP8
        |11 GP9   | 12 GP10
        |13 GP11  | 14 GP12
        |15 GP13  | 16 GP14
        |17 GP15* | 18 (GND)
        |19 GP17* | 20 (GND)
        |21 GP16* | 22 GP18*
        |23 GP20  | 24 (GND)
        |25 GP21  | 26 (GND)
        |27 GP22  | 28 GP26_ADC0
        |29 GND   | 30 RUN
        |31 ADC2  | 32 VSYS
        |33 GND   | 34 VBUS
        |35 3.3V* | 36 (GND)
        |37 3.3V* | 38 (GND)
        +---------+
        (* = Used for motor control)
```

---

## Complete Wiring Checklist

### Power Connections

- [ ] TB6612FNG VCC → Pico Pin 36 (3.3V)
- [ ] TB6612FNG GND → Pico Pin 38 (GND)
- [ ] External power supply (+) → TB6612FNG VMOT
- [ ] External power supply (-) → TB6612FNG GND and Pico GND (common ground)

### Control Signal Connections

- [ ] TB6612FNG STBY → Pico GP15 (Pin 20)
- [ ] TB6612FNG PWM → Pico GP16 (Pin 21)
- [ ] TB6612FNG IN1 → Pico GP17 (Pin 22)
- [ ] TB6612FNG IN2 → Pico GP18 (Pin 24)

### Motor Connections

- [ ] DC Motor lead 1 → TB6612FNG AO1
- [ ] DC Motor lead 2 → TB6612FNG AO2

---

## Motor Control Commands

Once wired, control the motor using the Python API:

```python
# Forward at full speed
motor.forward(100)

# Forward at 50% speed
motor.forward(50)

# Reverse at full speed
motor.reverse(100)

# Stop (coast)
motor.stop()

# Brake (hold in place)
motor.brake()

# Adjust speed while running
motor.set_speed(75)
```

---

## TB6612FNG Truth Table

| IN1 | IN2 | PWM | Function                          |
| --- | --- | --- | --------------------------------- |
| 0   | 0   | X   | Stop/Coast                        |
| 1   | 0   | > 0 | Forward (speed controlled by PWM) |
| 0   | 1   | > 0 | Reverse (speed controlled by PWM) |
| 1   | 1   | X   | Brake (hard stop)                 |

---

## Troubleshooting

**Motor doesn't spin:**

- Check power supply voltage (4.5V - 13.5V)
- Verify common ground between Pico and power supply
- Check STBY pin is HIGH (enabled)
- Verify PWM pin is receiving PWM signal (not 0)

**Motor spins wrong direction:**

- Swap motor leads (AO1 ↔ AO2)
- Or change IN1/IN2 logic in code

**Motor jerky or unstable:**

- Add capacitors across motor leads (100µF)
- Check wire connections for loose contacts
- Verify power supply has adequate current rating (≥ 2A for typical motors)

**Driver gets hot:**

- Check for short circuits
- Verify motor not stalled/blocked
- Reduce PWM duty cycle
- May need larger power supply

---

## Safety Notes

⚠️ **Always:**

- Use proper gauge wire for power connections (≥ 18 AWG for signals, ≥ 14 AWG for motor power)
- Ensure power supply is properly regulated
- Disconnect power before modifying connections
- Use proper fuses/circuit protection on motor power

---

## File Location

Python motor control code: `motor.py`

Motor control classes:

- `Motor` - Single motor control
- `HBridge` - TB6612FNG driver management
