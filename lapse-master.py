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


log_filename="/var/log/dlapse-master.log"

def wait(duration):
   time.sleep(duration)

def motor_pulse(duration, forward=True):
   logging.info("Motor pulse %d, forward=%d"%(duration, int(forward)))
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
   wait(0.2)
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



def do_time_lapse(frames, dt, dx, pulselength, forward=True, pub=None, commands=None):


    logging.info("Starting Time Lapse")
    logging.info("  Frames = %d"%frames)
    logging.info("Dt = %lf"%dt)
    logging.info("MotorPulse = %lf"%pulselength)
    logging.info("Forward = %d"%forward)

    # PROBLEM: really, we need to do better here.
    allowance = 0.1*dt # the camera shutter speed should always be less than this....
                       # because we don't have the user input it as info.

    take_picture() 
    wait(allowance)

    DX = 0.0
    for i in xrange(frames-1):

       if commands: 
          msg = "Running: frame %d of %d, total movement %.0f mm"%(i+2, frames, DX)
          commands.send(msg)

       motor_pulse(pulselength, forward)

       DX += dx*10.0 # keep track of total movement in mm.

       wait(dt-allowance)
       take_picture() 
       wait(allowance)
 
       # see if we have received a cancel, and if so, break out.
       if commands: 
           try:
              msg = commands.recv(flags=zmq.NOBLOCK) # this is a nonblocking receive.
              if msg == "cancel":
                 logging.info("Master received a cancel from GUI")
                 break
           except zmq.Again:
              pass
       

    # maybe it would be more reliable to send this on the commands socket?
    logging.info("Time lapse finished.")
    if commands: commands.send("finished")


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
          os.system("pkill lapse-gui") # doesn't work.
          lapse_gui_file = os.path.realpath(__file__).replace("master","gui")
          subprocess.Popen(["python", lapse_gui_file])
          logging.info("Finishing spawning GUI.")
          logging.info("Listening for commands from the GUI.")  

          # this socket takes commands from the GUI.  We recognise two commands: "start", and "cancel".
          # if we receive a "start" message, we expect to receive an Info object in the next message.
          context = zmq.Context()
          commands = context.socket(zmq.PAIR)
          commands.bind("tcp://*:5556")

          # this socket is so that the GUI can get feedback on the current state of the time lapse.
          pub=None
          #pub = context.socket(zmq.PUB)
          #pub.bind("tcp://*:5557") 

          while True:
              msg = commands.recv() # this is a blocking receive.
              if msg == "start":
                 logging.info("GUI has told us to start.")
                 info = commands.recv_pyobj()
                 do_time_lapse(info.frames, info.dt, info.dx, info.motorpulse, info.forward, pub, commands) 
            
    finally:
       cleanup_gpio()
