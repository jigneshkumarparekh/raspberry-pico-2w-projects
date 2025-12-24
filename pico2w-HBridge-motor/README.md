# Pico 2w H-Bridge Motor Control

This project demonstrates how to control DC motors using an H-Bridge motor driver with the Raspberry Pi Pico 2w.

## Overview

The H-Bridge (also known as a full bridge) is an electronic circuit that enables a DC motor to rotate in either direction. This project shows how to wire and control a motor using GPIO pins on the Pico 2w.

## Components Required

- Raspberry Pi Pico 2w
- H-Bridge Motor Driver (e.g., L298N, L9110S)
- DC Motor(s)
- Power supply (appropriate voltage for your motor)
- Breadboard and jumper wires
- Resistors and capacitors (for stability)

## Wiring Guide

Refer to `WIRING_GUIDE.md` for detailed connection instructions.

## Circuit Diagram

See `CIRCUIT_DIAGRAM.md` for the circuit design and connections.

## Files

- `motor.py` - Main motor control implementation
- `blink.py` - Basic LED blink test
- `pico2w_hbridge_motor.fzz` - Fritzing circuit diagram
- `WIRING_GUIDE.md` - Detailed wiring instructions
- `CIRCUIT_DIAGRAM.md` - Circuit design documentation

## Usage

Upload the MicroPython code to your Pico 2w and modify the GPIO pins and control logic as needed for your specific setup.

## Features

- Forward and reverse motor control
- Speed control via PWM
- Safe GPIO pin management
