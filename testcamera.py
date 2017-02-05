#!/usr/bin/python

import RPi.GPIO as GPIO
import time

shutter_pin = 4
focus_pin = 2

GPIO.setmode(GPIO.BCM)
GPIO.setup(shutter_pin, GPIO.OUT)
GPIO.setup(focus_pin, GPIO.OUT)


GPIO.output(shutter_pin, GPIO.LOW)
GPIO.output(focus_pin, GPIO.LOW)



for i in xrange(10):
  time.sleep(1.0)

  #print "FOCUS"
  #GPIO.output(focus_pin, GPIO.HIGH)
  #time.sleep(0.2)
  #GPIO.output(focus_pin, GPIO.LOW)

  #time.sleep(0.2)

  print "CLICK %d"%i
  GPIO.output(shutter_pin, GPIO.HIGH)
  time.sleep(0.1)
  GPIO.output(shutter_pin, GPIO.LOW)



GPIO.cleanup()

