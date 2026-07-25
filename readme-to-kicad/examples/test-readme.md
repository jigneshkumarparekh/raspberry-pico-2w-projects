# Obstacle-Avoiding Robo Car Wiring

This README is formatted for `readme-to-kicad`.

## Components

- Raspberry Pi Pico 2W
- TB6612FNG motor driver
- HC-SR04 ultrasonic sensor
- Left DC motor
- Right DC motor
- Battery pack

## Connections

| From | To |
| --- | --- |
| Pico GPIO12 | TB6612FNG STBY |
| Pico GPIO15 | TB6612FNG PWMA |
| Pico GPIO14 | TB6612FNG AIN1 |
| Pico GPIO13 | TB6612FNG AIN2 |
| Pico GPIO8 | TB6612FNG PWMB |
| Pico GPIO7 | TB6612FNG BIN1 |
| Pico GPIO6 | TB6612FNG BIN2 |
| Pico GPIO16 | HC-SR04 TRIG |
| Pico GPIO17 | HC-SR04 ECHO |
| Pico 3V3 | HC-SR04 VCC |
| Pico 3V3 | TB6612FNG VCC |
| Pico GND | HC-SR04 GND |
| Pico GND | TB6612FNG GND |
| Battery positive | TB6612FNG VM |
| Battery negative | TB6612FNG GND |
| TB6612FNG AO1 | Left DC motor positive |
| TB6612FNG AO2 | Left DC motor negative |
| TB6612FNG BO1 | Right DC motor positive |
| TB6612FNG BO2 | Right DC motor negative |

## Notes

- `Pico GPIO12`, `Pico GPIO15`, and similar labels intentionally use GPIO names, not physical header pin numbers.
- `Battery positive` powers the TB6612FNG motor supply pin `VM`.
- `Battery negative`, Pico `GND`, sensor `GND`, and TB6612FNG `GND` are tied together as a common ground.
- If the HC-SR04 is powered from 5 V instead of 3.3 V, protect the Pico `GPIO17` echo input with a divider or level shifter.
