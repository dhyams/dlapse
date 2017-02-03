#!/usr/bin/python

import RPi.GPIO as GPIO
import time

motor_pin = 6 
motor_dir1 = 5
motor_dir2 = 10 

def wait(duration):
   time.sleep(duration)

def motor_on(duration, forward=True):
   set_motor_direction(forward)
   GPIO.output(motor_pin, GPIO.HIGH)
   wait(duration)
   GPIO.output(motor_pin, GPIO.LOW)

def set_motor_direction(forward=True):
   if forward:
      GPIO.output(motor_dir1, GPIO.HIGH)
      GPIO.output(motor_dir2, GPIO.LOW)
   else:
      GPIO.output(motor_dir1, GPIO.LOW)
      GPIO.output(motor_dir2, GPIO.HIGH)
   

GPIO.setmode(GPIO.BCM)
GPIO.setup(motor_pin, GPIO.OUT)
GPIO.setup(motor_dir1, GPIO.OUT)
GPIO.setup(motor_dir2, GPIO.OUT)

wait(1.0)

motor_on(1.0, True)

wait(1.0)

motor_on(1.0, False)



GPIO.cleanup()

