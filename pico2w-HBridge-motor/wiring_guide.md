# Raspberry Pi Pico 2 W ↔ TB6612FNG Motor Driver Wiring

This document lists the **pin connections** used in the working setup shown in your photos.
Configuration is for **one TT DC motor (Channel A)** using the **TB6612FNG H-Bridge**.

---

## Power Connections

| TB6612FNG Pin | Connects To                      | Notes                      |
| ------------- | -------------------------------- | -------------------------- |
| VM            | External Battery + (AA pack ~6V) | Motor supply               |
| VCC           | Pico 2 W 3V3(OUT)                | Logic supply               |
| GND           | Pico GND + Battery −             | **Common ground required** |

**⚠️ IMPORTANT:**: GND must be common between Battery and Microcontroller

---

## Control Pins (Channel A)

| TB6612FNG Pin | Pico 2 W GPIO | Pico Pin # | Purpose                 |
| ------------- | ------------- | ---------- | ----------------------- |
| PWMA          | GPIO15        | Pin 20     | Motor speed (PWM)       |
| AIN1          | GPIO14        | Pin 19     | Motor direction         |
| AIN2          | GPIO13        | Pin 17     | Motor direction         |
| STBY          | GPIO12        | Pin 16     | Standby (HIGH = enable) |

**⚠️ IMPORTANT:** Remember that the PWM pins of the motor driver need to be PWM pins on your microcontroller.

> STBY must be pulled **HIGH** for the motor driver to operate.

---

## Motor Output

| TB6612FNG Pin | Connects To     |
| ------------- | --------------- |
| AO1           | TT Motor Wire 1 |
| AO2           | TT Motor Wire 2 |

(Swap AO1/AO2 if motor direction is reversed.)

---

## Optional / Unused Pins

| TB6612FNG Pin      | Status   |
| ------------------ | -------- |
| BIN1 / BIN2 / PWMB | Not used |
| BO1 / BO2          | Not used |

---

## Notes

- PWM on **GPIO15** controls speed
- Direction logic:
  - AIN1=1, AIN2=0 → Forward
  - AIN1=0, AIN2=1 → Reverse
  - Both LOW or HIGH → Brake
- Battery **must not** power Pico 3V3 directly

---

## Diagram Reference

Use this pin list together with the generated wiring diagram image for correct placement on the breadboard.
