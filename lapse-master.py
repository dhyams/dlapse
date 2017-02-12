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
from lapse_util import Info
import lapse_util as util

# Prerequisities:
#  remi (download and install with python setup.py)
#  zeromq (pip install zmq)
#  scipy  (apt-get install python-scipy)
#  psutil (pip install psutil)


# BUG: direction pin always high....short on HAT board? Answer: yes, it's bridged to 3.3V.
# TODO: need a good way to kill GUI process if the master goes down.


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


##############################################################
# other setup
log_filename="/var/log/dlapse-master.log"
pid_file = "/tmp/lapse-master.pid"
##############################################################



def wait(duration):
   time.sleep(duration)

def motor_pulse(duration, forward=True):
   try:
      logging.info("Motor pulse %d, forward=%d"%(duration, int(forward)))
      set_motor_direction(forward)
      motor_on()
      wait(duration)
   finally:
      motor_off()

def motor_on():
   GPIO.output(motor_pin, GPIO.HIGH)

def motor_off():
   GPIO.output(motor_pin, GPIO.LOW)
  
def take_picture():
   try:
      logging.info("Taking picture.")
      GPIO.output(shutter_pin, GPIO.HIGH) 
      wait(0.2)
   finally:
      GPIO.output(shutter_pin, GPIO.LOW) 

def set_motor_direction(forward=True):
   GPIO.output(motor_dir1, GPIO.HIGH if forward else GPIO.LOW)
   GPIO.output(motor_dir2, GPIO.LOW  if forward else GPIO.HIGH)

  
def low_power():
   # saves 25-30 mA; turn HDMI circuitry off.
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



def do_time_lapse(frames, dt, dx, pulselength, forward=True, socket=None):

    logging.info("Starting Time Lapse")
    logging.info("  Frames = %d"%frames)
    logging.info("Dt = %lf"%dt)
    logging.info("MotorPulse = %lf"%pulselength)
    logging.info("Forward = %d"%forward)

    # PROBLEM: really, we need to do better here.
    allowance = 0.1*dt # the camera shutter speed should always be less than this....
                       # because we don't have the user input it as info.

    DX = 0.0
    for i in xrange(frames):
  
       if socket: 
          msg = "Running: frame %d/%d, total movement %.1f mm"%(i+1, frames, DX)
          socket.send(msg)

       DX += dx*10.0 # keep track of total movement in mm.

       if i == 0: # the first picture is special; no movement needed for this one.
          take_picture()
          wait(allowance)
       else: 
          motor_pulse(pulselength, forward)

          wait(dt-allowance)
          take_picture() 
          wait(allowance)

 
       # see if we have received a cancel, and if so, break out.
       if socket: 
           try:
              msg = socket.recv(flags=zmq.NOBLOCK) # this is a nonblocking receive.
              if msg == "cancel":
                 logging.info("Master received a cancel from GUI")
                 break
           except zmq.Again:
              pass
       

    logging.info("Time lapse finished.")
    if socket: socket.send("finished")


def check_jumpers():
    states = [GPIO.input(p) for p in program_pins]
    for s in states:
       logging.info("Program pin state: %s"%str(s))

    # TODO: set up the programs
    if states[0] or states[1] or states[2]:
       info = Info(tlen=15.0, framerate=30, cliplen=8.0, raildist=75.0, reverse=False)

       do_time_lapse(info.frames, info.dt,  info.motorpulse, info.forward) 
       return True
    
    return False

def setup_logging():
    logging.basicConfig(filename=log_filename, level=logging.DEBUG)
    logging.getLogger().addHandler(logging.StreamHandler())
    formatter = logging.Formatter('%(asctime)s %(process)d %(levelname)s: %(message)s')
    for handler in logging.getLogger().handlers:
        handler.setFormatter(formatter)
    logging.info("Start.")



if __name__ == "__main__":
    util.create_pid_file(pid_file)
    setup_logging() 
    setup_gpio() 

    try:
       low_power()
       if not check_jumpers():

          logging.info("Running GUI.") 
          os.system("pkill lapse-gui") # doesn't work.
          lapse_gui_file = os.path.realpath(__file__).replace("master","gui")
          subprocess.Popen(["python", lapse_gui_file])

          logging.info("Finishing spawning GUI.")
          logging.info("Listening for commands from the GUI.")  

          context = zmq.Context()
          socket = context.socket(zmq.PAIR)
          socket.bind("tcp://*:5556")

          while True:
              msg = socket.recv() # this is a blocking receive.

              if msg == "start":
                 logging.info("GUI has told us to start.")
                 info = socket.recv_pyobj()
                 do_time_lapse(info.frames, info.dt, info.dx, info.motorpulse, info.forward, socket) 

              if msg == "rewind":
                 logging.info("GUI has told us to rewind.")
                 info = socket.recv_pyobj()
                 motor_pulse(info.rewind, not info.forward)

            
    finally:
       cleanup_gpio()
       util.cleanup_pid_file(pid_file)
