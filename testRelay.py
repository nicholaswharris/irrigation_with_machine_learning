#!/usr/bin/env python3

"""
Program is used simply for testing relay that controls water pump.
When testing, use KeyboardInterrupt to ensure that GPIO access is properly cleaned.
Else, high/low might become flipped.
"""

import RPi.GPIO as GPIO
import time

# Using pin 32 to control relay on/off
GPIO.setmode(GPIO.BOARD)
GPIO.setup(32,GPIO.OUT)
GPIO.output(32,GPIO.HIGH)

while (True):
    try:
        GPIO.output(32,GPIO.LOW)
        print("It's on")
        time.sleep(5)
        GPIO.output(32,GPIO.HIGH)
        print("It's off")
        time.sleep(2)
    
    except KeyboardInterrupt:
        print("Cleaning GPIO")
        GPIO.cleanup()
