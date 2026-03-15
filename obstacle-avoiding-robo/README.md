# Obstacle-Avoiding Robo Car (Pico 2 W + TB6612FNG)

An obstacle-avoiding robo car using Raspberry Pi Pico 2 W, TB6612FNG dual H-Bridge, and an HC-SR04 ultrasonic sensor. Two ready-to-flash variants are included:

- Single motor: Reverse-until-safe behavior using the left motor only. See [single_motor_main.py](single_motor_main.py).
- Dual motor: Reverse, then turn-in-place with simple validation before resuming. See [dual_motor_main.py](dual_motor_main.py).

Both variants are MicroPython-based and blink the onboard LED while running.

Here is the link to the video: https://youtube.com/shorts/muM9jOU0rGQ?feature=share

## Features

- Obstacle detection: HC-SR04 distance measurement with adaptive slowdown near obstacles.
- Smooth PWM control: 0–100% speed mapped to PWM at 10 kHz; ramped speed changes.
- Two variants: Single-motor reverse-only and dual-motor reverse+turn with retries.
- Safe defaults: Reverse safety timeout; driver disabled on stop.

## Hardware

- Board: Raspberry Pi Pico 2 W (MicroPython).
- Motor driver: TB6612FNG (dual channel A/B) with STBY standby pin.
- Motors: 1× DC motor (single) or 2× DC motors (dual).
- Sensor: HC-SR04 ultrasonic.
- Power: VM (motors/battery), VCC (logic). Common ground required between Pico, driver, and sensor.

## Wiring

- Diagrams
  - Single-motor: [Obstacle_avoiding_robo_car_wiring_single_motor.png](Obstacle_avoiding_robo_car_wiring_single_motor.png)
  - Dual-motor: [Obstacle_avoiding_robo_car_wiring_dual_motor.png](Obstacle_avoiding_robo_car_wiring_dual_motor.png)
- Reference: Existing Miro wiring board link (kept for additional clarity): https://miro.com/app/board/uXjVGOnAl5s=/?share_link_id=999963932204
- Notes
  - Tie grounds: Pico GND, TB6612FNG GND, sensor GND, and battery negative.
  - TB6612FNG STBY must be driven high to enable outputs.
  - If HC-SR04 runs at 5 V, ensure the Echo signal to the Pico is 3.3 V safe (divider/level shifter).
  - Motor polarity may need swapping to match “forward” with the code.

## Pin Map (GPIO)

- Common
  - STBY: 12
  - TRIG: 16
  - ECHO: 17
  - LED: onboard (“LED”)
- Single motor (left / channel A) — [single_motor_main.py](single_motor_main.py)
  - LEFT_PWM: 15
  - LEFT_IN1: 14
  - LEFT_IN2: 13
- Dual motor (adds right / channel B) — [dual_motor_main.py](dual_motor_main.py)
  - RIGHT_PWM: 8
  - RIGHT_IN1: 7
  - RIGHT_IN2: 6

## Quick Start

1) Flash MicroPython on Pico 2 W and wire according to the diagram for your variant.
2) Copy the chosen file to the Pico and name it `main.py` to auto-run on power.
   - Single motor: [single_motor_main.py](single_motor_main.py)
   - Dual motor: [dual_motor_main.py](dual_motor_main.py)
3) Power on; the onboard LED will blink as the script runs.

## Setup / Flashing

- Install MicroPython on the Pico 2 W (via Thonny or UF2 drag-and-drop).
- Choose your variant and rename it to `main.py` on the Pico filesystem to auto-run on boot.
- On boot, the onboard LED blinks as the script runs.

## How to Run

- Default demo: Each script calls `simplified_run(20000)` to run ~20 seconds, then stop and disable the driver.
- Continuous operation (recommended):
  - Increase the time limit in the final `simplified_run(...)` call (e.g., use a large value for multi-minute runs), or
  - Edit the script to loop indefinitely before flashing as `main.py`.
- Expected behavior
  - Single motor: Forward cruise, adaptive slowdown near obstacles, reverse-until-safe, then resume.
  - Dual motor: Stop → reverse-until-safe → turn-in-place (alternating direction with validation/retry) → resume.

## Tuning / Calibration

- Shared (both scripts)
  - THRESHOLD_CM: Start avoidance below this distance (single: ~30; dual: ~50 by default).
  - CRUISE_SPEED: Forward speed (0–100%).
  - REVERSE_SPEED: Reverse speed (0–100%).
  - MAX_REVERSE_MS: Safety cap for maximum reverse duration.
  - Ramps and cadence: RAMP_TIME_MS, DECEL_RAMP_MS, RESUME_RAMP_MS, ADAPTIVE_THRESHOLD_MULT, LOOP_DELAY_MS.
- Dual-only (in [dual_motor_main.py](dual_motor_main.py))
  - Turning: TURN_MS, TURN_SPEED, TURN_RAMP_MS, TURN_SETTLE_MS.
  - Validation: TURN_MAX_RETRIES, TURN_VALIDATION_PAUSE_MS.
  - Cruise hysteresis: CRUISE_HYSTERESIS_FACTOR reduces re-ramping chatter near target speed.

## Troubleshooting

- Motors don’t move:
  - Ensure STBY is high; verify VM battery and common ground; confirm PWM pin mapping.
- Jerky/weak motion:
  - Check battery current capability and wiring; the default 10 kHz PWM is fine for most drivers; verify mechanical drag.
- Wrong direction:
  - Swap motor leads or swap IN1/IN2 wiring on the corresponding channel.
- Sensor reads 0 or times out:
  - Verify TRIG and ECHO wiring and sensor power; make Echo 3.3 V safe when powering HC-SR04 from 5 V; avoid very close ranges (<2–3 cm).
- Random resets:
  - Power brownouts under stall; use a capable battery, add bulk and ceramic decoupling near the TB6612FNG.

## Safety & Power

- Separate VM (motors) and VCC (logic) per TB6612FNG guidelines; always share ground.
- Add bulk and ceramic decoupling near the motor driver.
- Respect motor stall current and thermal limits on the driver.

## Files

- Single-motor variant: [single_motor_main.py](single_motor_main.py)
- Dual-motor variant: [dual_motor_main.py](dual_motor_main.py)
- Wiring diagrams:
  - [Obstacle_avoiding_robo_car_wiring_single_motor.png](Obstacle_avoiding_robo_car_wiring_single_motor.png)
  - [Obstacle_avoiding_robo_car_wiring_dual_motor.png](Obstacle_avoiding_robo_car_wiring_dual_motor.png)

Notes

- Removed references to non-existent files (separate main.py source, main_original.py, drive_and_avoid.py, pins.py, test.py) and aligned docs to the two actual variant scripts.
