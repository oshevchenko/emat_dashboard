import message_queue as mq
# -*- coding: utf-8 -*-
print("Loading HaasoscopeLib.py")

from serial import Serial, SerialException
from struct import unpack
import numpy as np
import time, json, os
import matplotlib
from const import *
max10adcchans = []#[(0,110),(0,118),(1,110),(1,118)] #max10adc channels to draw (board, channel on board), channels: 110=ain1, 111=pin6, ..., 118=pin14, 119=temp

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
import matplotlib.pyplot as plt
print(("matplotlib backend is",plt.get_backend()))

#disable some default key mappings
#keymap.fullscreen : f, ctrl+f       # toggling
#keymap.home : h, r, home            # home or reset mnemonic
#keymap.back : left, c, backspace    # forward / backward keys to enable
#keymap.forward : right, v           #   left handed quick navigation
#keymap.pan : p                      # pan mnemonic
#keymap.zoom : o                     # zoom mnemonic
#keymap.save : s                     # saving current figure
#keymap.quit : ctrl+w, cmd+w         # close the current figure
#keymap.grid : g                     # switching on/off a grid in current axes
#keymap.yscale : l                   # toggle scaling of y-axes ('log'/'linear')
#keymap.xscale : L, k                # toggle scaling of x-axes ('log'/'linear')
#keymap.all_axes : a                 # enable all axes
plt.rcParams['keymap.fullscreen'] = ''
plt.rcParams['keymap.home'] = ''
plt.rcParams['keymap.back'] = ''
plt.rcParams['keymap.forward'] = ''
plt.rcParams['keymap.pan'] = ''
plt.rcParams['keymap.zoom'] = ''
#plt.rcParams['keymap.save'] = ''
#plt.rcParams['keymap.quit'] = ''
plt.rcParams['keymap.grid'] = ''
#plt.rcParams['keymap.yscale'] = ''
plt.rcParams['keymap.xscale'] = ''
plt.rcParams['keymap.all_axes'] = ''

from scipy.signal import resample
import serial.tools.list_ports
import scipy.optimize

enable_ripyl=False # set to True to use ripyl serial decoding... have to get it from https://github.com/kevinpt/ripyl and then install it first!
if enable_ripyl:
    import ripyl.util.plot as rplot
    from collections import OrderedDict
    import ripyl.streaming as stream
    import ripyl.protocol.uart as uart

