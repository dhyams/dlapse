#!/usr/bin/python
import os, sys
import remi
import zmq
import remi.gui as gui
import time
import logging
from info import Info




##############################################################
address = '192.168.1.7'
port = 8081
log_filename = '/var/log/dlapse.log'
##############################################################






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

        def make_checkbox(label, labelc, handler=None):
            lb = gui.Label(label, width='50%', height=30, margin='10px')
            cb = gui.CheckBoxLabel(labelc, False, width='50%', height=30, margin='10px')

            sub1 = gui.HBox(width='100%', height=50)
            sub1.style['position'] = 'relative'
            sub1.append(lb)
            sub1.append(cb)

            if handler: cb.set_on_change_listener(handler)
            
            main.append(sub1)  
            return cb

        title = gui.Label('Time Lapse Controller', width='80%', height=30)
        #title.style['margin'] = 'auto'
        main.append(title)

        self.sp_length    = make_spinbox('Time Length (min)', val=20, min=2, max=120, handler=self.OnLengthChanged)
        self.sp_raildist  = make_spinbox('Distance Along Rail (cm)', val=95, min=10, max=95, handler=self.OnRailDistanceChanged)
        self.sp_framerate = make_spinbox('Clip Frame Rate', val=30, min=10, max=120, handler=self.OnClipFrameRateChanged)
        self.sp_cliplen   = make_spinbox('Clip Duration', val=6, min=1, max=30, handler=self.OnClipLengthChanged)
        self.cb_motorreverse = make_checkbox('Motor Direction', 'Right-to-Left', handler=self.OnMotorDirChanged)

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

        #self.scheduler = sched.scheduler(time.time, time.sleep)

        # returning the root widget
        return main

    # listener function
    def on_start(self, widget, title):

        info = self.GetInfo()

        title.set_text('Starting Time Lapse.')  

        self.bt_start.set_enabled(False)

        socket.send("start lapse")

        socket.send_pyobj(info)

        # after this, we should go into "listen" mode....and pick up messages from the server.  Because
        # the server can't progress without us listening, in the PAIR setup.


    def OnLengthChanged(self, widget, newValue):
        self.UpdateInfo()

    def OnMotorDirChanged(self, widget, newValue):
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
        reverse = bool(self.cb_motorreverse.get_value())

        info = Info(tlen, framerate, cliplen, raildist, reverse)

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
    logging.basicConfig(filename=log_filename, level=logging.DEBUG)
    logging.getLogger().addHandler(logging.StreamHandler())
    formatter = logging.Formatter('%(asctime)s %(process)d %(levelname)s: %(message)s')
    for handler in logging.getLogger().handlers:
        handler.setFormatter(formatter)
    logging.info("Start.")


    global socket
    context = zmq.Context()
    socket = context.socket(zmq.PAIR)
    socket.connect("tcp://localhost:5556")

    try:
       remi.start(MyApp, address=address, port=port, multiple_instance=False, enable_file_cache=True, update_interval=1.0, start_browser=False)
    finally:
       pass
