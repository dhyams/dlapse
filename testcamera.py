#!/usr/bin/python

import RPi.GPIO as GPIO
import time

focus_pin = 4
shutter_pin = 2

GPIO.setmode(GPIO.BCM)
GPIO.setup(shutter_pin, GPIO.OUT)
GPIO.setup(focus_pin, GPIO.OUT)


GPIO.output(shutter_pin, GPIO.LOW)
GPIO.output(focus_pin, GPIO.LOW)

time.sleep(10)

print "CLICK"
GPIO.output(shutter_pin, GPIO.HIGH)
GPIO.output(focus_pin, GPIO.HIGH)
time.sleep(0.1)
GPIO.output(shutter_pin, GPIO.LOW)



GPIO.cleanup()