class Haasoscope():

    def construct(self):
        self.mq_adapter = mq.Adapter('main_queue')
        self.mq_publisher = mq.Publisher(self.mq_adapter)

        self.serialdelaytimerwait=100 #150 # 600 # delay (in 2 us steps) between each 32 bytes of serial output (set to 600 for some slow USB serial setups, but 0 normally)
        if mearm: self.serialdelaytimerwait=600
        self.brate = 1500000 #serial baud rate #1500000 #115200 #921600
        self.sertimeout = 3.0 #time to wait for serial response #3.0, num_bytes*8*10.0/brate, or None
        self.serport="" # the name of the serial port on your computer, connected to Haasoscope, like /dev/ttyUSB0 or COM8, leave blank to detect automatically!
        self.usbport=[] # the names of the USB2 ports on your computer, connected to Haasoscope, leave blank to detect automatically!
        self.usbser=[]
        self.otherlines = []
        self.texts = []
        # self.xdata=np.arange(self.num_samples)
        # self.xdata2=np.arange(self.num_samples*2) # for oversampling
        # self.xdata4=np.arange(self.num_samples*4) # for over-oversampling
        self.ydata = []
        # ysampdatat=np.zeros(self.nsamp*len(max10adcchans)); self.ysampdata=np.reshape(ysampdatat,(len(max10adcchans),self.nsamp))
        # self.xsampdata=np.arange(self.nsamp)
        self.paused=False
        self.getone=False
        self.average=False #will average every 2 samples
        self.fallingedge=True #trigger on falling edge
        self.dogrid=True #redraw the grid
        self.chanforscreen=0 #channel to draw on the mini-display
        self.triggertimethresh=1 #samples for which the trigger must be over/under threshold
        self.dofft=False #drawing the FFT plot
        self.dousb=False #whether to use USB2 output
        self.dogetotherdata=False # whether to read other calculated data like TDC
        self.domaindrawing=True # whether to update the main window data and redraw it
        self.selectedchannel=0 #what channel some actions apply to
        self.selectedmax10channel=0 #what max10 channel is selected
        self.autorearm=False #whether to automatically rearm the trigger after each event, or wait for a signal from software
        self.dohighres=False #whether to do averaging during downsampling or not (turned on by default during startup, and off again during shutdown)
        self.useexttrig=False #whether to use the external trigger input
        self.autocalibchannel=-1 #which channel we are auto-calibrating
        self.autocalibgainac=0 #which stage of gain and acdc we are auto-calibrating
        self.recordedchannellength=250 #number of events to overlay in the 2d persist plot
        self.chtext = "Ch." #the text in the legend for each channel
        self.db = False #debugging #True #False

        self.dolockin=False # read lockin info
        self.dolockinplot=True # plot the lockin info
        self.lockinanalyzedataboard=0 # the board to analyze lockin info from
        self.debuglockin=False #debugging of lockin calculations #True #False
        self.reffreq = 0.008 #MHz of reference signal on chan 3 for lockin calculations
        self.refsinchan = 3 #the channel number of the ref input signal (for auto reffreq calculation via sin fit)

        self.xscaling=1.e0 # for the x-axis scale
        self.rollingtrigger=True #rolling auto trigger at 5 Hz
        self.dologicanalyzer=False #whether to send logic analyzer data


        #These hold the state of the IO expanders
        self.a20= int('f0',16) # oversamp (set bits 0,1 to 0 to send 0->2 and 1->3) / gain (set second char to 0 for low gain)
        self.b20= int('0f',16)  # shdn (set first char to 0 to turn on) / ac coupling (set second char to f for DC, 0 for AC)
        self.a21= int('00',16) # leds (on is 1)
        self.b21= int('00',16)# free pins

    def tellrolltrig(self,rt):
        #tell them to roll the trigger (a self-trigger each ~second), or not
        frame=[]
        if rt: frame.append(101); self.rollingtrigger=True; print("rolling trigger")
        else:  frame.append(102); self.rollingtrigger=False; print("not rolling trigger")
        self.ser.write(frame)

    def tellsamplesmax10adc(self, nsamp):
        #tell it the number of samples to use for the 1MHz internal Max10 ADC
        frame=[]
        frame.append(120)
        frame.extend(bytearray.fromhex('{:04x}'.format(nsamp)))
        self.ser.write(frame)

        if self.db: print(("Nsamp for max10 ADC is ",256*frame[1]+1*frame[2]," self.nsamp:",self.nsamp))

    def settriggerpoint(self,tp):
        #tell it the trigger point
        frame=[]
        frame.append(121)
        offset=5 #small offset due to drawing and delay
        myb=bytearray.fromhex('{:04x}'.format(tp+offset))
        frame.extend(myb)
        self.ser.write(frame)

        print(("Trigger point is",256*myb[0]+1*myb[1]-offset))

    def tellsamplessend(self, num_samples_to_send):
        #tell it the number of samples to send
        frame=[]
        frame.append(122)
        # Either 0 for all, or num_samples*pow(2,sendincrement)
        frame.extend(bytearray.fromhex('{:04x}'.format(num_samples_to_send)))
        self.ser.write(frame)

        print(("num samples is",256*frame[1]+1*frame[2]))

    def telllockinnumtoshift(self,numtoshift):
        #tell it the number of samples to shift when calculating 90deg outofphase sum for lockin
        frame=[]
        frame.append(138)
        myb=bytearray.fromhex('{:04x}'.format(numtoshift))
        frame.extend(myb)
        self.ser.write(frame)

        if self.db: print(("lockinnumtoshift is",256*myb[0]+1*myb[1]))

    def tellserialdelaytimerwait(self):
        #tell it the number of microseconds to wait between every 32 (64?) bytes of serial output (for some slow USB serial setups)
        frame=[]
        frame.append(135)
        frame.extend(bytearray.fromhex('{:04x}'.format(self.serialdelaytimerwait)))
        self.ser.write(frame)

        print(("serialdelaytimerwait is",256*frame[1]+1*frame[2]))

    def tellbytesskip(self, sendincrement):
        #tell it the number of bytes to skip after each send, log2
        frame=[]
        frame.append(123)
        frame.append(sendincrement)
        self.ser.write(frame)

        print(("123 send increment is",sendincrement))

    def setlogicanalyzer(self, dologicanalyzer):
        #tell it start/stop doing logic analyzer
        self.dologicanalyzer = dologicanalyzer
        frame=[]
        frame.append(145)
        if self.dologicanalyzer:
            frame.append(5)
        else:
            frame.append(4)
        self.ser.write(frame)
        print(("dologicanalyzer is now",self.dologicanalyzer))

    minfirmwareversion=255
    def getfirmwareversion(self, board):
        #get the firmware version of a board
        oldtime=time.time()
        frame=[]
        frame.append(30+board) #make the next board active (serial_passthrough 0)
        frame.append(147) #request the firmware version byte
        self.ser.write(frame)
        self.ser.timeout=0.1; rslt = self.ser.read(1); self.ser.timeout=self.sertimeout # reduce the serial timeout temporarily, since the old firmware versions will return nothing for command 147
        byte_array = unpack('%dB'%len(rslt),rslt)
        firmwareversion=0
        if len(byte_array)>0: firmwareversion=byte_array[0]
        print(("got firmwareversion",firmwareversion,"for board",board,"in",round((time.time()-oldtime)*1000.,2),"ms"))
        return firmwareversion # is 0 if not found (firmware version <5)

    def telltickstowait(self,ds):
        #tell it the number of clock ticks to wait, log2, between sending bytes
        frame=[]
        frame.append(125)
        frame.append(ds)
        self.ser.write(frame)
        if self.db: print(("clockbitstowait is",ds))

    def tellminidisplaychan(self,ch):
        #tell it the channel to show on the mini-display
        frame=[]
        frame.append(126)
        frame.append(ch)
        self.ser.write(frame)
        print(("chanforscreen is",ch))

    def settriggerthresh(self,tp):
        #tell it the trigger threshold
        tp=255-tp # need to flip it due to op amp
        frame=[]
        frame.append(127)
        frame.append(tp)
        self.ser.write(frame)
        print(("Trigger threshold is",tp))

    def settriggerthresh2(self,tp):
        #tell it the high trigger threshold (must be below this to trigger)
        tp=255-tp # need to flip it due to op amp
        frame=[]
        frame.append(140)
        frame.append(tp)
        self.ser.write(frame)
        print(("Trigger high threshold is",tp))

    def settriggertype(self,tp):
        #tell it the trigger type: rising edge, falling edge, either, ...
        frame=[]
        frame.append(128)
        frame.append(tp)
        self.ser.write(frame)
        if self.db: print(("Trigger type is",tp))

    def settriggertime(self,ttt):
        #tell it the trigger time over/under threshold required
        # if ttt>self.num_samples and ttt>10:
        usedownsamplefortriggertot=True
        if usedownsamplefortriggertot: ttt+=pow(2,12) #set bit [ram_width] (max) = 1
        frame=[]
        frame.append(129)
        frame.extend(bytearray.fromhex('{:04x}'.format(ttt)))
        self.ser.write(frame)
        print(("129 trigger time over/under thresh now",256*frame[1]+1*frame[2]-pow(2,12),"and usedownsamplefortriggertot is",usedownsamplefortriggertot))

    def getfirmchan(self,chan):
        theboard = HAAS_NUM_BOARD-1-int(chan/self.num_chan_per_board)
        chanonboard = chan%self.num_chan_per_board
        firmchan=theboard*self.num_chan_per_board+chanonboard
        return firmchan # the channels are numbered differently in the firmware

    def tellSPIsetup(self,what):
        time.sleep(.01) #pause to make sure other SPI writng is done
        frame=[]
        frame.append(131)
        myb=bytearray.fromhex('06 10') #default
        #SPIsenddata[14:8]=7'h08;//Common mode bias voltages
        #SPIsenddata[7:0]=8'b00000000;//off //0x00
        #SPIsenddata[7:0]=8'b11111111;//on 0.45V //0xff
        #SPIsenddata[7:0]=8'b11001100;//on 0.9V //0xcc
        #SPIsenddata[7:0]=8'b10111011;//on 1.35V //0xbb
        if what==0: myb=bytearray.fromhex('08 00') #not connected, 0.9V
        if what==1: myb=bytearray.fromhex('08 ff') #0.45V
        if what==2: myb=bytearray.fromhex('08 dd') #0.75V
        if what==3: myb=bytearray.fromhex('08 cc') #0.9V
        if what==4: myb=bytearray.fromhex('08 99') #1.05V
        if what==5: myb=bytearray.fromhex('08 aa') #1.2V
        if what==6: myb=bytearray.fromhex('08 bb') #1.35V
        #SPIsenddata[14:8]=7'h06; //Clock Divide/Data Format/Test Pattern
        #SPIsenddata[7:0]=8'b01010000;//do test pattern in offset binary // 0x50
        #SPIsenddata[7:0]=8'b00010000;//do offset binary //0x10
        if what==10: myb=bytearray.fromhex('06 50') #test pattern output
        if what==11: myb=bytearray.fromhex('06 10') #offset binary output + no clock divide
        if what==12: myb=bytearray.fromhex('06 11') #offset binary output + divide clock by 2
        if what==13: myb=bytearray.fromhex('06 12') #offset binary output + divide clock by 4
        if what==20: myb=bytearray.fromhex('04 00') #50 Ohm termination chA (default)
        if what==21: myb=bytearray.fromhex('05 00') #50 Ohm termination chB (default)
        if what==22: myb=bytearray.fromhex('04 1b') #150 Ohm termination chA
        if what==23: myb=bytearray.fromhex('05 1b') #150 Ohm termination chB
        if what==24: myb=bytearray.fromhex('04 24') #300 Ohm termination chA
        if what==25: myb=bytearray.fromhex('05 24') #300 Ohm termination chB
        if what==30: myb=bytearray.fromhex('01 02') #multiplexed, with chA first
        if what==31: myb=bytearray.fromhex('01 06') #multiplexed, with chB first
        if what==32: myb=bytearray.fromhex('01 00') # not multiplexed output
        frame.extend(myb)
        self.ser.write(frame)
        print(("tell SPI setup: 131 ",myb[0],myb[1]))
        time.sleep(.01) #pause to make sure other SPI writng is done

    # testBit() returns a nonzero result, 2**offset, if the bit at 'offset' is one.
    def testBit(self,int_type, offset):
        mask = 1 << offset
        return(int_type & mask)
    # setBit() returns an integer with the bit at 'offset' set to 1.
    def setBit(self,int_type, offset):
        mask = 1 << offset
        return(int_type | mask)
    # clearBit() returns an integer with the bit at 'offset' cleared.
    def clearBit(self,int_type, offset):
        mask = ~(1 << offset)
        return(int_type & mask)
    # toggleBit() returns an integer with the bit at 'offset' inverted, 0 -> 1 and 1 -> 0.
    def toggleBit(self,int_type, offset):
        mask = 1 << offset
        return(int_type ^ mask)

    def sendi2c(self,whattosend,board=200):
        db2=False
        time.sleep(.02)
        frame=[]
        frame.append(136)
        myb=bytearray.fromhex(whattosend)
        frame.append(len(myb)-1)
        frame.extend(myb)
        # pad with extra bytes since the command expects a total of 5 bytes (numtosend, addr, and 3 more bytes)
        for b in np.arange(4-len(myb)):
            frame.append(255)
        frame.append(board)
        self.ser.write(frame) #200 (default) will address message to all boards, otherwise only the given board ID will listen
        time.sleep(.02)
        if db2: print("sendi2c frame:",unpack('%dB' % len(frame), frame))
    def setupi2c(self):
        self.sendi2c("20 00 00") #port A on IOexp 1 are outputs
        self.sendi2c("20 01 00") #port B on IOexp 1 are outputs
        self.sendi2c("21 00 00") #port A on IOexp 2 are outputs
        self.sendi2c("20 12 "+ ('%0*x' % (2,self.a20)) ) #port A of IOexp 1
        self.sendi2c("20 13 "+ ('%0*x' % (2,self.b20)) ) #port B of IOexp 1
        self.sendi2c("21 12 "+ ('%0*x' % (2,self.a21)) ) #port A of IOexp 2
        if self.minfirmwareversion<15:
            self.sendi2c("21 01 00") #port B on IOexp 2 are outputs
            self.sendi2c("21 13 "+ ('%0*x' % (2,self.b21)) ) #port B of IOexp 2
        else:
            self.sendi2c("21 01 ff") #port B on IOexp 2 are inputs!
            self.sendi2c("21 0d ff") #port B on IOexp 2 enable pull-up resistors!
            #print "portB on IOexp2 are inputs now"
        #print "initialized all i2c ports and set to starting values"


    def shutdownadcs(self):
        self.b20= int('ff',16)  # shdn (set first char to f to turn off) / ac coupling (?)
        self.sendi2c("20 13 "+ ('%0*x' % (2,self.b20)) ) #port B of IOexp 1
        print("shut down adcs")

    def testi2c(self):
        print("test i2c")
        dotest=3 # what to test
        if dotest==0:
            # IO expander 1
            self.sendi2c("20 12 ff") #turn on all port A of IOexp 1 (12 means A, ff is which of the 8 bits to turn on)
            self.sendi2c("20 13 ff") #turn on all port B of IOexp 1 (13 means B, ff is which of the 8 bits to turn on)
            time.sleep(3)
            self.sendi2c("20 12 00") #turn off all port A of IOexp 1
            self.sendi2c("20 13 00") #turn off all port B of IOexp 1
        elif dotest==1:
            #Test the DAC
            self.setdac(0,0)
            time.sleep(3)
            self.setdac(0,1200)
        elif dotest==2:
            #toggle led 3, at 0x21 a0
            self.a21=self.toggleBit(self.a21,3); self.sendi2c("21 12 "+ ('%0*x' % (2,self.a21)) )
        elif dotest==3:
            #toggle pin E24 B7, at 0x21 b7
            self.b21=self.toggleBit(self.b21,7); self.sendi2c("21 13 "+ ('%0*x' % (2,self.b21)) )

    def toggledousb(self):#toggle whether to read over FT232H USB or not
        if len(self.usbser)==0:
            self.dousb=False
            print("usb2 connection not available")
        else:
            self.dousb = not self.dousb
            frame=[]
            frame.append(137)
            self.ser.write(frame)
            print(("dousb toggled to",self.dousb))
            if self.dousb: print(("rate theoretically",round(4000000./(self.num_bytes*HAAS_NUM_BOARD+len(max10adcchans)*self.nsamp),2),"Hz over USB2"))
            self.telltickstowait()

    def togglehighres(self):#toggle whether to do highres averaging during downsampling or not
            frame=[]
            frame.append(143)
            self.ser.write(frame)
            self.dohighres = not self.dohighres
            print(("143 do highres is",self.dohighres))

    def toggleuseexttrig(self):#toggle whether to use the external trigger input or not
            frame=[]
            frame.append(144)
            self.ser.write(frame)
            self.useexttrig = not self.useexttrig
            print(("useexttrig is",self.useexttrig))

    def settriggerchan(self,firmchan):
        #tell it to trigger or not trigger on a given channel
        frame=[]
        frame.append(130)
        frame.append(firmchan)
        self.ser.write(frame)

    def toggleautorearm(self):
        frame=[]
        #tell it to toggle the auto rearm of the tirgger after readout
        frame.append(139)
        # prime the trigger one last time
        frame.append(100)
        self.ser.write(frame)
        self.autorearm = not self.autorearm
        print(("Trigger auto rearm now",self.autorearm))
        if self.db: print((time.time()-self.oldtime,"priming trigger"))

    def getID(self, n):
        debug3=True
        frame=[]
        frame.append(30+n)
        frame.append(142)
        self.ser.write(frame)
        num_other_bytes = 8
        rslt = self.ser.read(num_other_bytes)
        return rslt

    def togglesupergainchan(self,chan):
        if len(plt.get_fignums())>0: origline,legline,channum = self.lined[chan]
        if self.supergain[chan]==1:
            self.supergain[chan]=0 #x100 super gain on!
            if len(plt.get_fignums())>0:
                if self.gain[chan]==1:
                    origline.set_label(self.chtext+str(chan)+" x100")
                    self.leg.get_texts()[chan].set_text(self.chtext+str(chan)+" x100")
                else:
                    origline.set_label(self.chtext+str(chan)+" x1000")
                    self.leg.get_texts()[chan].set_text(self.chtext+str(chan)+" x1000")
        else:
            self.supergain[chan]=1 #normal gain
            if len(plt.get_fignums())>0:
                if self.gain[chan]==1:
                    origline.set_label(self.chtext+str(chan))
                    self.leg.get_texts()[chan].set_text(self.chtext+str(chan))
                else:
                    origline.set_label(self.chtext+str(chan)+" x10")
                    self.leg.get_texts()[chan].set_text(self.chtext+str(chan)+" x10")
        self.selectedchannel=chan
        self.setdacvalue()
        if len(plt.get_fignums())>0: self.figure.canvas.draw()
        print(("Supergain switched for channel",chan,"to",self.supergain[chan]))

    def tellswitchgain(self,chan):
        #tell it to switch the gain of a channel
        frame=[]
        frame.append(134)
        firmchan=self.getfirmchan(chan)
        frame.append(firmchan)
        self.ser.write(frame)
        if len(plt.get_fignums())>0: origline,legline,channum = self.lined[chan]
        if self.gain[chan]==1:
            self.gain[chan]=0 # x10 gain on!
            if len(plt.get_fignums())>0:
                if self.supergain[chan]==1:
                    origline.set_label(self.chtext+str(chan)+" x10")
                    self.leg.get_texts()[chan].set_text(self.chtext+str(chan)+" x10")
                else:
                    origline.set_label(self.chtext+str(chan)+" x1000")
                    self.leg.get_texts()[chan].set_text(self.chtext+str(chan)+" x1000")
        else:
            self.gain[chan]=1 #low gain
            if len(plt.get_fignums())>0:
                if self.supergain[chan]==1:
                    origline.set_label(self.chtext+str(chan))
                    self.leg.get_texts()[chan].set_text(self.chtext+str(chan))
                else:
                    origline.set_label(self.chtext+str(chan)+" x100")
                    self.leg.get_texts()[chan].set_text(self.chtext+str(chan)+" x100")
        self.selectedchannel=chan # needed for setdacvalue
        self.setdacvalue()
        if len(plt.get_fignums())>0: self.figure.canvas.draw()
        print(("Gain switched for channel",chan,"to",self.gain[chan]))

    def oversamp(self,chan):
        #tell it to toggle oversampling for this channel
        chanonboard = chan%self.num_chan_per_board
        if chanonboard>1: return
        if chanonboard==1 and self.dooversample[chan] and self.dooversample[chan-1]==9: print(("first disable over-oversampling on channel",chan-1)); return
        self.togglechannel(chan+2,True)
        self.dooversample[chan] = not self.dooversample[chan];
        print(("oversampling is now",self.dooversample[chan],"for channel",chan))
        if self.dooversample[chan] and self.downsample>0: self.telldownsample(0) # must be in max sampling mode for oversampling to make sense
        frame=[]
        frame.append(141)
        firmchan=self.getfirmchan(chan)
        frame.append(firmchan)
        self.ser.write(frame)
        self.drawtext()
        self.figure.canvas.draw()

    def overoversamp(self):
        if self.selectedchannel%4: print("over-oversampling only for channel 0 of a board!")
        elif self.dooversample[self.selectedchannel]==0 or self.dooversample[self.selectedchannel+1]==0: print("for over-oversampling, first do oversampling on channels 0 and 1 of the board")
        elif self.dooversample[self.selectedchannel]==1: self.dooversample[self.selectedchannel]=9; self.togglechannel(self.selectedchannel+1,True); print("over-oversampling")
        elif self.dooversample[self.selectedchannel]==9: self.dooversample[self.selectedchannel]=1; print("no more over-oversampling")

    def resetchans(self):
        for chan in np.arange(HAAS_NUM_BOARD*self.num_chan_per_board):
            if self.gain[chan]==0:
                self.tellswitchgain(chan) # set all gains back to low gain
            # if  self.trigsactive[chan]==0:
                # TODO fix this
                # self.settriggerchan(chan) # set all trigger channels back to active
            if self.dooversample[chan]:
                self.oversamp(chan) # set all channels back to no oversampling

    def setbacktoserialreadout(self):
        if self.dousb:
            frame=[]
            frame.append(137)
            self.ser.write(frame)
            self.dousb=False
            print(("dousb set back to",self.dousb))

    def telldownsample(self,ds):
        #tell it the amount to downsample, log2... so 0 (none), 1(factor 2), 2(factor 4), etc.
        frame=[]
        frame.append(124)
        frame.append(ds)
        self.ser.write(frame)


    def adjustvertical(self,up,amount=10):
        if self.keyShift: amount*=5
        if self.keyControl: amount/=10
        #print "amount is",amount
        if self.gain[self.selectedchannel]: amount*=10 #low gain
        if self.supergain[self.selectedchannel]==0 and self.acdc[self.selectedchannel]: amount=max(1,amount/10) #super gain
        #print "now amount is",amount
        if up:
             self.chanlevel[self.selectedchannel] = self.chanlevel[self.selectedchannel] - amount
        else:
             self.chanlevel[self.selectedchannel] = self.chanlevel[self.selectedchannel] + amount
        self.rememberdacvalue()
        self.setdacvalue()

    def rememberdacvalue(self):
        #remember current dac level for the future to the right daclevel, depending on other settings
        if self.gain[self.selectedchannel]: # low gain
            if self.supergain[self.selectedchannel]:
                if self.acdc[self.selectedchannel]: self.lowdaclevel[self.selectedchannel]=self.chanlevel[self.selectedchannel]
                else: self.lowdaclevelac[self.selectedchannel]=self.chanlevel[self.selectedchannel]
            else: #supergain
                if self.acdc[self.selectedchannel]: self.lowdaclevelsuper[self.selectedchannel]=self.chanlevel[self.selectedchannel] #dc super gain
                else: self.lowdaclevelsuperac[self.selectedchannel]=self.chanlevel[self.selectedchannel]
        else: # high gain
            if self.supergain[self.selectedchannel]:
                if self.acdc[self.selectedchannel]: self.highdaclevel[self.selectedchannel]=self.chanlevel[self.selectedchannel]
                else: self.highdaclevelac[self.selectedchannel]=self.chanlevel[self.selectedchannel]
            else: #supergain
                if self.acdc[self.selectedchannel]: self.highdaclevelsuper[self.selectedchannel]=self.chanlevel[self.selectedchannel] #dc super gain
                else: self.highdaclevelsuperac[self.selectedchannel]=self.chanlevel[self.selectedchannel]


    def setacdc(self):
        chan=self.selectedchannel
        theboard = HAAS_NUM_BOARD-1-int(chan/self.num_chan_per_board)
        chanonboard = chan%self.num_chan_per_board
        print(("toggling acdc for chan",chan,"which is chan",chanonboard,"on board",theboard))
        self.acdc[int(chan)] = not self.acdc[int(chan)]
        self.b20= int('00',16)  # shdn (set first char to 0 to turn on) / ac coupling (set second char to f for DC, 0 for AC)
        for c in range(0,4):
            realchan = (HAAS_NUM_BOARD-1-theboard)*self.num_chan_per_board+c
            if self.acdc[int(realchan)]:
                self.b20 = self.toggleBit(self.b20,int(c)) # 1 is dc, 0 is ac
                if self.db: print(("toggling bit",c,"for chan",realchan))
        self.sendi2c("20 13 "+ ('%0*x' % (2,self.b20)),  theboard) #port B of IOexp 1, only for the selected board
        self.setdacvalue()
        self.drawtext()


    def storecalib(self):
        cwd = os.getcwd()
        print(("current directory is",cwd))
        for board in range(0,HAAS_NUM_BOARD):
            self.storecalibforboard(board)
    def storecalibforboard(self,board):
        sc = board*self.num_chan_per_board
        print(("storing calibrations for board",board,", channels",sc,"-",sc+4))
        c = dict(
            boardID=self.uniqueID[board],
            lowdaclevels=self.lowdaclevel[sc : sc+4].tolist(),
            highdaclevels=self.highdaclevel[sc : sc+4].tolist(),
            lowdaclevelssuper=self.lowdaclevelsuper[sc : sc+4].tolist(),
            highdaclevelssuper=self.highdaclevelsuper[sc : sc+4].tolist(),
            lowdaclevelsac=self.lowdaclevelac[sc : sc+4].tolist(),
            highdaclevelsac=self.highdaclevelac[sc : sc+4].tolist(),
            lowdaclevelssuperac=self.lowdaclevelsuperac[sc : sc+4].tolist(),
            highdaclevelssuperac=self.highdaclevelsuperac[sc : sc+4].tolist(),
            firmwareversion=self.minfirmwareversion
            )
        #print json.dumps(c,indent=4)
        fname = "calib/calib_"+self.uniqueID[board]+".json.txt"
        json.dump(c,open(fname,'w'),indent=4)
        print(("wrote",fname))




    #called when sampling is changed, to reset some things
    def prepareforsamplechange(self):
        self.recordedchannel=[]
        if self.doxyplot:
            plt.close(self.figxy)
        if self.recorddata:
            plt.close(self.fig2d)

    #will grab the next keys as input
    keyResample=False
    keysettriggertime=False
    keySPI=False
    keyi2c=False
    keyLevel=False
    keyShift=False
    keyAlt=False
    keyControl=False





    def fittosin(self,xdatanew, ydatanew, chan):
        res = self.fit_sin(xdatanew, ydatanew)
        phase=res['phase']*180./np.pi
        if res['amp']<0.: phase+=180.
        print(("Chan:",chan, "cov=",res['maxcov'], "amp=",abs(res['amp']), "phase=",phase, "offset=", res['offset'], res['freq']*1000000./self.xscaling,'kHz'))
        if res['maxcov']<1e-4:
            if self.oldchanphase>=0.:
                diff=phase-self.oldchanphase
                if diff<0: diff+=360
                print(("phase diff=",diff))
            self.oldchanphase=phase
            return res['freq']
        else: print("sin fit failed!"); return 0;

    #For finding the frequency of a reference sin wave signal, for lockin calculations
    def fit_sin(self,tt, yy):
        '''Fit sin to the input time sequence, and return fitting parameters "amp", "omega", "phase", "offset", "freq", "period" and "fitfunc"'''
        tt = np.array(tt)
        yy = np.array(yy)
        ff = np.fft.fftfreq(len(tt), (tt[1]-tt[0]))   # assume uniform spacing
        Fyy = abs(np.fft.fft(yy))
        guess_freq = abs(ff[np.argmax(Fyy[1:])+1])   # excluding the zero frequency "peak", which is related to offset
        guess_amp = np.std(yy) * 2.**0.5
        guess_offset = np.mean(yy)
        guess = np.array([guess_amp, 2.*np.pi*guess_freq, 0., guess_offset])

        def sinfunc(t, A, w, p, c):  return A * np.sin(w*t + p) + c
        popt, pcov = scipy.optimize.curve_fit(sinfunc, tt, yy, p0=guess)
        A, w, p, c = popt
        f = w/(2.*np.pi)
        fitfunc = lambda t: A * np.sin(w*t + p) + c
        return {"amp": A, "omega": w, "phase": p, "offset": c, "freq": f, "period": 1./f, "fitfunc": fitfunc, "maxcov": np.max(pcov), "rawres": (guess,popt,pcov)}

    def autocalibrate(self,thechan,ydatanew):
        self.selectedchannel=thechan
        avg = np.average(ydatanew)
        #print avg
        gotonext=False
        tol = 1.0
        tol2 = 0.25
        if self.supergain[self.selectedchannel] or self.gain[self.selectedchannel]: # normal gain or low gain
            tol = 0.3
            tol2 = 0.02
        if avg>0+tol:
            self.adjustvertical(False,10)
        elif avg<0-tol:
            self.adjustvertical(True,10)
        elif avg>0+tol2:
            self.adjustvertical(False,1)
        elif avg<0-tol2:
            self.adjustvertical(True,1)
        else: gotonext=True
        if self.chanlevel[self.selectedchannel]==0: gotonext=True
        if gotonext:
            #go to the next channel, unless we're at the end of all channels
            self.autocalibchannel=self.autocalibchannel+1
            if self.autocalibchannel==self.num_chan_per_board*HAAS_NUM_BOARD:
                self.autocalibgainac=self.autocalibgainac+1
                if self.autocalibgainac==1:
                    self.autocalibchannel=0
                    for chan in range(self.num_chan_per_board*HAAS_NUM_BOARD):
                        self.selectedchannel=chan
                        self.setacdc()
                elif self.autocalibgainac==2:
                    self.autocalibchannel=0
                    for chan in range(self.num_chan_per_board*HAAS_NUM_BOARD):
                        self.selectedchannel=chan
                        self.tellswitchgain(chan)
                elif self.autocalibgainac==3:
                    self.autocalibchannel=0
                    for chan in range(self.num_chan_per_board*HAAS_NUM_BOARD):
                        self.selectedchannel=chan
                        self.setacdc()
                else:
                    self.autocalibchannel=-1 #all done
                    self.autocalibgainac=0
                    for chan in range(self.num_chan_per_board*HAAS_NUM_BOARD):
                        self.selectedchannel=chan
                        self.tellswitchgain(chan)
                        if self.minfirmwareversion<15: self.togglesupergainchan(chan)
                    print("done with autocalibration \a") # beep!




    def handle_main_close(self,evt):
        plt.close('all')
    def handle_xy_close(self,evt):
        self.drawnxy=False
        self.doxyplot=False
    def handle_persist_close(self,evt):
        self.drawn2d=False
        self.recorddata=False
    def handle_fft_close(self,evt):
        self.dofft=False
        self.fftdrawn=False
    def handle_lockin_close(self,evt):
        self.dolockinplot=False
        self.lockindrawn=False


    def getotherdata(self,board):
        debug3=True
        frame=[]
        frame.append(132)
        self.ser.write(frame)
        num_other_bytes = 1
        rslt = self.ser.read(num_other_bytes)
        if len(rslt)==num_other_bytes:
            byte_array = unpack('%dB'%len(rslt),rslt) #Convert serial data to array of numbers
            if debug3: print(("\n delay counter data",byte_array[0],"from board",board))
            #if debug3: print "other data",bin(byte_array[0])
        else: print(("getotherdata asked for",num_other_bytes,"delay counter bytes and got",len(rslt)))
        frame=[]
        frame.append(133)
        self.ser.write(frame)
        num_other_bytes = 1
        rslt = self.ser.read(num_other_bytes)
        if len(rslt)==num_other_bytes:
            byte_array = unpack('%dB'%len(rslt),rslt) #Convert serial data to array of numbers
            if debug3: print((" carry counter data",byte_array[0],"from board",board))
            #if debug3: print "other data",bin(byte_array[0])
        else: print(("getotherdata asked for",num_other_bytes,"carry counter bytes and got",len(rslt)))

    def to_int(self,n): # takes a 32 bit decimal number in two's complement and converts to a binary and then to a signed integer
        bin = '{0:32b}'.format(n)
        x = int(bin, 2)
        if bin[0] == '1': # "sign bit", big-endian
            x -= 2**len(bin)
        return x

    def lockinanalyzedata(self,board):
        if self.lockinanalyzedataboard!=board: return False
        y2 = self.ydata[2] # channel 2 signal
        y3 = self.ydata[3] # channel 3 signal
        meany2=np.sum(y2)/self.num_samples
        meany3=np.sum(y3)/self.num_samples
        y2 = y2-meany2
        y3 = y3-meany3
        y3shifted = np.roll(y3,self.numtoshift)
        res1=y2*y3
        res2=y2*y3shifted
        r1m=np.sum(res1)
        r2m=np.sum(res2)
        #print r1m,r2m
        r1m/=4096.
        r2m/=4096.
        ampl = np.sqrt(r1m*r1m+r2m*r2m)
        phase = 180.*np.arctan2(r2m,r1m)/np.pi
        if self.debuglockin:
            print(("no window:  ",r1m.round(2), r2m.round(2), self.numtoshift, meany2.round(1),meany3.round(1)))
            print((ampl.round(2), phase.round(2), "<------ offline no window"))
        lowerwindowedge = self.numtoshift+1
        upperwindowedge = self.num_samples-self.numtoshift
        if self.debuglockin:
            self.ydata[0]= y3shifted+127 # to see on screen, alter self.ydata here
            self.ydata[0][0:lowerwindowedge] = np.zeros((lowerwindowedge,), dtype=np.int)+127
            self.ydata[0][upperwindowedge:self.num_samples] = np.zeros((self.num_samples-upperwindowedge,), dtype=np.int)+127
        y2window = y2[lowerwindowedge:upperwindowedge]
        y3window = y3[lowerwindowedge:upperwindowedge]
        y3shiftedwindow = y3shifted[lowerwindowedge:upperwindowedge]
        res1window=y2window*y3window
        res2window=y2window*y3shiftedwindow
        r1mwindow=np.sum(res1window)
        r2mwindow=np.sum(res2window)
        if self.debuglockin: print(("window:",r1mwindow,r2mwindow))
        r1mwindow/=4096.
        r2mwindow/=4096.
        amplwindow = np.sqrt(r1mwindow*r1mwindow+r2mwindow*r2mwindow)
        phasewindow = 180.*np.arctan2(r2mwindow,r1mwindow)/np.pi
        if self.debuglockin:
            print(("with window:",r1mwindow.round(2), r2mwindow.round(2), self.numtoshift, meany2.round(1),meany3.round(1)))
            print((amplwindow.round(2), phasewindow.round(2), "<------ offline with window"))
        meany2float=np.mean(self.ydata[2])
        meany3float=np.mean(self.ydata[3])
        y3shiftedfloat = np.roll(self.ydata[3]-meany3float,self.numtoshift)
        y2windowfloat = self.ydata[2][lowerwindowedge:upperwindowedge]-meany2float
        y3windowfloat = self.ydata[3][lowerwindowedge:upperwindowedge]-meany3float
        y3shiftedwindowfloat = y3shiftedfloat[lowerwindowedge:upperwindowedge]
        res1windowfloat=y2windowfloat*y3windowfloat
        res2windowfloat=y2windowfloat*y3shiftedwindowfloat
        r1mwindowfloat=np.sum(res1windowfloat)
        r2mwindowfloat=np.sum(res2windowfloat)
        #print "windowfloat:",r1mwindowfloat,r2mwindowfloat
        r1mwindowfloat/=4096.
        r2mwindowfloat/=4096.
        amplwindowfloat = np.sqrt(r1mwindowfloat*r1mwindowfloat+r2mwindowfloat*r2mwindowfloat)
        phasewindowfloat = 180.*np.arctan2(r2mwindowfloat,r1mwindowfloat)/np.pi
        if self.debuglockin:
            print(("float with window:",r1mwindowfloat.round(2), r2mwindowfloat.round(2), self.numtoshift, meany2.round(1),meany3.round(1)))
            print((amplwindowfloat.round(2), phasewindowfloat.round(2), "<------ offline with window float\n"))
        self.lockinampo = amplwindowfloat
        self.lockinphaseo = phasewindowfloat

    def getlockindata(self,board):
            rslt = self.ser.read(16)
            byte_array = unpack('%dB'%len(rslt),rslt) #Convert serial data to array of numbers
            if len(rslt)==16:
                r1_fpga = (256*256*256*byte_array[3]+256*256*byte_array[2]+256*byte_array[1]+byte_array[0])
                r2_fpga =  (256*256*256*byte_array[7]+256*256*byte_array[6]+256*byte_array[5]+byte_array[4])
                r1_fpga = self.to_int(r1_fpga)
                r2_fpga = self.to_int(r2_fpga)
                mean_c2 = (256*256*256*byte_array[11]+256*256*byte_array[10]+256*byte_array[9]+byte_array[8])
                mean_c3 = (256*256*256*byte_array[15]+256*256*byte_array[14]+256*byte_array[13]+byte_array[12])
                if self.debuglockin:
                    print((byte_array[0:4], r1_fpga))
                    print((byte_array[4:8], r2_fpga))
                    print((byte_array[8:12], mean_c2))
                    print((byte_array[12:16], mean_c3))
                r1_fpga/=4096.
                r2_fpga/=4096.
                ampl_fpga = np.sqrt(r1_fpga*r1_fpga+r2_fpga*r2_fpga)
                phase_fpga = 180.*np.arctan2(r2_fpga,r1_fpga)/np.pi
                if self.lockinanalyzedataboard==board:
                    self.lockinamp = ampl_fpga
                    self.lockinphase = phase_fpga
                if False:
                    print((ampl_fpga.round(2), phase_fpga.round(2), "<------ fpga "))
            else: print(("getdata asked for",16,"lockin bytes and got",len(rslt),"from board",board))

    usbsermap=[]
    def makeusbsermap(self): # figure out which board is connected to which USB 2 connection
        self.usbsermap=np.zeros(HAAS_NUM_BOARD, dtype=int)
        if len(self.usbser)<HAAS_NUM_BOARD:
            print("Not a USB2 connection for each board!")
            return False
        if len(self.usbser)>1:
            for usb in np.arange(HAAS_NUM_BOARD): self.usbser[usb].timeout=.5 # lower the timeout on the connections, temporarily
            foundusbs=[]
            for bn in np.arange(HAAS_NUM_BOARD):
                frame=[]
                frame.append(100)
                frame.append(10+bn)
                self.ser.write(frame)
                for usb in np.arange(len(self.usbser)):
                    if not usb in foundusbs: # it's not already known that this usb connection is assigned to a board
                        rslt = self.usbser[usb].read(self.num_bytes) # try to get data from the board
                        if len(rslt)==self.num_bytes:
                            #print "   got the right nbytes for board",bn,"from usb",usb
                            self.usbsermap[bn]=usb
                            foundusbs.append(usb) # remember that we already have figured out which board this usb connection is for, so we don't bother trying again for another board
                            break # already found which board this usb connection is used for, so bail out
                        #else: print "   got the wrong nbytes for board",bn,"from usb",usb
                    #else: print "   already know what usb",usb,"is for"
            for usb in np.arange(HAAS_NUM_BOARD): self.usbser[usb].timeout=self.sertimeout # put back the timeout on the connections
        print(("usbsermap is",self.usbsermap))
        return True

    timedout = False
    def getdata(self,board):
        frame=[]
        frame.append(10+board)
        self.ser.write(frame)
        if self.db: print((time.time()-self.oldtime,"asked for data from board",board))
        if self.dolockin: self.getlockindata(board)
        if self.dousb:
            #try:
            rslt = self.usbser[self.usbsermap[board]].read(self.num_bytes)
                #usbser.flushInput() #just in case
        #except serial.SerialException: pass
        else:
            rslt = self.ser.read(self.num_bytes)
            #ser.flushInput() #just in case
        if self.db: print((time.time()-self.oldtime,"getdata wanted",self.num_bytes,"bytes and got",len(rslt),"from board",board))
        byte_array = unpack('%dB'%len(rslt),rslt) #Convert serial data to array of numbers
        if len(rslt)==self.num_bytes:
            self.timedout = False
            db2=False #True
            if db2: print((byte_array[1:11]))
            self.ydata=np.reshape(byte_array,(self.num_chan_per_board,self.num_samples))
            # if self.dooversample[self.num_chan_per_board*(HAAS_NUM_BOARD-board-1)]: self.oversample(0,2)
            # if self.dooversample[self.num_chan_per_board*(HAAS_NUM_BOARD-board-1)+1]: self.oversample(1,3)
            # if self.dooversample[self.num_chan_per_board*(HAAS_NUM_BOARD-board-1)]==9: self.overoversample(0,1)
            if self.average:
                for c in np.arange(self.num_chan_per_board):
                    for i in np.arange(self.num_samples/2):
                        val=(self.ydata[c][2*i]+self.ydata[c][2*i+1])/2
                        self.ydata[c][2*i]=val; self.ydata[c][2*i+1]=val;
        else:
            self.timedout = True
            if not self.db and self.rollingtrigger: print(("getdata asked for",self.num_bytes,"bytes and got",len(rslt),"from board",board))
            if len(rslt)>0 and self.rollingtrigger: print((byte_array[0:10]))
        if self.dologicanalyzer:
            #get extra logic analyzer data, if needed
            logicbytes=self.num_bytes/4
            if self.dousb:
                #try:
                rslt = self.usbser[self.usbsermap[board]].read(logicbytes)
                    #usbser.flushInput() #just in case
            #except serial.SerialException: pass
            else:
                rslt = self.ser.read(logicbytes)
                #ser.flushInput() #just in case
            if self.db: print((time.time()-self.oldtime,"getdata wanted",logicbytes,"logic bytes and got",len(rslt),"from board",board))
            byte_array = unpack('%dB'%len(rslt),rslt) #Convert serial data to array of numbers
            if len(rslt)==logicbytes:
                db2=False #True
                if db2: print((byte_array[1:11]))
                self.ydatalogic=np.reshape(byte_array,(1,self.num_samples))
            else:
                if not self.db and self.rollingtrigger: print(("getdata asked for",self.num_bytes,"logic bytes and got",len(rslt),"from board",board))
                if len(rslt)>0 and self.rollingtrigger: print((byte_array[0:10]))

    def oversample(self,c1,c2):
        tempc1=self.ydata[c1]
        tempc2=self.ydata[c2]
        adjustmeanandrms=True
        if adjustmeanandrms:
            mean_c1 = np.mean(tempc1)
            rms_c1 = np.sqrt(np.mean((tempc1-mean_c1)**2))
            mean_c2 = np.mean(tempc2)
            rms_c2 = np.sqrt(np.mean((tempc2-mean_c2)**2))
            meanmean=(mean_c1+mean_c2)/2.
            meanrms=(rms_c1+rms_c2)/2.
            tempc1=meanrms*(tempc1-mean_c1)/rms_c1 + meanmean
            tempc2=meanrms*(tempc2-mean_c2)/rms_c2 + meanmean
            #print mean_c1, mean_c2, rms_c1, rms_c2
        ns=self.num_samples
        mergedsamps=np.empty(ns*2)
        mergedsamps[0:ns*2:2]=tempc1 # a little tricky which is 0 and which is 1 (i.e. which is sampled first!)
        mergedsamps[1:ns*2:2]=tempc2
        self.ydata[c1]=mergedsamps[0:ns]
        self.ydata[c2]=mergedsamps[ns:ns*2]

    def overoversample(self,c1,c2):
        tempc1=np.concatenate([self.ydata[c1],self.ydata[c1+2]])
        tempc2=np.concatenate([self.ydata[c2],self.ydata[c2+2]])
        adjustmeanandrms=True
        if adjustmeanandrms:
            mean_c1 = np.mean(tempc1)
            rms_c1 = np.sqrt(np.mean((tempc1-mean_c1)**2))
            mean_c2 = np.mean(tempc2)
            rms_c2 = np.sqrt(np.mean((tempc2-mean_c2)**2))
            meanmean=(mean_c1+mean_c2)/2.
            meanrms=(rms_c1+rms_c2)/2.
            tempc1=meanrms*(tempc1-mean_c1)/rms_c1 + meanmean
            tempc2=meanrms*(tempc2-mean_c2)/rms_c2 + meanmean
            #print mean_c1, mean_c2, rms_c1, rms_c2
        ns=2*self.num_samples
        mergedsamps=np.empty(ns*2)
        mergedsamps[0:ns*2:2]=tempc1 # a little tricky which is 0 and which is 1 (i.e. which is sampled first!)
        mergedsamps[1:ns*2:2]=tempc2
        self.ydata[c1]=mergedsamps[0:ns/2]
        self.ydata[c2]=mergedsamps[ns/2:ns]
        self.ydata[c1+2]=mergedsamps[ns:3*ns/2]
        self.ydata[c2+2]=mergedsamps[3*ns/2:ns*2]

    def getmax10adc(self,bn):
        chansthisboard = [(x,y) for (x,y) in max10adcchans if x==bn]
        if self.db: print((time.time()-self.oldtime,"getting",chansthisboard))
        for chans in chansthisboard:
            chan=chans[1]
            #chan: 110=ain1, 111=pin6, ..., 118=pin14, 119=temp
            frame=[]
            frame.append(chan)
            self.ser.write(frame)
            if self.db: print((time.time()-self.oldtime,"getting max10adc chan",chan,"for bn",bn))
            rslt = self.ser.read(self.nsamp*2) #read N bytes (2 per sample)
            if self.db: print((time.time()-self.oldtime,"getmax10adc got bytes:",len(rslt)))
            if len(rslt)!=(self.nsamp*2):
                print((time.time()-self.oldtime,"getmax10adc got bytes:",len(rslt),"for board",bn,"and chan",chan))
                return
            byte_array = unpack('%dB'%len(rslt),rslt) #Convert serial data to array of numbers
            db2=False #True #False
            self.ysampdata[self.max10adcchan-1]=np.add(np.multiply(256,byte_array[1:2*self.nsamp:2]),byte_array[0:2*self.nsamp:2])
            self.ysampdata[self.max10adcchan-1]/=16
            if db2:
                for samp in np.arange(10):
                    code=256*byte_array[1+2*samp]+byte_array[2*samp]
                    self.ysampdata[self.max10adcchan-1][samp]=code/16
                    if chan==119:
                        temp=-3.056e-4*code*code+1.763*code-2325.049
                        print((samp,chan,code,round(temp,1),"C",round(temp*1.8+32,1),"F"))
                    else: print((samp,chan,code,round( (3.3*code)/pow(2,12) ,4),"V"))
            # TODO: Add drawing the plots.
            # self.on_running(self.ysampdata[self.max10adcchan-1], -self.max10adcchan)
            self.max10adcchan+=1

    oldtime=time.time()
    oldtime2=time.time()
    def getchannels(self):
        if not self.autorearm:
            if self.db: print((time.time()-self.oldtime,"priming trigger"))
            frame=[]
            frame.append(100)
            self.ser.write(frame)
        self.max10adcchan=1
        for bn in np.arange(HAAS_NUM_BOARD):
            if self.db: print((time.time()-self.oldtime,"getting board",bn))
            self.getdata(bn) #this sets all boards before this board into serial passthrough mode, so this and following calls for data will go to this board and then travel back over serial
            self.getmax10adc(bn) # get data from 1 MHz Max10 ADC channels
            if self.dogetotherdata: self.getotherdata(bn) # get other data, like TDC info, or other bytes
            if self.dofft: self.plot_fft(bn) #do the FFT plot
            if self.dolockin and self.debuglockin:
                if sendincrement==0: self.lockinanalyzedata(bn)
                else: print("you need to set sendincrement = 0 first before debugging lockin info"); return False
            if self.dolockin and self.dolockinplot: self.plot_lockin()
            msg = mq.Message({
                'id': 1,
                'ydata': self.ydata,
                'bn': bn
                })
            self.mq_publisher.publish(msg)
            # self.on_running(self.ydata, bn) #update data in main window
            if self.db: print((time.time()-self.oldtime,"done with board",bn))
        if self.domaindrawing and self.domeasure:
            thetime=time.time()
            elapsedtime=thetime-self.oldtime
            if elapsedtime>1.0:
                msg = mq.Message({
                    'id': 2
                    })
                self.mq_publisher.publish(msg)
                # self.drawtext() #redraws the measurements
                self.oldtime=thetime
        if self.minfirmwareversion>=15: #v9.0 and up
            thetime2=time.time()
            elapsedtime=thetime2-self.oldtime2
            if elapsedtime>1.0:
                if not self.havereadswitchdata: self.switchpos = [0] * HAAS_NUM_BOARD
                for b in range(HAAS_NUM_BOARD): self.getswitchdata(b) #gets the dpdt switch positions
                self.havereadswitchdata=True
                self.oldtime2=thetime2
        return True

    #get the positions of the dpdt switches from IO expander 2B, and then take action (v9.0 and up!)
    havereadswitchdata=False
    def getswitchdata(self,board):
        #for i in range(2): #twice because the first time just reads it into the board's fpga
            frame=[]
            frame.append(30+board)
            frame.append(146)
            frame.append(33)
            frame.append(board)
            self.ser.write(frame)
            rslt = self.ser.read(1)
            if len(rslt)>0:# and i==1:
                byte_array = unpack('%dB'%len(rslt),rslt)
                #print "i2c data from board",board,"IO 2B",byte_array[0]
                newswitchpos=byte_array[0]
                if newswitchpos!=self.switchpos[board] or not self.havereadswitchdata:
                    for b in range(8):
                        if self.testBit(newswitchpos,b) != self.testBit(self.switchpos[board],b) or not self.havereadswitchdata:
                            #print "switch",b,"is now",self.testBit(newswitchpos,b)
                            #switch 0-3 is 50/1M Ohm termination on channels 0-3, on is 1M, off is 50
                            #switch 4-7 is super/normal gain on channels 0-3, on is super, off is normal
                            if b>=4:
                                thechan=b-4+(HAAS_NUM_BOARD-board-1)*self.num_chan_per_board
                                if self.supergain[thechan] and self.testBit(newswitchpos,b)>0:
                                    self.togglesupergainchan(thechan)
                                if not self.supergain[thechan] and not self.testBit(newswitchpos,b)>0:
                                    self.togglesupergainchan(thechan)
                    self.switchpos[board] = newswitchpos

    #initialization
    def init(self):
            frame=[]
            frame.append(0)
            frame.append(20+(HAAS_NUM_BOARD-1))
            self.ser.write(frame)
            for b in range(HAAS_NUM_BOARD):
                firmwareversion = self.getfirmwareversion(b)
                if firmwareversion<self.minfirmwareversion: self.minfirmwareversion=firmwareversion
            print(("minimum firmwareversion of all boards is",self.minfirmwareversion))
            self.maxdownsample=15 # slowest I can run
            if self.minfirmwareversion>=5: #updated firmware
                self.maxdownsample=15 +(12-ram_width) # slowest I can run (can add 12-ram_width when using newer firmware)
            # self.tellbytesskip()
            # self.telldownsample(self.downsample)
            self.togglehighres()
            self.settriggertime(self.triggertimethresh)
            self.tellserialdelaytimerwait()
            self.tellSPIsetup(0) #0.9V CM but not connected
            self.tellSPIsetup(11) #offset binary output
            self.tellSPIsetup(24) #300 Ohm termination ChA
            self.tellSPIsetup(25) #300 Ohm termination ChB
            #self.tellSPIsetup(30) # multiplexed output
            self.tellSPIsetup(32) # non-multiplexed output (less noise)
            self.setupi2c() # sets all ports to be outputs
            self.toggledousb() # switch to USB2 connection for readout of events, if available
            if self.dousb:
                if not self.makeusbsermap(): return False # figure out which usb connection has which board's data
            # self.getIDs() # get the unique ID of each board, for calibration etc.
            # self.readcalib() # get the calibrated DAC values for each board; if it fails then use defaults
            self.domeasure=self.domaindrawing #by default we will calculate measurements if we are drawing
            return True

    #cleanup
    def cleanup(self):
        try:
            self.setbacktoserialreadout()
            self.resetchans()
            if self.autorearm: self.toggleautorearm()
            if self.dohighres: self.togglehighres()
            if self.useexttrig: self.toggleuseexttrig()
            if self.dologicanalyzer: self.setlogicanalyzer(False)
            if self.serport!="" and hasattr(self,'ser'):
                self.shutdownadcs()
                for p in self.usbser: p.close()
                self.ser.close()
        except SerialException:
            print("failed to talk to board when cleaning up!")
        plt.close()
        print("bye bye!")

    #For setting up serial and USB connections
    def setup_connections(self):
        adjustedbrate=1./(1./self.brate+2.*self.serialdelaytimerwait*1.e-6/(32.*11.)) # delay of 2*serialdelaytimerwait microseconds every 32*11 bits
        # serialrate=adjustedbrate/11./(self.num_bytes*HAAS_NUM_BOARD+len(max10adcchans)*self.nsamp) #including start+2stop bits
        # print(("rate theoretically",round(serialrate,2),"Hz over serial"))
        ports = list(serial.tools.list_ports.comports()); ports.sort(reverse=True)
        autofindusbports = len(self.usbport)==0
        if self.serport=="" or True:
            for port_no, description, address in ports: print((port_no,":",description,":",address))
        for port_no, description, address in ports:
            if self.serport=="":
                if '1A86:7523' in address or '1a86:7523' in address: self.serport = port_no
            if autofindusbports:
                if "USB Serial" in description or "Haasoscope" in description: self.usbport.append(port_no)
        if self.serport!="":
            try:
                self.ser = Serial(self.serport,self.brate,timeout=self.sertimeout,stopbits=2)
            except SerialException:
                print(("Could not open",self.serport,"!")); return False
            print(("connected serial to",self.serport,", timeout",self.sertimeout,"seconds"))
        else: self.ser=""
        for p in self.usbport:
            self.usbser.append(Serial(p,timeout=self.sertimeout))
            print(("connected USBserial to",p,", timeout",self.sertimeout,"seconds"))
        if self.serport=="": print("No serial COM port opened!"); return False
        return True

    def set_variables(self, **argd):
            self.__dict__.update (argd)