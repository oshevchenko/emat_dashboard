import message_queue as mq
import numpy as np
from struct import unpack
import time, json, os
from const import *

class HaasoscopeStateMachine(object):
    """docstring for HaasoscopeStateMachine"""
    def __init__(self, gui, ser):
        super(HaasoscopeStateMachine, self).__init__()
        self.db = True
        self.gui = gui
        self.ser = ser
        self.mq_adapter = mq.Adapter('main_queue')
        self.mq_subscriber = mq.Subscriber(self.mq_adapter)

        print(("num main ADC and max10adc bytes for all boards = ",HAAS_NUM_BYTES*HAAS_NUM_BOARD,"and",len(HAAS_MAX10ADCCHANS)*HAAS_NSAMP))
        self.Vrms=np.zeros(HAAS_NUM_BOARD*HAAS_NUM_CHAN_PER_BOARD, dtype=float) # the Vrms for each channel
        self.Vmean=np.zeros(HAAS_NUM_BOARD*HAAS_NUM_CHAN_PER_BOARD, dtype=float) # the Vmean for each channel
        self.dologicanalyzer = False
        self.rolltrigger=True #roll the trigger
        self.ser.tellrolltrig(self.rolltrigger)
        self.downsample=2 #adc speed reduction, log 2... so 0 (none), 1(factor 2), 2(factor 4), etc.
        self.dolockin=False # read lockin info
        self.dooversample=np.zeros(HAAS_NUM_BOARD*HAAS_NUM_CHAN_PER_BOARD, dtype=int) # 1 is oversampling, 0 is no oversampling, 9 is over-oversampling
        self.maxdownsample=15 # slowest I can run
        self.telldownsample(self.downsample)
        self.uniqueID=[]
        self.getIDs()
        xscale =  HAAS_NUM_SAMPLES/2.0*(1000.0*pow(2,self.downsample)/HAAS_CLKRATE)
        self.lowdaclevel=np.ones(HAAS_NUM_BOARD*HAAS_NUM_CHAN_PER_BOARD)*2050 # these hold the user set levels for each gain combination
        self.highdaclevel=np.ones(HAAS_NUM_BOARD*HAAS_NUM_CHAN_PER_BOARD)*2800
        self.lowdaclevelsuper=np.ones(HAAS_NUM_BOARD*HAAS_NUM_CHAN_PER_BOARD)*120
        self.highdaclevelsuper=np.ones(HAAS_NUM_BOARD*HAAS_NUM_CHAN_PER_BOARD)*50
        self.lowdaclevelac=np.ones(HAAS_NUM_BOARD*HAAS_NUM_CHAN_PER_BOARD)*2250 # these hold the user set levels for each gain combination in ac coupling mode
        self.highdaclevelac=np.ones(HAAS_NUM_BOARD*HAAS_NUM_CHAN_PER_BOARD)*4600
        self.lowdaclevelsuperac=np.ones(HAAS_NUM_BOARD*HAAS_NUM_CHAN_PER_BOARD)*2300
        self.highdaclevelsuperac=np.ones(HAAS_NUM_BOARD*HAAS_NUM_CHAN_PER_BOARD)*4600
        self.chanlevel=np.ones(HAAS_NUM_BOARD*HAAS_NUM_CHAN_PER_BOARD)*self.lowdaclevel # the current level for each channel, initially set to lowdaclevel (x1)
        self.gain=np.ones(HAAS_NUM_BOARD*HAAS_NUM_CHAN_PER_BOARD, dtype=int) # 1 is low gain, 0 is high gain (x10)
        self.supergain=np.ones(HAAS_NUM_BOARD*HAAS_NUM_CHAN_PER_BOARD, dtype=int) # 1 is normal gain, 0 is super gain (x100)
        self.acdc=np.ones(HAAS_NUM_BOARD*HAAS_NUM_CHAN_PER_BOARD, dtype=int) # 1 is dc, 0 is ac
        self.trigsactive=np.ones(HAAS_NUM_BOARD*HAAS_NUM_CHAN_PER_BOARD, dtype=int) # 1 is triggering on that channel, 0 is not triggering on it
        self.dooversample=np.zeros(HAAS_NUM_BOARD*HAAS_NUM_CHAN_PER_BOARD, dtype=int) # 1 is oversampling, 0 is no oversampling, 9 is over-oversampling
        self.selectedchannel = 0
        self.ydatarefchan=-1 #the reference channel for each board, whose ydata will be subtracted from other channels' ydata on the board
        self.domeasure = True
        self.readcalib()
        text = self.chantext()
        self.gui.on_launch_draw(xscale, text)

    def chantext(self):
        text ="Channel: "+str(self.selectedchannel)
        if self.ydatarefchan>=0: text += " - ref "+str(int(self.ydatarefchan))
        text +="\nLevel="+str(int(self.chanlevel[self.selectedchannel]))
        if self.acdc[self.selectedchannel]:
            text +="\nDC coupled"
        else:
            text +="\nAC coupled"
        chanonboard = self.selectedchannel%HAAS_NUM_CHAN_PER_BOARD
        theboard = HAAS_NUM_BOARD-1-self.selectedchannel/HAAS_NUM_CHAN_PER_BOARD
        # if self.havereadswitchdata:
        #     if self.testBit(self.switchpos[theboard],chanonboard):
        #         text += ", 1M"
        #     else:
        #         text += ", 50"
        text +="\nTriggering="+str(self.trigsactive[self.selectedchannel])
        if self.domeasure:
            if abs(self.Vmean[self.selectedchannel])>.9: text +="\nMean={0:1.3g} V".format(self.Vmean[self.selectedchannel])
            else: text +="\nMean={0:1.3g} mV".format(1000.*self.Vmean[self.selectedchannel])
            if abs(self.Vrms[self.selectedchannel])>.9: text +="\nRMS={0:1.3g} V".format(self.Vrms[self.selectedchannel])
            else: text +="\nRMS={0:1.3g} mV".format(1000.*self.Vrms[self.selectedchannel])
        if chanonboard<2:
            if self.dooversample[self.selectedchannel]==1: text+= "\nOversampled x2"
            if self.dooversample[self.selectedchannel]==9: text+= "\nOversampled x4"
        else:
            if self.selectedchannel>1 and self.dooversample[self.selectedchannel-2]: text+= "\nOff (oversamp)"
        if len(HAAS_MAX10ADCCHANS)>0:
            text+="\n"
            text+="\nSlow chan: "+str(self.selectedmax10channel)
        return text

    def setdac(self,chan,val,board):
        if chan==0: c="50"
        elif chan==1: c="52"
        elif chan==2: c="54"
        elif chan==3: c="56"
        else:
            print(("channel",chan,"out of range 0-3"))
            return
        if val>4096*2-1 or val<0:
            print(("value",val,"out of range 0-(4096*2-1)"))
            return
        #d="0" # Vdd ref (0-3.3V, but noisy?)
        d="8" #internal ref, gain=1 (0-2V)
        if val>4095:
            d="9" #internal ref, gain=2 (0-4V)
            val/=2
        self.ser.sendi2c("60 "+c+d+('%0*x' % (3,int(val))),  board) #DAC, can go from 000 to 0fff in last 12 bits, and only send to the selected board

        # example:
        # channel 0 , board 0 calib
        # 136, 3, // header for i2c command with 3 bytes of data
        # 96, // i2c address of dac
        # 80, // channel 80,82,84,86 for chan 0,1,2,3
        # 136, 22, // high 4 bits can be 8 or 9 (internal ref 2V or 4V, respectively), next 12 bits are the 0-4095 level
        # 0 // send to board 0 (200 for all boards)

    def setdaclevelforchan(self,chan,level):
        if level>4096*2-1:
            print("level can't be bigger than 2**13-1=4096*2-1")
            level=4096*2-1
        if level<0:
            print("level can't be less than 0")
            level=0
        theboard = HAAS_NUM_BOARD-1-int(chan/HAAS_NUM_CHAN_PER_BOARD)
        print(("theboard:",theboard," HAAS_NUM_BOARD:",HAAS_NUM_BOARD," chan:",chan," HAAS_NUM_CHAN_PER_BOARD:",HAAS_NUM_CHAN_PER_BOARD))

        chanonboard = chan%HAAS_NUM_CHAN_PER_BOARD
        self.setdac(chanonboard,level,theboard)
        self.chanlevel[chan]=level
        # TODO: Add drawtext call!
        # if not self.firstdrawtext: self.drawtext()
        if self.db: print(("DAC level set for channel",chan,"to",level,"which is chan",chanonboard,"on board",theboard))


    def setdacvalue(self):
        #set current dac level to the remembered value, depending on other settings
        if self.gain[self.selectedchannel]: # low gain
            if self.supergain[self.selectedchannel]:
                if self.acdc[self.selectedchannel]: self.setdaclevelforchan(self.selectedchannel,self.lowdaclevel[self.selectedchannel])
                else: self.setdaclevelforchan(self.selectedchannel,self.lowdaclevelac[self.selectedchannel])
            else: #supergain
                if self.acdc[self.selectedchannel]: self.setdaclevelforchan(self.selectedchannel,self.lowdaclevelsuper[self.selectedchannel]) #dc super gain
                else: self.setdaclevelforchan(self.selectedchannel,self.lowdaclevelsuperac[self.selectedchannel])
        else: # high gain
            if self.supergain[self.selectedchannel]:
                if self.acdc[self.selectedchannel]: self.setdaclevelforchan(self.selectedchannel,self.highdaclevel[self.selectedchannel])
                else: self.setdaclevelforchan(self.selectedchannel,self.highdaclevelac[self.selectedchannel])
            else: #supergain
                if self.acdc[self.selectedchannel]: self.setdaclevelforchan(self.selectedchannel,self.highdaclevelsuper[self.selectedchannel]) #dc super gain
                else: self.setdaclevelforchan(self.selectedchannel,self.highdaclevelsuperac[self.selectedchannel])


    def setdacvalues(self,sc):
        oldchan=self.selectedchannel
        for chan in range(sc,sc+4):
            self.selectedchannel=chan
            self.setdacvalue()
        self.selectedchannel=oldchan

    def readcalib(self):
        cwd = os.getcwd()
        print(("current directory is",cwd))
        for board in range(0,HAAS_NUM_BOARD):
            self.readcalibforboard(board)

    def readcalibforboard(self,board):
        sc = board*HAAS_NUM_CHAN_PER_BOARD
        if len(self.uniqueID)<=board:
            print(("failed to get board ID for board",board))
            self.setdacvalues(sc) #will load in defaults
            return
        print(("reading calibrations for board",board,", channels",sc,"-",sc+4))
        fname = "calib/calib_"+self.uniqueID[board]+".json.txt"
        try:
            c = json.load(open(fname))
            print(("read",fname))
            assert c['boardID']==self.uniqueID[board]
            self.lowdaclevel[sc : sc+4] = c['lowdaclevels']
            self.highdaclevel[sc : sc+4] = c['highdaclevels']
            self.lowdaclevelsuper[sc : sc+4] = c['lowdaclevelssuper']
            self.highdaclevelsuper[sc : sc+4] = c['highdaclevelssuper']
            self.lowdaclevelac[sc : sc+4] = c['lowdaclevelsac']
            self.highdaclevelac[sc : sc+4] = c['highdaclevelsac']
            self.lowdaclevelsuperac[sc : sc+4] = c['lowdaclevelssuperac']
            self.highdaclevelsuperac[sc : sc+4] = c['highdaclevelssuperac']
            if "firmwareversion" in c:
                print(("calib was written using firmware version",c["firmwareversion"]))
            else:
                print("calib was written using unknown firmware version")
            self.setdacvalues(sc) #and use the new levels right away
            if not self.firstdrawtext: self.drawtext()
        except IOError:
            print(("No calib file found for board",board,"at file",fname))
            self.setdacvalues(sc) #will load in defaults

    def telltickstowait(self):
        #tell it the number of clock ticks to wait, log2, between sending bytes
        if self.ser.dousb: ds=self.downsample-2
        else: ds=self.downsample-3
        if ds<1: ds=1
        if self.ser.minfirmwareversion>=5:
            ds=1
        else:
            if ds>8:
                ds=8 # otherwise we timeout upon readout
                if HAAS_NUM_SAMPLES>10: self.ser.settriggerpoint(HAAS_NUM_SAMPLES-10) # set trigger way to the right, so we can capture full event - NOTE - screws up mini-screen!
                self.gui.disable_otherline(0)
                # self.otherlines[0].set_visible(False) # don't draw trigger time position line, to indicate it's not really set anymore
        self.ser.telltickstowait(ds)

    def getIDs(self):
        debug3=True
        for n in range(HAAS_NUM_BOARD):
            rslt = self.ser.getID(n)
            num_other_bytes = 8
            if len(rslt)==num_other_bytes:
                byte_array = unpack('%dB'%len(rslt),rslt) #Convert serial data to array of numbers
                self.uniqueID.append( ''.join(format(x, '02x') for x in byte_array) )
                if debug3: print(("got uniqueID",self.uniqueID[n],"for board",n,", len is now",len(self.uniqueID)))
            else: print(("getID asked for",num_other_bytes,"bytes and got",len(rslt),"from board",n))

    def telldownsample(self,ds):
        #tell it the amount to downsample, log2... so 0 (none), 1(factor 2), 2(factor 4), etc.
        if self.dolockin and ds<2: print("downsample can't be <2 in lockin mode !"); return False
        if ds<-8: print("downsample can't be <-8... that's too fast !"); return False
        if ds<0: # negative downsample means just scale/zoom the data, don't actually change the sampling done on the board
            self.downsample=ds
        else:
            if max(self.dooversample)>0 and ds>0: print("can't change sampling rate while oversampling - must be fastest!"); return False
            if ds>self.maxdownsample: print(("downsample >",self.maxdownsample,"doesn't work well... I get bored running that slow!")); return False
            self.ser.telldownsample(ds)
            # frame=[]
            # frame.append(124)
            # frame.append(ds)
            # self.ser.write(frame)
            self.downsample=ds
            if self.db: print(("downsample is",self.downsample))
            if self.dolockin:
                twoforoversampling=1
                uspersample=(1.0/HAAS_CLKRATE)*pow(2,self.downsample)/twoforoversampling # us per sample = 10 ns * 2^downsample
                numtoshiftf= 1.0/self.reffreq/4.0 / uspersample
                print(("would like to shift by",round(numtoshiftf,4),"samples, and uspersample is",uspersample))
                self.numtoshift = int(round(numtoshiftf,0))+0 # shift by 90 deg
                self.ser.telllockinnumtoshift(self.numtoshift)
            else:
                self.ser.telllockinnumtoshift(0) # tells the FPGA to not send lockin info
            self.telltickstowait()
        if hasattr(self,'ax'): self.setxaxis(self.ax,self.figure)
        return True # successful (parameter within OK range)

    def togglelogicanalyzer(self):
        self.dologicanalyzer = not self.dologicanalyzer
        self.ser.setlogicanalyzer(self.dologicanalyzer)
        self.gui.setlogicanalyzer(self.dologicanalyzer)
        print(("dologicanalyzer is now",self.dologicanalyzer))

    def getfirmchan(self,chan):
        theboard = HAAS_NUM_BOARD-1-int(chan/HAAS_NUM_CHAN_PER_BOARD)
        chanonboard = chan%HAAS_NUM_CHAN_PER_BOARD
        firmchan=theboard*HAAS_NUM_CHAN_PER_BOARD+chanonboard
        return firmchan # the channels are numbered differently in the firmware

    def process_queue(self):
        while True:
            message = self.mq_subscriber.consume()
            if not message: break
            message_content = message.get_content_body()
            msg_id = message_content['id']
            print ("message id:", msg_id)
            if msg_id==MSG_ID_YDATA:
                ydata = message_content['ydata']
                bn = message_content['bn']
                self.gui.on_running(ydata, bn, self.downsample)
            elif msg_id==MSG_ID_DRAWTEXT:
                self.gui.drawtext(self.chantext())
            elif msg_id==MSG_ID_TOGGLE_LOGICANALYZER:
                self.togglelogicanalyzer()
            elif msg_id==MSG_ID_SELECT_CHANNEL:
                self.selectedchannel = message_content['selectedchannel']
                self.gui.drawtext(self.chantext())
                print(("New selectedchannel:",self.selectedchannel))
            elif msg_id==MSG_ID_SELECT_TRIGGER_CHANNEL:
                channel = message_content['triggerchannel']
                self.trigsactive[channel] = not self.trigsactive[channel]
                self.gui.settriggerchan(self,channel, self.trigsactive[channel])
                self.gui.drawtext(self.chantext())
                firmchan=self.getfirmchan(channel)
                self.ser.settriggerchan(firmchan)
                if self.db: print(("Trigger toggled for channel",channel))

        pass
