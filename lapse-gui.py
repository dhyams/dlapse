#!/usr/bin/python
import os, sys
import remi
import zmq
import remi.gui as gui
import time
import logging
from lapse_util import Info
import lapse_util as util
import threading




##############################################################
address = '192.168.1.7'
port = 80
log_filename = '/var/log/dlapse.log'
pid_file = "/tmp/dlapse-gui.pid"
##############################################################


class MyTimer(threading.Thread):
    def __init__(self, event, delay, callback):
        threading.Thread.__init__(self)
        self.delay = delay
        self.stopped = event
        self.callback = callback

    def run(self):
        while not self.stopped.wait(self.delay):
            self.callback()



class TimeLapse(remi.App):
    def __init__(self, *args):
        super(TimeLapse, self).__init__(*args)

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

        self.info_status  = make_infoshow('Status')
        self.sp_length    = make_spinbox('Time Length (min)', val=20, min=2, max=120, handler=self.OnInfoChanged)
        self.sp_raildist  = make_spinbox('Distance Along Rail (cm)', val=95, min=10, max=95, handler=self.OnInfoChanged)
        self.sp_framerate = make_spinbox('Clip Frame Rate', val=30, min=10, max=120, handler=self.OnInfoChanged)
        self.sp_cliplen   = make_spinbox('Clip Duration', val=6, min=1, max=30, handler=self.OnInfoChanged)
        self.cb_motorreverse = make_checkbox('Motor Direction', 'Right-to-Left', handler=self.OnInfoChanged)

        self.info_interval  = make_infoshow('Time Between Shots')
        self.info_shotcount = make_infoshow('Number of Shots')
        self.info_railincr  = make_infoshow('Rail Increment (cm)')
        self.info_motorpulse  = make_infoshow('Motor Pulse (sec)')

        sub1 = gui.HBox(width='100%', height=50)
        sub1.style['position'] = 'relative'

        # Start button
        self.bt_start = gui.Button('Start', width='100%', height=30, margin='10px')
        self.bt_start.set_on_click_listener(self.on_start, title)
        sub1.append(self.bt_start)

        # Cancel button
        self.bt_cancel = gui.Button('Cancel', width='100%', height=30, margin='10px')
        self.bt_cancel.set_on_click_listener(self.on_cancel, title)
        sub1.append(self.bt_cancel)

        # Rewind button
        self.bt_rewind = gui.Button('Rewind(2)', width='100%', height=30, margin='10px')
        self.bt_rewind.set_on_click_listener(self.on_rewind, title)
        sub1.append(self.bt_rewind)

        main.append(sub1)

        self.enable_gui()
        self.UpdateInfo() 


        # returning the root widget
        return main

    # listener function
    def on_start(self, widget, title):

        info = self.GetInfo()

        title.set_text('Starting Time Lapse.')  

        self.enable_gui(False)

        socket.send("start")
        socket.send_pyobj(info)

    def enable_gui(self, enabled=True):
       
        self.bt_start.set_enabled(enabled)
        self.bt_cancel.set_enabled(not enabled)
        self.bt_rewind.set_enabled(enabled)
        self.sp_length.set_enabled(enabled)
        self.sp_raildist.set_enabled(enabled)
        self.sp_framerate.set_enabled(enabled)
        self.sp_cliplen.set_enabled(enabled)
        self.cb_motorreverse.set_enabled(enabled)
       
        if enabled:
           self.info_status.set_text("Waiting for input.")

           if hasattr(self,'stopFlag'): 
              self.stopFlag.set()
              del self.stopFlag
        
        else:
           self.info_status.set_text("Waiting for communication from master.")

           self.stopFlag = threading.Event()
           self.timer = MyTimer(self.stopFlag, 2, self.on_timer)
           self.timer.daemon = True
           self.timer.start()  
         

    def on_cancel(self, widget, title):
        socket.send("cancel") 

    def on_rewind(self, widget, title):
        # TODO: pop a dialog to ask user how long to rewind.

        info = self.GetInfo()

        info.rewind = 2.0  # TODO FILL THIS IN

        socket.send("rewind")
        socket.send_pyobj(info)
        
    def on_timer(self):
        msg = ''
        try:
            while True:
                msg = socket.recv(flags=zmq.NOBLOCK) 
                if msg == "finished": 
                   self.enable_gui(True)
                   break
        except zmq.Again:
            if msg: 
               self.info_status.set_text(msg)
        except:
            import traceback
            logging.info(traceback.format_exc())
               

    def OnInfoChanged(self, widget, newValue):
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

    global socket
    context = zmq.Context()
    socket = context.socket(zmq.PAIR)
    socket.connect("tcp://localhost:5556")

    try:
       remi.start(TimeLapse, address=address, port=port, multiple_instance=False, enable_file_cache=True, update_interval=1.0, start_browser=False)
    finally:
       util.cleanup_pid_file(pid_file)
