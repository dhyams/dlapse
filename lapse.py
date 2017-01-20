
import remi
import remi.gui as gui

# motor information
motor_RPM = 15.0

# pulley information
pulley_pitch = 0.2 # in cm
pulley_T = 36 # number of teeth





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
        # TODO: read all of the controls
        title.set_text('Starting Time Lapse.') 
        
        #self.do_time_lapse()

    def OnLengthChanged(self, widget, newValue):
        self.UpdateInfo()

    def OnClipFrameRateChanged(self, widget, newValue):
        self.UpdateInfo()

    def OnClipLengthChanged(self, widget, newValue):
        self.UpdateInfo()

    def OnRailDistanceChanged(self, widget, newValue):
        self.UpdateInfo()

    def UpdateInfo(self):
        # update the time interval between shots, and the shot count.
        # can also guesstimate the total size of the shoot for a Canon 70D.
 
        tlen = int(self.sp_length.get_value())
        framerate = int(self.sp_framerate.get_value())
        cliplen = int(self.sp_cliplen.get_value())
     
        frames = framerate*cliplen
        duration = float(tlen)/float(frames)*60.0 # in seconds
   
        self.info_interval.set_text('%.1f sec'%duration)
        self.info_shotcount.set_text(str(frames)) 


        raildist = int(self.sp_raildist.get_value())
        railincr = float(raildist)/float(frames-1)

        self.info_railincr.set_text('%.1f cm'%railincr)

        d = railincr
        import math
        RPM = motor_RPM 
        pitch = pulley_pitch # cm
        T = pulley_T   # tooth count 
        Dp = pitch*T/math.pi
        print "Diameter of pully", Dp
        Vr = Dp/2.0*RPM*(2.0*math.pi/60.0) 
        motorpulse = d/Vr 
        self.info_motorpulse.set_text('%.3f sec'%motorpulse)
 

        
    #def on_button_mousedown(self, widget, x, y, mydata1, mydata2, mydata3):
    #    print("x:%s  y:%s  data1:%s  data2:%s  data3:%s"%(x, y, mydata1, mydata2, mydata3))
    #    
    #def on_button_mouseup(self, widget, x, y, mydata1):
    #    print("x:%s  y:%s  data1:%s"%(x, y, mydata1))

    #def on_button_mouseup2(self, widget, x, y):
    #    print("x:%s  y:%s  no userdata"%(x, y))


if __name__ == "__main__":
    remi.start(MyApp, address='192.168.1.7', port=8081, multiple_instance=False, enable_file_cache=True, update_interval=0.1, start_browser=False)
