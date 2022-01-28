#!/usr/bin/env python3

"""
Program is used to test serial communication with Arduino.
"""

import serial
import RPi.GPIO as GPIO
import time
from datetime import datetime
from pytz import timezone

# Set timezone for timestamps
tz = timezone('EST')

# Sensor data is read by serial communication with Arduino
# Arduino interprets the moisture and sends it
# Python gets those data points and stores them here
sensor0 = 0
sensor1 = 0
sensor2 = 0


if __name__ == '__main__':
    ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1)
    ser.flush()
    
    while True:
        if ser.in_waiting > 0:
            # Read data from serial
            line = ser.readline().decode('utf-8').rstrip()
            # Parse data
            values = line.split(' ')
            sensor0 = int(values[0])
            sensor1 = int(values[1])
            sensor2 = int(values[2])
            # Print sensor values
            print("s0 = {}%, s1 = {}%, s2 = {}%".format(sensor0, sensor1, sensor2))
