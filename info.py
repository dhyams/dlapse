import scipy.optimize


def calibration(p):
   # heat capacity model
   a=   2.27422194447785E+00
   b=   1.42230347360781E+01
   c=   -2.41086937157436E-03
   d = a + b*p + c/p/p
   return d

def opt_function(p, dd):
   return calibration(p) - dd


class Info(object):
   def __init__(self, tlen, framerate, cliplen, raildist, reverse):
        tlen *= 60                     # convert time length from minutes to seconds
        self.tlen = tlen               # in seconds
        self.framerate = framerate     # count
        self.cliplen = cliplen         # in seconds
        self.raildist = raildist       # in cm
        self.forward = not reverse

        self.frames = int(framerate*cliplen)
        self.dt     = float(tlen)/float(self.frames-1) # in seconds
        self.dx     = float(raildist)/float(self.frames-1) # in cm


        if 0:
          d = self.dx
          RPM = motor_RPM
          pitch = pulley_pitch # cm
          T = pulley_T   # tooth count
          Dp = pitch*T/math.pi
          Vr = Dp/2.0*RPM*(2.0*math.pi/60.0)
          self.motorpulse = d/Vr
        else:
          try:
             self.motorpulse = scipy.optimize.newton(opt_function, 0.15, args=(self.dx*10.0,))
          except:
             self.motorpulse = 0.1

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

