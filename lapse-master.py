#!/usr/bin/python
import os, sys
import zmq
import RPi.GPIO as GPIO
import time
import math
import logging
import sched
import scipy.optimize
import subprocess
from info import Info

# BUG: direction pin always high....short on HAT board?

###############################################################
# not really relevant now, since a calibration curve is now used.
# motor information
motor_RPM = 15.0
# pulley information
pulley_pitch = 0.2 # in cm
pulley_T = 36 # number of teeth
##############################################################

##############################################################
# RPi pin configuration
motor_pin = 6 
motor_dir1 = 5
motor_dir2 = 10 
program_pins = [19,13,26,21]
shutter_pin = 4
focus_pin = 2
##############################################################


log_filename="/var/log/dlapse-master.log"

def wait(duration):
   time.sleep(duration)

def motor_pulse(duration, forward=True):
   logging.info("Motor pulse %d, forward=%d"%(duration, int(forward))
   set_motor_direction(forward)
   motor_on()
   wait(duration)
   motor_off()

def motor_on():
   GPIO.output(motor_pin, GPIO.HIGH)

def motor_off():
   GPIO.output(motor_pin, GPIO.LOW)
  
def take_picture():
   logging.info("Taking picture.")
   GPIO.output(shutter_pin, GPIO.HIGH) 
   wait(0.1)
   GPIO.output(shutter_pin, GPIO.LOW) 

def set_motor_direction(forward=True):
   if forward:
      GPIO.output(motor_dir1, GPIO.HIGH)
      GPIO.output(motor_dir2, GPIO.LOW)
   else:
      GPIO.output(motor_dir1, GPIO.LOW)
      GPIO.output(motor_dir2, GPIO.HIGH)

  
def low_power():
   # saves 25-30 mA 
   cmd = "/usr/bin/tvservice -o"
   os.system(cmd)

   # saves ~5mA
   cmd = "echo none | tee /sys/class/leds/led0/trigger"
   os.system(cmd)

   cmd = "echo 1 | tee /sys/class/leds/led0/brightness"
   os.system(cmd)

def setup_gpio():
   GPIO.setmode(GPIO.BCM)
   GPIO.setup(motor_pin, GPIO.OUT)
   GPIO.setup(motor_dir1, GPIO.OUT)
   GPIO.setup(motor_dir2, GPIO.OUT)
   GPIO.setup(shutter_pin, GPIO.OUT)
   GPIO.setup(focus_pin, GPIO.OUT)

   for p in program_pins:
      GPIO.setup(p, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

   GPIO.output(shutter_pin, GPIO.LOW)
   GPIO.output(focus_pin, GPIO.LOW)
   
   motor_off()


def cleanup_gpio():
   GPIO.cleanup()



def do_time_lapse(frames, dt, pulselength, forward=True):


    logging.info("Starting Time Lapse")
    logging.info("  Frames = %d"%frames)
    logging.info("Dt = %lf"%dt)
    logging.info("MotorPulse = %lf"%pulselength)
    logging.info("Forward = %d"%forward)

    allowance = 0.1*dt # the camera shutter speed should always be less than this....
                       # because we don't have the user input it as info.

    take_picture() 
    wait(allowance)

    for i in xrange(frames-1):
       motor_pulse(pulselength, forward)
       wait(dt-allowance)
       take_picture() 
       wait(allowance)


def check_jumpers():
    states = [GPIO.input(p) for p in program_pins]
    for s in states:
       logging.info("State: %s"%str(s))

    if states[0] or states[1] or states[2]:
       info = Info(tlen=15.0, framerate=24, cliplen=6.0, raildist=50.0, reverse=False)
       do_time_lapse(info.frames, info.dt,  info.motorpulse, info.forward) 
       return True
    
    return False



if __name__ == "__main__":
    logging.basicConfig(filename=log_filename, level=logging.DEBUG)
    logging.getLogger().addHandler(logging.StreamHandler())
    formatter = logging.Formatter('%(asctime)s %(process)d %(levelname)s: %(message)s')
    for handler in logging.getLogger().handlers:
        handler.setFormatter(formatter)
    logging.info("Start.")

     
    
    setup_gpio() 
    try:
       low_power()
       if not check_jumpers():
          logging.info("Running GUI.")
          # TODO: must wait until the network is up!!!
          os.system("pkill lapse-gui")
          subprocess.Popen(["python","lapse-gui.py"])
          logging.info("Finishing spawning GUI.")
          logging.info("Listening for commands from the GUI.")  
          context = zmq.Context()
          socket = context.socket(zmq.PAIR)
          socket.bind("tcp://*:5556")
          while True:
              msg = socket.recv()
              if msg == "start lapse":
                 info = socket.recv_pyobj()
                 do_time_lapse(info.frames, info.dt,  info.motorpulse, info.forward) 
              time.sleep(1) 
            
    finally:
       cleanup_gpio()
