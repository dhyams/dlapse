#!/usr/bin/python
import remi
import remi.gui as gui
import RPi.GPIO as GPIO
import time
import math

# motor information
motor_RPM = 15.0

# pulley information
pulley_pitch = 0.2 # in cm
pulley_T = 36 # number of teeth

motor_pin = 6 
motor_dir1 = 5
motor_dir2 = 10 

def wait(duration):
   time.sleep(duration)

def motor_pulse(duration, forward=True):
   set_motor_direction(forward)
   motor_on()
   wait(duration)
   motor_off()

def motor_on():
   GPIO.output(motor_pin, GPIO.HIGH)

def motor_off():
   GPIO.output(motor_pin, GPIO.LOW)
   

def set_motor_direction(forward=True):
   if forward:
      GPIO.output(motor_dir1, GPIO.HIGH)
      GPIO.output(motor_dir2, GPIO.LOW)
   else:
      GPIO.output(motor_dir1, GPIO.LOW)
      GPIO.output(motor_dir2, GPIO.HIGH)
   

def setup_gpio():
   GPIO.setmode(GPIO.BCM)
   GPIO.setup(motor_pin, GPIO.OUT)
   GPIO.setup(motor_dir1, GPIO.OUT)
   GPIO.setup(motor_dir2, GPIO.OUT)

def cleanup_gpio():
   GPIO.cleanup()



class Info(object):
   def __init__(self, tlen, framerate, cliplen, raildist):
        tlen *= 60                     # convert time length from minutes to seconds
        self.tlen = tlen               # in seconds
        self.framerate = framerate     # count
        self.cliplen = cliplen         # in seconds
        self.raildist = raildist       # in cm

        self.frames = framerate*cliplen
        self.dt     = float(tlen)/float(self.frames-1) # in seconds
        self.dx     = float(raildist)/float(self.frames-1) # in cm

        self.forward = True

        d = self.dx
        RPM = motor_RPM 
        pitch = pulley_pitch # cm
        T = pulley_T   # tooth count 
        Dp = pitch*T/math.pi
        Vr = Dp/2.0*RPM*(2.0*math.pi/60.0) 
        self.motorpulse = d/Vr 

   def __str__(self):
        s = "INFO:\n"
        s += "Time Length: %d s "%self.tlen  + '\n'
        s += "Frame Rate : %d"%self.framerate  + '\n'
        s += "Clip Length: %d"%self.cliplen  + '\n'
        s += "Rail Dist  : %d"%self.raildist  + '\n'
        s += "Frames     : %d"%self.frames  + '\n'
        s += "Dt         : %f sec"%self.dt  + '\n'
        s += "Dx         : %f cm"%self.dx  + '\n'
        s += "MotorPulse : %f sec"%self.motorpulse  + '\n'
        return s



