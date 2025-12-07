# TB6612FNG H-Bridge Motor Control - Circuit Diagram

## Visual Wiring Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                      POWER SUPPLY (12V)                         │
│                     ┌─────────────────┐                         │
│                     │   + (Positive)  │                         │
│                     │   - (Negative)  │                         │
│                     └────┬────────┬───┘                         │
│                          │        │                            │
│          ┌────────────────┘        └────────────────┐           │
│          │                                          │           │
│          ▼                                          ▼           │
│     [VMOT]                                     [GND/Ground]     │
│          │                                          │           │
│          │         ┌─────────────────┐             │           │
│          │         │  TB6612FNG      │             │           │
│          └────────►│ H-Bridge Driver │◄────────────┘           │
│                    │                 │                         │
│   ┌─────────────┐  │    (DIP-16)    │  ┌──────────────┐       │
│   │ Pico 2W     │  │                 │  │  DC Motor    │       │
│   │             │  │ [VCC] [GND1]   │  │              │       │
│   │ 3.3V ──────►│──┤ PWR  PWR       │  │   ┌────────┐ │       │
│   │ GND ───┬───►│──┤ GND  GND       │  │   │        │ │       │
│   │        │    │  │                 │  │   │ Motor  │ │       │
│   │        │    │  │ [STBY] Enable  │  │   │ Leads  │ │       │
│   │ GP15 ──┼──────┤ STBY            │  │   │        │ │       │
│   │        │    │  │                 │  │   └────────┘ │       │
│   │ GP16 ──┼──────┤ PWMA PWM        │  │       │    │  │       │
│   │ GP17 ──┼──────┤ AIN1 Direction  │  │       │    │  │       │
│   │ GP18 ──┼──────┤ AIN2 Control    │  │       ▼    ▼  │       │
│   │        │    │  │                 │  │     [AO1] [AO2]     │
│   │        │    │  │ [VMOT] Motor   │  │         │      │     │
│   │        │    │  │ Power Input     │  └─────────┴──────┘     │
│   │        │    │  │                 │                         │
│   └────────┼──────┤ GND2 COMMON GND  │                         │
│            │    │  │                 │                         │
│            │    └──┤ GND GND         │                         │
│            │       │                 │                         │
│            └──────►└─────────────────┘                         │
│         (COMMON GROUND)                                         │
│         (Essential!)                                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Pin Connection Summary

### Pico 2W Connections

```
Pico 2W (Top View)

     ┌──────────────────────┐
     │ USB                  │
     │                      │
     │ [GP15] - Pin 20 ──→ STBY
     │ [GP16] - Pin 21 ──→ PWMA
     │ [GP17] - Pin 22 ──→ AIN1
     │ [GP18] - Pin 24 ──→ AIN2
     │                      │
     │ [3.3V] - Pin 36 ──→ VCC
     │ [GND]  - Pin 38 ──→ GND (COMMON GROUND)
     │                      │
     └──────────────────────┘
            │
            ▼
        TB6612FNG
```

### TB6612FNG Connections

```
TB6612FNG (DIP-16)

         Top View
    ┌─────────────┐
 1  │ AO1    GND2 │ 16
 2  │ AO2    VMOT │ 15
 3  │ GND1   PWMB │ 14
 4  │ VCC    BIN1 │ 13
 5  │ STBY   BIN2 │ 12
 6  │ PWMA   BO2  │ 11
 7  │ AIN1   BO1  │ 10
 8  │ AIN2   (Key)│  9
    └─────────────┘

Control Pins Used:
├─ Pin 4  (VCC)   ← Pico 3.3V
├─ Pin 3  (GND1)  ← Pico GND
├─ Pin 5  (STBY)  ← Pico GP15
├─ Pin 6  (PWMA)  ← Pico GP16
├─ Pin 7  (AIN1)  ← Pico GP17
├─ Pin 8  (AIN2)  ← Pico GP18
├─ Pin 15 (VMOT)  ← Power Supply +12V
├─ Pin 16 (GND2)  ← Power Supply GND
└─ Pin 1-2 (AO1/AO2) → DC Motor Leads
```

## Power Flow Diagram

```
┌──────────────────┐
│  External Power  │
│   Supply (12V)   │
└────────┬─────────┘
         │
    ┌────┴────┐
    │          │
    ▼          ▼
  (+12V)     (GND)
    │          │
    │      ┌───┴────────────┐
    │      │                │
    ▼      ▼                ▼
  [VMOT]  [GND2]      [Pico GND]  ◄── COMMON GROUND
    │      │                │           (Critical!)
    └──┬───┴────────────────┘
       │
       └──→ TB6612FNG (Motor Driver)
            │
            ├─→ STBY (Enable Pin)
            ├─→ PWM  (Speed Control)
            ├─→ IN1  (Direction Ctrl)
            ├─→ IN2  (Direction Ctrl)
            │
            └──→ Motor Output (AO1, AO2)
                 │
                 ▼
               Motor
```

## Component List

| Component            | Quantity | Voltage                     | Notes                                          |
| -------------------- | -------- | --------------------------- | ---------------------------------------------- |
| Raspberry Pi Pico 2W | 1        | 3.3V Logic                  | Microcontroller                                |
| TB6612FNG H-Bridge   | 1        | 3.3V Logic, 4.5-13.5V Motor | Dual motor driver                              |
| DC Motor             | 1        | 6-12V                       | Standard brushed DC motor                      |
| Power Supply         | 1        | 4.5-13.5V @ 2A+             | Separate from Pico power                       |
| Jumper Wires         | 11       | -                           | Signal and power connections                   |
| Capacitors           | 2        | 100µF                       | Optional: across motor leads (noise filtering) |

---

## Connections Quick Reference

| From            | To               | Wire Color (Suggested) |
| --------------- | ---------------- | ---------------------- |
| Pico GP15       | TB6612FNG STBY   | Yellow                 |
| Pico GP16       | TB6612FNG PWMA   | Orange                 |
| Pico GP17       | TB6612FNG AIN1   | Green                  |
| Pico GP18       | TB6612FNG AIN2   | Blue                   |
| Pico 3.3V       | TB6612FNG VCC    | Red                    |
| Pico GND        | TB6612FNG GND1   | Black                  |
| Pico GND        | Power Supply GND | Black                  |
| Power Supply +  | TB6612FNG VMOT   | Red (Heavy Gauge)      |
| Power Supply -  | TB6612FNG GND2   | Black (Heavy Gauge)    |
| DC Motor Lead 1 | TB6612FNG AO1    | -                      |
| DC Motor Lead 2 | TB6612FNG AO2    | -                      |

---

## Assembly Steps

1. **Prepare breadboard or perfboard** if using one
2. **Insert components** (Pico, TB6612FNG)
3. **Connect power first** (less chance of shorts):
   - Pico 3.3V → TB6612FNG VCC
   - Pico GND → TB6612FNG GND1
   - Power supply GND → TB6612FNG GND2
   - Power supply GND → Pico GND (common ground)
   - Power supply + → TB6612FNG VMOT
4. **Connect control signals** (Signal wires):
   - GP15 → STBY
   - GP16 → PWMA
   - GP17 → AIN1
   - GP18 → AIN2
5. **Connect motor** to AO1 and AO2
6. **Double-check all connections** before powering on
7. **Test with motor.py code**

---

## Safety Checklist

- [ ] All power connections verified
- [ ] Common ground connected (GND)
- [ ] No loose wires touching each other
- [ ] Motor not mechanically blocked
- [ ] Power supply current rating adequate (≥2A)
- [ ] No exposed copper/short circuit risks
- [ ] Code uploaded and ready
