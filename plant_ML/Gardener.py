"""
This application is used to pull data from the Arduino and to drive the relay that controls the irrigation pump.
"""

#!/usr/bin/env python3
import serial
import RPi.GPIO as GPIO
import time
from datetime import datetime
from pytz import timezone

# Gardener Class for activating water pump via Relay
class WaterPump:
    def __init__(self):
        pass
        # Water pump is connected to relay whose power is controlled by GPIO 32
        # Power is normally off
        # Power is turned on when plants need watered
        # GPIO.setmode(GPIO.BCM)
        # GPIO.setwarnings(False)
        # pumpPin = 12
        # GPIO.setup(pumpPin, GPIO.OUT)
        # Sometimes need this line
        # # GPIO.output(pumpPin, True)
    
    def runPump(seconds):
        pass
        # False = ON, True = OFF
        # GPIO.output(pumpPin, False)
        # time.sleep(5)
        # GPIO.output(pumpPin, True)

# Gardener Class for reading Arduino Data
class SensorStream:
    def __init__(self):
        # Sensor data is read by serial communication with Arduino
        # Arduino interprets the moisture and sends it
        # Python gets those data points and stores them here
        self.s0 = 0
        self.s1 = 0
        self.s2 = 0
            
    def readSensors(self):
        # Create serial communication with Arduino
        # Arduino is connected to soil moisture sensors
        self.ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1)
        self.ser.flush()
        while True:
            if self.ser.in_waiting > 0:
                # Read data from serial
                line = self.ser.readline().decode('utf-8').rstrip()
                # Parse data
                values = line.split(' ')
                self.s0 = int(values[0])
                self.s1 = int(values[1])
                self.s2 = int(values[2])
