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


dir = True
wait(1.0)

#pulsewidths = [0.05, 0.10, 0.15, 0.20]
pulsewidths = [0.3, 0.35]
for p in pulsewidths:
   for i in xrange(7):
       print "Pulse: %lf [%d]"%(p, i+1)
       motor_on(p, dir)
       wait(3.0)





GPIO.cleanup()