class MyApp(remi.App):
    def __init__(self, *args):
        super(MyApp, self).__init__(*args)

    def main(self, name='world'):
        main = gui.Widget(width='100%', height=600, margin='0px auto') #margin 0px auto allows to center the app to the screen
        main.style["position"] = "relative"

        def make_spinbox(label, val, min=1, max=100, step=1, handler=None):

            lb = gui.Label(label, width='50%', height=30, margin='10px')
            sp = gui.SpinBox(default_value=val, min=min, max=max, step=step, allow_editing=True,  width='50%', height=30, margin='10px')

            sub1 = gui.HBox(width='100%', height=50)
            sub1.style['position'] = 'relative'
            sub1.append(lb)
            sub1.append(sp)

            if handler: sp.set_on_change_listener(handler) 

            main.append(sub1)
            return sp

        def make_infoshow(label):
            lb = gui.Label(label, width='50%', height=30, margin='10px')
            lbinfo = gui.Label('', width='50%', height=30, margin='10px')

            sub1 = gui.HBox(width='100%', height=50)
            sub1.style['position'] = 'relative'
            sub1.append(lb)
            sub1.append(lbinfo)

            main.append(sub1)
            return lbinfo

        title = gui.Label('Time Lapse Controller', width='80%', height=30)
        #title.style['margin'] = 'auto'
        main.append(title)

        self.sp_length    = make_spinbox('Time Length (min)', val=20, min=2, max=120, handler=self.OnLengthChanged)
        self.sp_raildist  = make_spinbox('Distance Along Rail (cm)', val=95, min=10, max=95, handler=self.OnRailDistanceChanged)
        self.sp_framerate = make_spinbox('Clip Frame Rate', val=30, min=10, max=120, handler=self.OnClipFrameRateChanged)
        self.sp_cliplen   = make_spinbox('Clip Duration', val=6, min=1, max=30, handler=self.OnClipLengthChanged)

        self.info_interval  = make_infoshow('Time Between Shots')
        self.info_shotcount = make_infoshow('Number of Shots')
        self.info_railincr  = make_infoshow('Rail Increment (cm)')
        self.info_motorpulse  = make_infoshow('Motor Pulse (sec)')

        # part of the rail to use

        # Start button
        self.bt_start = gui.Button('Start', width='100%', height=30, margin='10px')
        self.bt_start.set_on_click_listener(self.on_start, title)
        main.append(self.bt_start)

        # TODO: add widgets that show the status of a shoot during the shoot.  Time left, shots taken, dist down rail, etc.
     
        self.UpdateInfo() 

        # returning the root widget
        return main

    # listener function
    def on_start(self, widget, title):

        info = self.GetInfo()

        title.set_text('Starting Time Lapse.')  

        print info
 
        self.do_time_lapse(info.frames, info.dt,  info.motorpulse, info.forward)

    def do_time_lapse(self, frames, dt, pulselength, forward=True):

        print "Frames = ", frames
        print "Dt = ", dt
        print "MotorPulse = ", pulselength
        print "Forward = ", forward

        allowance = 0.1*dt # the camera shutter speed should always be less than this....
                           # because we don't have the user input it as info.
        self.take_picture() 
        for i in xrange(frames-1):
           motor_pulse(pulselength, forward)
           wait(dt-allowance)
           self.take_picture() 
           wait(allowance)

    def take_picture(self):
        print "Click!"
             

    def OnLengthChanged(self, widget, newValue):
        self.UpdateInfo()

    def OnClipFrameRateChanged(self, widget, newValue):
        self.UpdateInfo()

    def OnClipLengthChanged(self, widget, newValue):
        self.UpdateInfo()

    def OnRailDistanceChanged(self, widget, newValue):
        self.UpdateInfo()

    def GetInfo(self):
        # update the time interval between shots, and the shot count.
        # can also guesstimate the total size of the shoot for a Canon 70D.

        tlen = int(self.sp_length.get_value())     # in minutes
        framerate = int(self.sp_framerate.get_value())  # count
        cliplen = int(self.sp_cliplen.get_value())    # in seconds
        raildist = int(self.sp_raildist.get_value())  # in cm

        info = Info(tlen, framerate, cliplen, raildist)

        return info
     
    
    def UpdateInfo(self):
        info = self.GetInfo() 

        self.info_interval.set_text('%.1f sec'%info.dt)
        self.info_shotcount.set_text(str(info.frames)) 
        self.info_railincr.set_text('%.1f cm'%info.dx)
        self.info_motorpulse.set_text('%.3f sec'%info.motorpulse)
        
    #def on_button_mousedown(self, widget, x, y, mydata1, mydata2, mydata3):
    #    print("x:%s  y:%s  data1:%s  data2:%s  data3:%s"%(x, y, mydata1, mydata2, mydata3))
    #    
    #def on_button_mouseup(self, widget, x, y, mydata1):
    #    print("x:%s  y:%s  data1:%s"%(x, y, mydata1))

    #def on_button_mouseup2(self, widget, x, y):
    #    print("x:%s  y:%s  no userdata"%(x, y))


if __name__ == "__main__":
    setup_gpio() 
    motor_off()
    try:
       remi.start(MyApp, address='192.168.1.7', port=8081, multiple_instance=False, enable_file_cache=True, update_interval=0.1, start_browser=False)

    finally:
       cleanup_gpio()
