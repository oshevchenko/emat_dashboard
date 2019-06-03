import message_queue as mq
# -*- coding: utf-8 -*-
# print("Loading HaasoscopeLib.py")

from serial import Serial, SerialException
from struct import unpack
import numpy as np
import time, json, os
import matplotlib
from const import *


mearm=False
mewin=False
try:
    print((os.uname()))
    if os.uname()[4].startswith("arm") or os.uname()[4].startswith("aarch"):
        print("On a raspberry pi?")
        mearm=True
except AttributeError:
    mewin=True
    print("Not on Linux?")

dofast=False #do the fast way of redrawing, just the specific things that could have likely changed, only works well on Windows?
if mewin:
    dofast=True
    matplotlib.use('Qt4Agg')
#to print possible backends
#import matplotlib.rcsetup as rcsetup
#print rcsetup.interactive_bk
# import matplotlib.pyplot as plt
# print(("matplotlib backend is",plt.get_backend()))


from scipy.signal import resample
import serial.tools.list_ports
import scipy.optimize

class PsSerial():

    def __init__(self):

        self.mq_adapter = mq.Adapter('main_queue')
        self.mq_publisher = mq.Publisher(self.mq_adapter)

        self.serialdelaytimerwait=100 #150 # 600 # delay (in 2 us steps) between each 32 bytes of serial output (set to 600 for some slow USB serial setups, but 0 normally)
        if mearm: self.serialdelaytimerwait=600
        self.brate = 1500000 #serial baud rate #1500000 #115200 #921600
        self.sertimeout = 3.0 #time to wait for serial response #3.0, HAAS_NUM_BYTES*8*10.0/brate, or None
        self.serport="" # the name of the serial port on your computer, connected to Haasoscope, like /dev/ttyUSB0 or COM8, leave blank to detect automatically!



    #cleanup
    def cleanup(self):
        try:
            if self.serport!="" and hasattr(self,'ser'):
                self.ser.close()
        except SerialException:
            print("failed to talk to board when cleaning up!")
        print("bye bye!")

    def hvon(self):
        frame=[]
        s="hv on\r"
        frame.extend(s.encode())
        self.ser.write(frame)

    def hvoff(self):
        frame=[]
        s="hv off\r"
        frame.extend(s.encode())
        self.ser.write(frame)

    #For setting up serial and USB connections
    def setup_connections(self):
        # serialrate=adjustedbrate/11./(HAAS_NUM_BYTES*HAAS_NUM_BOARD+len(HAAS_MAX10ADCCHANS)*HAAS_NSAMP) #including start+2stop bits
        # print(("rate theoretically",round(serialrate,2),"Hz over serial"))
        print(">>> PsSerial>>>")

        ports = list(serial.tools.list_ports.comports()); ports.sort(reverse=True)

        for port_no, description, address in ports: print((port_no,":",description,":",address))
        for port_no, description, address in ports:
            if self.serport=="":
                if '0483:5740' in address: self.serport = port_no
        if self.serport!="":
            try:
                self.ser = Serial(self.serport,self.brate,timeout=self.sertimeout,stopbits=2)
            except SerialException:
                print(("Could not open",self.serport,"!")); return False
            print(("connected serial to",self.serport,", timeout",self.sertimeout,"seconds"))
        else: self.ser=""
        if self.serport=="": print("No serial COM port opened!"); return False
        return True
