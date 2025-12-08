# Pico 2w Temperature Sensor

This project demonstrates how to read temperature data from a temperature sensor using the Raspberry Pi Pico 2w.

## Overview

Temperature sensing is useful for monitoring environmental conditions or device performance. This project shows how to interface a digital temperature sensor with the Pico 2w and read temperature values.

## Components Required

- Raspberry Pi Pico 2w
- Temperature Sensor (e.g., DS18B20, DHT22, BMP280, or MCP9808)
- Power supply
- Breadboard and jumper wires
- Resistors (pull-up resistors if needed for your sensor)

## Files

- `temp_sensor.py` - Temperature sensor reading implementation
- `README.md` - This file

## Sensor Support

This project can be adapted for various temperature sensors:

- **DS18B20**: 1-Wire digital temperature sensor
- **DHT22**: Humidity and temperature sensor
- **BMP280**: Pressure and temperature sensor
- **MCP9808**: I2C precision temperature sensor

## Wiring

Wiring depends on the specific sensor you're using:

- Most sensors require VCC, GND, and data line(s)
- Some sensors use I2C (SDA/SCL pins)
- Some sensors use 1-Wire protocol
- Refer to your sensor's datasheet for pin configuration

## Usage

1. Connect your temperature sensor to the Pico 2w according to the sensor's specifications
2. Update the GPIO pins and sensor configuration in `temp_sensor.py` if needed
3. Upload the script to your Pico 2w
4. Monitor the serial output to see temperature readings

## Features

- Real-time temperature reading
- Serial output for monitoring
- Configurable sampling interval
- Error handling for sensor reading failures

## Notes

- Different sensors have different accuracy, range, and communication protocols
- Check sensor documentation for proper wiring and initialization
- Some sensors may require external libraries (included in MicroPython or need to be added)
