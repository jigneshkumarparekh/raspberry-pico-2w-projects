# Pico 2w Motion Sensor

This project demonstrates how to detect motion using a motion sensor (PIR - Passive Infrared) with the Raspberry Pi Pico 2w.

## Overview

Motion sensors are useful for security systems, automatic lighting, and presence detection. This project uses a PIR (Passive Infrared) sensor to detect motion and trigger actions on the Pico 2w.

## Components Required

- Raspberry Pi Pico 2w
- PIR Motion Sensor (e.g., HC-SR501)
- Power supply (5V for typical PIR sensors)
- Breadboard and jumper wires
- LED (optional, for visual feedback)
- Resistor (220Ω - 1kΩ if using LED)

## Files

- `motion-sensor.py` - Motion sensor detection implementation
- `blink.py` - Basic LED blink test
- `README.md` - This file

## How It Works

A PIR (Passive Infrared) sensor detects changes in infrared radiation caused by moving heat sources (like human movement). When motion is detected, the sensor outputs a signal that can be read by the Pico 2w.

## Wiring

Typical PIR sensor pinout (HC-SR501):

- VCC: 5V or 3.3V (check sensor specifications)
- GND: Ground
- OUT: Connected to a GPIO pin on the Pico 2w (e.g., GPIO 16)

Optional LED for visual feedback:

- Connect LED positive through a 220Ω resistor to another GPIO pin
- Connect LED negative to GND

## Usage

1. Connect your PIR sensor to the Pico 2w
2. Update the GPIO pin numbers in `motion-sensor.py` if needed
3. Upload the script to your Pico 2w
4. Monitor the serial output to see motion detection events

## Features

- Real-time motion detection
- Serial output for event logging
- Optional LED indicator
- Configurable sensitivity (via sensor potentiometer)
- Debounce handling to avoid false triggers

## Sensor Calibration

Most PIR sensors have adjustment potentiometers:

- **Sensitivity**: Adjust the range of motion detection (typically 3-7 meters)
- **Time Delay**: Adjust how long the sensor holds the output HIGH after motion detection (typically 5-300 seconds)

Refer to your specific sensor's datasheet for calibration instructions.

## Notes

- PIR sensors require a warm-up period (typically 30-60 seconds) after power-up
- Some sensors have adjustable timing and sensitivity via potentiometers on the module
- False triggers can occur from pets, fans, or sudden temperature changes
- Proper mounting and calibration reduce false positives
