import message_queue as mq
import tkinter as tk
from matplotlib.figure import Figure
from numpy import arange, sin, pi
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import numpy as np
from const import *

class EmatPage(tk.Frame) :
    keyResample=False
    keysettriggertime=False
    keySPI=False
    keyi2c=False
    keyLevel=False
    keyShift=False
    keyAlt=False
    keyControl=False

    def __init__(self, parent, controller):
        tk.Frame.__init__(self,parent)
        self.mq_adapter = mq.Adapter('main_queue')
        self.mq_publisher = mq.Publisher(self.mq_adapter)
        self.ydatarefchan=-1 #the reference channel for each board, whose ydata will be subtracted from other channels' ydata on the board
        self.dologicanalyzer = False
        self.sincresample=0 # amount of resampling to do (sinx/x)
        self.domaindrawing=True
        self.domeasure=True
        self.xdata=np.arange(HAAS_NUM_SAMPLES)
        self.xdata2=np.arange(HAAS_NUM_SAMPLES*2) # for oversampling
        self.xdata4=np.arange(HAAS_NUM_SAMPLES*4) # for over-oversampling
        self.xydata=np.empty([HAAS_NUM_CHAN_PER_BOARD*HAAS_NUM_BOARD,2,HAAS_NUM_SAMPLES-1],dtype=float)
        self.Vrms=np.zeros(HAAS_NUM_BOARD*HAAS_NUM_CHAN_PER_BOARD, dtype=float) # the Vrms for each channel
        self.Vmean=np.zeros(HAAS_NUM_BOARD*HAAS_NUM_CHAN_PER_BOARD, dtype=float) # the Vmean for each channel
        self.gain=np.ones(HAAS_NUM_BOARD*HAAS_NUM_CHAN_PER_BOARD, dtype=int) # 1 is low gain, 0 is high gain (x10)
        self.supergain=np.ones(HAAS_NUM_BOARD*HAAS_NUM_CHAN_PER_BOARD, dtype=int) # 1 is normal gain, 0 is super gain (x100)


        # >>>>>>>>>>>>>>>>>>>>>>>>>
        self.yscale = 7.5 # Vpp for full scale
        # if self.minfirmwareversion>=15: #v9.0 boards
        #     self.yscale*=1.1 # if we used 10M / 1.1M / 11k input resistors
        self.min_y = -self.yscale/2. #-4.0 #0 ADC
        self.max_y = self.yscale/2. #4.0 #256 ADC

        self.chtext = "Ch." #the text in the legend for each channel
        self.lines = []
        self.fitline1 = -1 # set to >-1 to draw a risetime fit
        self.logicline1 = -1 # to remember which is the first logic analyzer line
        self.otherlines = []
        self.texts = []
        # self.xydataslow=np.empty([len(HAAS_MAX10ADCCHANS),2,HAAS_NSAMP],dtype=float)
        # if self.domaindrawing: self.on_launch_draw()

        # >>>>>>>>>>>>>>>>>>>>>>>>>
        self.grid(row=1, column=0, columnspan=4, sticky="nsew")
        self.db = True
        ###Matplotlib

        self.fig = Figure(figsize=(5, 5), dpi=100)
        self.ax = self.fig.add_subplot(111)
        t = arange(0.0, 3.0, 0.01)
        s = sin(2*pi*t)

        self.ax.plot(t, s)

        fr = tk.Frame(self)
        fr.grid(row=0, column=0,  rowspan=7, sticky='nsew')
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=3)
        self.grid_rowconfigure(2, weight=1)
        self.grid_rowconfigure(3, weight=1)
        self.grid_rowconfigure(4, weight=1)
        self.grid_rowconfigure(5, weight=1)
        self.grid_rowconfigure(6, weight=1)

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=1)


        self.canvas = FigureCanvasTkAgg(self.fig, master=fr)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack()

        toolbar = NavigationToolbar2Tk(self.canvas, fr)
        toolbar.update()
        self.canvas._tkcanvas.pack()

        textbox_width = tk.Label(self, text="Width, mm:")
        textbox_width.grid(row=0, column=1, columnspan=2, sticky='nsew')
        # textbox_width.insert('end', "Width, mm:")


        measured_width = tk.Label(self, text="--.-", bg='lavender', font=("Helvetica", 20))
        measured_width.grid(row=1, column=1, columnspan=2, padx=5, pady=5, sticky='nsew')
        # measured_width.insert('end', "10.0")

        textbox_ps_on_off = tk.Label(self, text="PS:")
        textbox_ps_on_off.grid(row=2, column=1, rowspan=2, sticky='nsew')
        # textbox_ps_on_off.insert('end', "PS:")

        button_ps_on = tk.Button(self, text="ON",
                            command=lambda: controller.on_key_press())
        button_ps_on.grid(row=2, column=2, padx=5, pady=5, sticky='nsew')

        button_ps_off = tk.Button(self, text="OFF",
                            command=lambda: controller.on_key_press())
        button_ps_off.grid(row=3, column=2, padx=5, pady=5, sticky='nsew')

        textbox_hv_on_off = tk.Label(self, text="HV:")
        textbox_hv_on_off.grid(row=4, column=1, rowspan=2, sticky='nsew')
        # textbox_hv_on_off.insert('end', "HV:")

        button_hv_on = tk.Button(self, text="ON",
                            command=lambda: self.mq_publisher.publish(mq.Message({'id': MSG_ID_HV_ON})))

        button_hv_on.grid(row=4, column=2, padx=5, pady=5, sticky='nsew')

        button_hv_off = tk.Button(self, text="OFF",
                            command=lambda: self.mq_publisher.publish(mq.Message({'id': MSG_ID_HV_OFF})))
        button_hv_off.grid(row=5, column=2, padx=5, pady=5,  sticky='nsew')

        button_pulse = tk.Button(self, text="PULSE",
                            command=lambda: self.mq_publisher.publish(mq.Message({'id': MSG_ID_PULSE_ON})))
        button_pulse.grid(row=6, column=1, columnspan=2, padx=5, pady=5, sticky='nsew')


        ###Lab
        textbox1 = tk.Entry(self)
        textbox1.grid(row=7, column=0, columnspan=3, sticky='nsew')
        textbox1.insert('end', "Hello Emat!")

    firstdrawtext=True
    needtoredrawtext=False
    havereadswitchdata=False


    def drawtext(self, text):
        height = 0.25 # height up from bottom to start drawing text
        xpos = 1.02 # how far over to the right to draw
        if self.firstdrawtext:
            self.texts.append(self.ax.text(xpos, height, text, horizontalalignment='left', verticalalignment='top',transform=self.ax.transAxes))
            self.firstdrawtext=False
        else:
            self.texts[0].remove()
            self.texts[0]=(self.ax.text(xpos, height, text, horizontalalignment='left', verticalalignment='top',transform=self.ax.transAxes))
            #for txt in self.ax.texts: print txt # debugging
        self.needtoredrawtext=True
        self.canvas.draw()

    def onrelease(self,event): # a key was released
        #print event.key, "released"
        if event.key.find("shift")>-1: self.keyShift=False;return
        if event.key.find("alt")>-1: self.keyAlt=False;return
        if event.key=="control": self.keyControl=False; return
        if event.key.find("ctrl")>-1: self.keyControl=False; return
        if event.key.find("control")>-1: self.keyControl=False; return

    #will grab the next keys as input
    keyResample=False
    keysettriggertime=False
    keySPI=False
    keyi2c=False
    keyLevel=False
    keyShift=False
    keyAlt=False
    keyControl=False

    def onpress(self,event): # a key was pressed
            if self.keyResample:
                try:
                    self.sincresample=int(event.key)
                    print(("resample now",self.sincresample))
                    if self.sincresample>0: self.xydata=np.empty([num_chan_per_board*HAAS_NUM_BOARD,2,self.sincresample*(HAAS_NUM_SAMPLES-1)],dtype=float)
                    else: self.xydata=np.empty([num_chan_per_board*HAAS_NUM_BOARD,2,1*(HAAS_NUM_SAMPLES-1)],dtype=float)
                    self.prepareforsamplechange();
                    self.keyResample=False; return
                except ValueError: pass
            elif self.keysettriggertime:
                if event.key=="enter":
                    self.settriggertime(self.triggertimethresh)
                    self.keysettriggertime=False; return
                else:
                    self.triggertimethresh=10*self.triggertimethresh+int(event.key)
                    print(("triggertimethresh",self.triggertimethresh)); return
            elif self.keySPI:
                if event.key=="enter":
                    self.tellSPIsetup(self.SPIval)
                    self.keySPI=False; return
                else:
                    self.SPIval=10*self.SPIval+int(event.key)
                    print(("SPIval",self.SPIval)); return
            elif self.keyi2c:
                if event.key=="enter":
                    self.sendi2c(self.i2ctemp)
                    self.keyi2c=False; return
                else:
                    self.i2ctemp=self.i2ctemp+event.key
                    print(("i2ctemp",self.i2ctemp)); return
            elif self.keyLevel:
                if event.key=="enter":
                    self.keyLevel=False
                    s=self.leveltemp.split(",")
                    #print "Got",int(s[0]),int(s[1])
                    self.selectedchannel=int(s[0])
                    self.chanlevel[self.selectedchannel] = int(s[1])
                    self.rememberdacvalue()
                    self.setdacvalue()
                    return
                else:
                    self.leveltemp=self.leveltemp+event.key
                    print(("leveltemp",self.leveltemp)); return
            elif event.key=="r": self.mq_publisher.publish(mq.Message({'id': MSG_ID_TOGGLE_ROLL_TRIG})); return
            elif event.key=="p": self.paused = not self.paused;print(("paused",self.paused)); return
            elif event.key=="P": self.getone = not self.getone;print(("get one",self.getone)); return
            elif event.key=="a": self.average = not self.average;print(("average",self.average)); return
            elif event.key=="h": self.togglehighres(); return
            elif event.key=="e": self.toggleuseexttrig(); return
            elif event.key=="A": self.toggleautorearm(); return
            elif event.key=="U": self.toggledousb(); return
            elif event.key=="O": self.oversamp(self.selectedchannel); self.prepareforsamplechange(); return
            elif event.key=="ctrl+o": self.overoversamp(); self.prepareforsamplechange(); return
            elif event.key==">": self.refsinchan=self.selectedchannel; self.oldchanphase=-1.; self.reffreq=0;
            elif event.key=="t": self.fallingedge=not self.fallingedge;self.settriggertype(self.fallingedge);print(("trigger falling edge toggled to",self.fallingedge)); return
            elif event.key=="g": self.dogrid=not self.dogrid;print(("dogrid toggled",self.dogrid)); self.ax.grid(self.dogrid); return
            elif event.key=="ctrl+g": self.ax.xaxis.set_major_locator(plt.MultipleLocator( (self.max_x*1000/1024-self.min_x*1000/1024)/8./5. )); return
            elif event.key=="G": self.ax.yaxis.set_major_locator(plt.MultipleLocator(0.2)); return
            elif event.key=="x": self.tellswitchgain(self.selectedchannel)
            elif event.key=="ctrl+x":
                for chan in range(num_chan_per_board*HAAS_NUM_BOARD): self.tellswitchgain(chan)
            elif event.key=="X": self.togglesupergainchan(self.selectedchannel)
            elif event.key=="ctrl+X":
                for chan in range(num_chan_per_board*HAAS_NUM_BOARD): self.selectedchannel=chan; self.togglesupergainchan(chan)
            elif event.key=="F": self.fftchan=self.selectedchannel; self.dofft=True; self.keyShift=False; return
            elif event.key=="/": self.setacdc();return
            elif event.key=="I": self.testi2c(); return
            elif event.key=="c": self.readcalib(); return
            elif event.key=="C": self.storecalib(); return
            elif event.key=="D": self.decode(); return
            elif event.key=="ctrl+r":
                if self.ydatarefchan<0: self.ydatarefchan=self.selectedchannel
                else: self.ydatarefchan=-1
            elif event.key=="|": print("starting autocalibration");self.autocalibchannel=0;
            elif event.key=="W": self.domaindrawing=not self.domaindrawing; self.domeasure=self.domaindrawing; print(("domaindrawing now",self.domaindrawing)); return
            elif event.key=="M": self.domeasure=not self.domeasure; print(("domeasure now",self.domeasure)); self.drawtext(); return
            elif event.key=="m": self.domarkers(); return
            elif event.key=="Y":
                if self.selectedchannel+1>=len(self.dooversample): print("can't do XY plot on last channel")
                else:
                    if self.dooversample[self.selectedchannel]==self.dooversample[self.selectedchannel+1]:
                        self.doxyplot=True; self.xychan=self.selectedchannel; print(("doxyplot now",self.doxyplot,"for channel",self.xychan)); return;
                    else: print("oversampling settings must match between channels for XY plotting")
                self.keyShift=False
            elif event.key=="Z": self.recorddata=True; self.recorddatachan=self.selectedchannel; self.recordedchannel=[]; print(("recorddata now",self.recorddata,"for channel",self.recorddatachan)); self.keyShift=False; return;
            elif event.key=="right": self.telldownsample(DIR_RIGHT); return
            elif event.key=="left": self.telldownsample(DIR_LEFT); return
            elif event.key=="shift+right": self.telldownsample(DIR_RIGHT); return
            elif event.key=="shift+left": self.telldownsample(DIR_LEFT); return
            elif event.key=="up": self.adjustvertical(DIR_UP); return
            elif event.key=="down": self.adjustvertical(DIR_DOWN); return
            elif event.key=="shift+up": self.adjustvertical(DIR_UP); return
            elif event.key=="shift+down": self.adjustvertical(DIR_DOWN); return
            elif event.key=="ctrl+up": self.adjustvertical(DIR_UP); return
            elif event.key=="ctrl+down": self.adjustvertical(DIR_DOWN); return
            elif event.key=="?": self.togglelogicanalyzer(); return
            elif event.key=="d": self.tellminidisplaychan(self.selectedchannel);return
            elif event.key=="R": self.keyResample=True;print("now enter amount to sinc resample (0-9)");return
            elif event.key=="T": self.keysettriggertime=True;self.triggertimethresh=0;print("now enter time over/under thresh, then enter");return
            elif event.key=="S": self.keySPI=True;self.SPIval=0;print("now enter SPI code, then enter");return
            elif event.key=="i": self.keyi2c=True;self.i2ctemp="";print("now enter byte in hex for i2c, then enter:");return
            elif event.key=="L": self.keyLevel=True;self.leveltemp="";print("now enter [channel to set level for, level] then enter:");return
            elif event.key=="shift": self.keyShift=True;return
            elif event.key=="alt": self.keyAlt=True;return
            elif event.key=="control": self.keyControl=True;return
            elif event.key=="tab":
                for l in self.lines:
                    self.togglechannel(l)
                self.figure.canvas.draw()
                return;
            try:
                print(('key=%s' % (event.key)))
                print(('x=%d, y=%d, xdata=%f, ydata=%f' % (event.x, event.y, event.xdata, event.ydata)))
            except TypeError: pass

    def setxaxis(self, downsample):
        xscale =  HAAS_NUM_SAMPLES/2.0*(1000.0*pow(2, downsample)/HAAS_CLKRATE)
        if xscale<1e3:
            self.ax.set_xlabel("Time (ns)")
            self.min_x = -xscale
            self.max_x = xscale
            self.xscaling=1.e0
        elif xscale<1e6:
            self.ax.set_xlabel("Time (us)")
            self.min_x = -xscale/1e3
            self.max_x = xscale/1e3
            self.xscaling=1.e3
        else:
            self.ax.set_xlabel("Time (ms)")
            self.min_x = -xscale/1e6
            self.max_x = xscale/1e6
            self.xscaling=1.e6
        self.ax.set_xlim(self.min_x, self.max_x)
        self.ax.xaxis.set_major_locator(plt.MultipleLocator( (self.max_x*1000/1024-self.min_x*1000/1024)/8. ))
        self.canvas.draw()

    def setyaxis(self):
        self.ax.set_ylim(self.min_y, self.max_y)
        self.ax.set_ylabel("Volts") #("ADC value")
        self.ax.yaxis.set_major_locator(plt.MultipleLocator(1.0))
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)
        self.ax.spines['left'].set_visible(False)
        self.ax.spines['bottom'].set_visible(False)
        plt.setp(self.ax.get_xticklines(),visible=False)
        plt.setp(self.ax.get_yticklines(),visible=False)
        #self.ax.set_autoscaley_on(True)
        self.canvas.draw()

    def on_launch_draw(self, downsample, text):
        plt.ion() #turn on interactive mode
        self.nlines = HAAS_NUM_CHAN_PER_BOARD*HAAS_NUM_BOARD+len(HAAS_MAX10ADCCHANS)
        if self.db: print(("nlines=",self.nlines))
        for l in np.arange(self.nlines):
            maxchan=l-HAAS_NUM_CHAN_PER_BOARD*HAAS_NUM_BOARD
            c=(0,0,0)
            if maxchan>=0: # these are the slow ADC channels
                if HAAS_NUM_BOARD>1:
                    board = int(HAAS_NUM_BOARD-1-HAAS_MAX10ADCCHANS[maxchan][0])
                    if board%4==0: c=(1-0.1*maxchan,0,0)
                    if board%4==1: c=(0,1-0.1*maxchan,0)
                    if board%4==2: c=(0,0,1-0.1*maxchan)
                    if board%4==3: c=(1-0.1*maxchan,0,1-0.1*maxchan)
                else:
                    c=(0.1*(maxchan+1),0.1*(maxchan+1),0.1*(maxchan+1))
                line, = self.ax.plot([],[], '-', label=str(HAAS_MAX10ADCCHANS[maxchan]), color=c, linewidth=0.5, alpha=.5)
            else: # these are the fast ADC channels
                chan=l%4
                if HAAS_NUM_BOARD>1:
                    board=l/4
                    if board%4==0: c=(1-0.2*chan,0,0)
                    if board%4==1: c=(0,1-0.2*chan,0)
                    if board%4==2: c=(0,0,1-0.2*chan)
                    if board%4==3: c=(1-0.2*chan,0,1-0.2*chan)
                else:
                    if chan==0: c="red"
                    if chan==1: c="green"
                    if chan==2: c="blue"
                    if chan==3: c="magenta"
                line, = self.ax.plot([],[], '-', label=self.chtext+str(l), color=c, linewidth=1.0, alpha=.9)
            self.lines.append(line)

        #for the logic analyzer
        for l in np.arange(8):
            c=(0,0,0)
            line, = self.ax.plot([],[], '-', label="_logic"+str(l)+"_", color=c, linewidth=1.7, alpha=.65) # the leading and trailing "_"'s mean don't show in the legend
            line.set_visible(False)
            self.lines.append(line)
            if l==0: self.logicline1=len(self.lines)-1 # remember index where this first logic line is
        #other data to draw
        if self.fitline1>-1:
            line, = self.ax.plot([],[], '-', label="fit data", color="purple", linewidth=0.5, alpha=.5)
            self.lines.append(line)
            self.fitline1=len(self.lines)-1 # remember index where this line is
        self.setxaxis(downsample)
        self.setyaxis();
        self.ax.grid(True)
        self.vline=0
        otherline , = self.ax.plot([self.vline, self.vline], [-2, 2], 'k--', lw=1)#,label='trigger time vert')
        self.otherlines.append(otherline)
        self.hline = 0
        otherline , = self.ax.plot( [-2, 2], [self.hline, self.hline], 'k--', lw=1)#,label='trigger thresh horiz')
        self.otherlines.append(otherline)
        self.hline2 = 0
        otherline , = self.ax.plot( [-2, 2], [self.hline2, self.hline2], 'k--', lw=1, color='blue')#, label='trigger2 thresh horiz')
        otherline.set_visible(False)
        self.otherlines.append(otherline)
        if self.db: print(("drew lines in launch",len(self.otherlines)))
        self.canvas.mpl_connect('button_press_event', self.onclick)
        self.canvas.mpl_connect('key_press_event', self.onpress)
        self.canvas.mpl_connect('key_release_event', self.onrelease)
        self.canvas.mpl_connect('pick_event', self.onpick)
        # self.canvas.mpl_connect('scroll_event', self.onscroll)
        self.leg = self.ax.legend(loc='upper left', bbox_to_anchor=(1.02, 1),
              ncol=1, borderaxespad=0, fancybox=False, shadow=False, fontsize=10)
        self.leg.get_frame().set_alpha(0.4)
        self.fig.subplots_adjust(right=0.76)
        self.fig.subplots_adjust(left=.10)
        self.fig.subplots_adjust(top=.95)
        self.fig.subplots_adjust(bottom=.10)
        self.canvas.set_window_title('Haasoscope')
        self.lined = dict()
        channum=0
        for legline, origline in zip(self.leg.get_lines(), self.lines):
            legline.set_picker(5)  # 5 pts tolerance
            legline.set_linewidth(2.0)
            origline.set_picker(5)
            #save a reference to the plot line and legend line and channel number, accessible from either line or the channel number
            self.lined[legline] = (origline,legline,channum)
            self.lined[origline] = (origline,legline,channum)
            self.lined[channum] = (origline,legline,channum)
            channum+=1
        self.drawtext(text)
        # self.canvas.mpl_connect('close_event', self.handle_main_close)
        self.canvas.draw()

    def toggleuseexttrig(self):
        msg = mq.Message({'id': MSG_ID_TOGGLE_EXT_TRIG})
        self.mq_publisher.publish(msg)

    def toggleautorearm(self):
        msg = mq.Message({'id': MSG_ID_TOGGLE_AUTO_REARM})
        self.mq_publisher.publish(msg)

    def settriggerchan(self, tp, trigactive):
        # tell it to trigger or not trigger on a given channel
        origline,legline,channum = self.lined[tp]
        if trigactive: self.leg.get_texts()[tp].set_color('#000000')
        else: self.leg.get_texts()[tp].set_color('#aFaFaF')
        self.canvas.draw()

    def adjustvertical(self, direction):
        msg = mq.Message({'id': MSG_ID_ADJUST, 'direction':int(direction), 'shift': self.keyShift, 'control':self.keyControl})
        self.mq_publisher.publish(msg)

    def telldownsample(self, direction):
        msg = mq.Message({'id': MSG_ID_DOWNSAMPLE, 'direction':direction, 'shift': self.keyShift})
        self.mq_publisher.publish(msg)

    def pickline(self,theline):
        # on the pick event, find the orig line corresponding to the
        # legend proxy line, and toggle the visibility
        origline,legline,channum = self.lined[theline]
        if self.db: print(("picked",theline,"for channum",channum))
        if hasattr(self,'selectedlegline'):
            if self.selectedorigline.get_visible(): self.selectedlegline.set_linewidth(2.0)
            else: self.selectedlegline.set_linewidth(1.0)
        legline.set_linewidth(4.0)
        self.selectedlegline=legline; self.selectedorigline=origline # remember them so we can set it back to normal later when we pick something else
        if channum < HAAS_NUM_BOARD*HAAS_NUM_CHAN_PER_BOARD: # it's an ADC channel (not a max10adc channel or other thing)
            if self.db: print("picked a real ADC channel")
            msg = mq.Message({'id': MSG_ID_SELECT_CHANNEL, 'selectedchannel': channum})
            self.mq_publisher.publish(msg)
            if self.keyShift:
                msg = mq.Message({'id': MSG_ID_SELECT_TRIGGER_CHANNEL, 'triggerchannel': channum})
                self.mq_publisher.publish(msg)

        else:
            if self.db: print("picked a max10 ADC channel")
            self.selectedmax10channel=channum - HAAS_NUM_BOARD*HAAS_NUM_CHAN_PER_BOARD
        # self.drawtext()

    def onpick(self,event):
        if event.mouseevent.button==1: #left click
            if self.keyControl: self.togglechannel(event.artist)
            else:self.pickline(event.artist)
            self.canvas.draw()

    def onclick(self,event):
        try:
            if event.button==1: #left click
                pass
            if event.button==2: #middle click
                msg = mq.Message({'id': MSG_ID_MOUSE_M_CLICK, 'event':event, 'shift':self.keyShift, 'yscale':self.yscale})
                if self.keyShift:# if shift is held, turn off threshold2
                    self.otherlines[2].set_visible(False)
                else:
                    self.hline2 = event.ydata
                    self.otherlines[2].set_visible(True) # starts off being hidden, so now show it!
                    self.otherlines[2].set_data( [self.min_x, self.max_x], [self.hline2, self.hline2] )
            if event.button==3: #right click

                msg = mq.Message({'id': MSG_ID_MOUSE_R_CLICK, 'event':event, 'xscaling':self.xscaling, 'yscale':self.yscale})
                self.mq_publisher.publish(msg)

                self.vline = event.xdata
                self.otherlines[0].set_visible(True)
                self.otherlines[0].set_data( [self.vline, self.vline], [self.min_y, self.max_y] ) # vertical line showing trigger time
                self.hline = event.ydata
                self.otherlines[1].set_data( [self.min_x, self.max_x], [self.hline, self.hline] ) # horizontal line showing trigger threshold
            print(('%s click: button=%d, x=%d, y=%d, xdata=%f, ydata=%f' % ('double' if event.dblclick else 'single', event.button, event.x, event.y, event.xdata, event.ydata)))
            return
        except TypeError: pass


    doxyplot=False
    drawnxy=False
    xychan=0
    def drawxyplot(self,xdatanew,ydatanew,thechan):
        print("drawxyplot")
        if thechan==self.xychan: self.xydataforxaxis=ydatanew #the first channel will define the info on the x-axis
        if thechan==(self.xychan+1):
            if not self.drawnxy: # got to make the plot window the first time
                # self.figxy, self.ax = plt.subplots(1,1)
                # self.canvas.mpl_connect('close_event', self.handle_xy_close)
                self.drawnxy=True
                self.fig.set_size_inches(6, 6, forward=True)
                self.xyplot, = self.ax.plot(self.xydataforxaxis,ydatanew) #scatter
                self.canvas.set_window_title('XY display of channels '+str(self.xychan)+' and '+str(self.xychan+1))
                self.ax.set_xlabel('Channel '+str(self.xychan)+' Volts')
                self.ax.set_ylabel('Channel '+str(self.xychan+1)+' Volts')
                self.ax.set_xlim(self.min_y, self.max_y)
                self.ax.set_ylim(self.min_y, self.max_y)
                self.ax.grid()
            #redraw the plot
            self.canvas.set_window_title('XY display of channels '+str(self.xychan)+' and '+str(self.xychan+1))
            self.ax.set_xlabel('Channel '+str(self.xychan)+' Volts')
            self.ax.set_ylabel('Channel '+str(self.xychan+1)+' Volts')
            self.xyplot.set_data(self.xydataforxaxis, ydatanew)
            self.canvas.draw()
            print("drawxyplot, self.canvas.draw")

    def on_running(self, theydata, board, downsample): #update data for main plot for a board
        if board<0: #hack to tell it the max10adc channel
            chantodraw=-board-1 #draw chan 0 first (when board=-1)
            posi=chantodraw+HAAS_NUM_BOARD*HAAS_NUM_CHAN_PER_BOARD
            if self.db: print((time.time()-self.oldtime,"drawing line",posi))
            #if self.db: print "ydata[0]=",theydata[0]
            xdatanew=(self.xsampdata-HAAS_NUM_SAMPLES/2.)*(1000.0*pow(2,max(downsample,0))/HAAS_CLKRATE/self.xscaling) #downsample isn't less than 0 for xscaling
            ydatanew=theydata*(3.3/256)#full scale is 3.3V
            if len(self.lines)>posi: # we may not be drawing, so check!
                self.lines[posi].set_xdata(xdatanew)
                self.lines[posi].set_ydata(ydatanew)
            self.xydataslow[chantodraw][0]=xdatanew
            self.xydataslow[chantodraw][1]=ydatanew
        else:
            if self.dologicanalyzer and self.logicline1>=0 and hasattr(self,"ydatalogic"): #this draws logic analyzer info
                xlogicshift=12.0/pow(2,max(downsample,0)) # shift the logic analyzer data to the right by this number of samples (to account for the ADC delay) #downsample isn't less than 0 for xscaling
                xdatanew = (self.xdata+xlogicshift-HAAS_NUM_SAMPLES/2.)*(1000.0*pow(2,max(downsample,0))/HAAS_CLKRATE/self.xscaling) #downsample isn't less than 0 for xscaling
                for l in np.arange(8):
                    a=np.array(self.ydatalogic,dtype=np.uint8)
                    b=np.unpackbits(a)
                    bl=b[7-l::8] # every 8th bit, starting at 7-l
                    ydatanew = bl*.3 + (l+1)*3.2/8. # scale it and shift it
                    self.lines[l+self.logicline1].set_xdata(xdatanew)
                    self.lines[l+self.logicline1].set_ydata(ydatanew)
            for l in np.arange(HAAS_NUM_CHAN_PER_BOARD): #this draws the 4 fast ADC data channels for each board
                thechan=l+(HAAS_NUM_BOARD-board-1)*HAAS_NUM_CHAN_PER_BOARD
                #if self.db: print time.time()-self.oldtime,"drawing adc line",thechan
                if len(theydata)<=l: print(("don't have channel",l,"on board",board)); return
                # if self.egs.dooversample[thechan]==1: # account for oversampling
                #     xdatanew = (self.xdata2-HAAS_NUM_SAMPLES)*(1000.0*pow(2,max(downsample,0))/HAAS_CLKRATE/self.xscaling/2.) #downsample isn't less than 0 for xscaling
                #     theydata2=np.concatenate([theydata[l],theydata[l+2]]) # concatenate the 2 lists
                #     ydatanew=(127-theydata2)*(self.yscale/256.) # got to flip it, since it's a negative feedback op amp
                # elif self.egs.dooversample[thechan]==9: # account for over-oversampling
                #     xdatanew = (self.xdata4-HAAS_NUM_SAMPLES*2)*(1000.0*pow(2,max(downsample,0))/HAAS_CLKRATE/self.xscaling/4.) #downsample isn't less than 0 for xscaling
                #     theydata4=np.concatenate([theydata[l],theydata[l+1],theydata[l+2],theydata[l+3]]) # concatenate the 4 lists
                #     ydatanew=(127-theydata4)*(self.yscale/256.) # got to flip it, since it's a negative feedback op amp
                # else:
                xdatanew = (self.xdata-HAAS_NUM_SAMPLES/2.)*(1000.0*pow(2,max(downsample,0))/HAAS_CLKRATE/self.xscaling) #downsample isn't less than 0 for xscaling
                ydatanew=(127-theydata[l])*(self.yscale/256.) # got to flip it, since it's a negative feedback op amp
                if self.ydatarefchan>=0: ydatanew -= (127-theydata[self.ydatarefchan])*(self.yscale/256.) # subtract the board's reference channel ydata from this channel's ydata
                if self.sincresample>0:
                    (ydatanew,xdatanew) = resample(ydatanew, len(xdatanew)*self.sincresample, t = xdatanew)
                    xdatanew = xdatanew[1*self.sincresample:len(xdatanew)*self.sincresample]
                    ydatanew = ydatanew[1*self.sincresample:len(ydatanew)*self.sincresample]
                else:
                    xdatanew = xdatanew[1:len(xdatanew)]
                    ydatanew = ydatanew[1:len(ydatanew)]
                # if self.egs.dooversample[thechan]==1: # account for oversampling, take the middle-most section
                #     if self.sincresample>0:
                #         self.xydata[l][0]=xdatanew[self.sincresample+HAAS_NUM_SAMPLES*self.sincresample/2:3*HAAS_NUM_SAMPLES*self.sincresample/2:1] # for printing out or other analysis
                #         self.xydata[l][1]=ydatanew[self.sincresample+HAAS_NUM_SAMPLES*self.sincresample/2:3*HAAS_NUM_SAMPLES*self.sincresample/2:1]
                #     else:
                #         self.xydata[l][0]=xdatanew[1+HAAS_NUM_SAMPLES/2:3*HAAS_NUM_SAMPLES/2:1] # for printing out or other analysis
                #         self.xydata[l][1]=ydatanew[1+HAAS_NUM_SAMPLES/2:3*HAAS_NUM_SAMPLES/2:1]
                # elif self.egs.dooversample[thechan]==9: # account for over-oversampling, take the middle-most section
                #      if self.sincresample>0:
                #          self.xydata[l][0]=xdatanew[self.sincresample+3*HAAS_NUM_SAMPLES*self.sincresample/2:5*HAAS_NUM_SAMPLES*self.sincresample/2:1] # for printing out or other analysis
                #          self.xydata[l][1]=ydatanew[self.sincresample+3*HAAS_NUM_SAMPLES*self.sincresample/2:5*HAAS_NUM_SAMPLES*self.sincresample/2:1]
                #      else:
                #         self.xydata[l][0]=xdatanew[1+3*HAAS_NUM_SAMPLES/2:5*HAAS_NUM_SAMPLES/2:1] # for printing out or other analysis
                #         self.xydata[l][1]=ydatanew[1+3*HAAS_NUM_SAMPLES/2:5*HAAS_NUM_SAMPLES/2:1]
                # else: # the full data is stored
                self.xydata[l][0]=xdatanew # for printing out or other analysis
                self.xydata[l][1]=ydatanew
                if len(self.lines)>thechan and self.domaindrawing: # we may not be drawing, so check!
                    self.lines[thechan].set_xdata(xdatanew)
                    self.lines[thechan].set_ydata(ydatanew)
                if self.domeasure:
                    self.Vmean[thechan] = np.mean(ydatanew)
                    self.Vrms[thechan] = np.sqrt(np.mean((ydatanew-self.Vmean[thechan])**2))
                    gain=1
                    if self.gain[thechan]==0: gain*=10
                    if self.supergain[thechan]==0: gain*=100
                    if gain>1:
                        self.Vmean[thechan]/=gain
                        self.Vrms[thechan]/=gain
                    if self.fitline1>-1 and thechan==0: # optional risetime fit for channel 0
                        def fit_rise(x,a,bottom,b,top): # a function for fitting to find risetime
                            val=bottom+(x-a)*(top-bottom)/(b-a)
                            inbottom=(x<=a)
                            val[inbottom]=bottom
                            intop=(x>=b)
                            val[intop]=top
                            return val
                        try:
                            x2=xdatanew[(xdatanew>-.1) & (xdatanew<.1)] # only fit in range -.1 to .1 (us)
                            y2=ydatanew[(xdatanew>-.1) & (xdatanew<.1)]
                            popt, pcov = scipy.optimize.curve_fit(fit_rise,x2,y2,bounds=([-.1,-4,-0.05,0],[0.05,0,.1,4])) #and note these bounds - top must be>0 and bottom<0 !
                            self.lines[self.fitline1].set_xdata(x2)
                            self.lines[self.fitline1].set_ydata( fit_rise(x2, *popt) )
                            print(("risetime = ",1000*0.8*(popt[2]-popt[0]),"ns")) # from 10-90% is 0.8 on the line - don't forget to correct for x2 or x4 oversampling!
                        except:
                            print("fit exception!")
                if self.doxyplot and (thechan==self.xychan or thechan==(self.xychan+1)): self.drawxyplot(xdatanew,ydatanew,thechan)# the xy plot
                # self.drawtext()
                # if self.recorddata and thechan==self.recorddatachan: self.dopersistplot(xdatanew,ydatanew)# the persist shaded plot

                # if thechan==self.refsinchan-1 and self.reffreq==0: self.oldchanphase=-1.; self.fittosin(xdatanew, ydatanew, thechan) # first fit the previous channel, for comparison
                # elif thechan==self.refsinchan and self.reffreq==0: self.reffreq = self.fittosin(xdatanew, ydatanew, thechan) # then fit for the ref freq and store the result

                # if self.autocalibchannel>=0 and thechan==self.autocalibchannel: self.autocalibrate(thechan,ydatanew)
                self.canvas.draw()
    def setlogicanalyzer(self, dologicanalyzer):
        #tell it start/stop doing logic analyzer
        self.dologicanalyzer = dologicanalyzer
        if self.dologicanalyzer:
            if len(self.lines)>=8+self.logicline1: # check that we're drawing
                for l in np.arange(8): self.lines[l+self.logicline1].set_visible(True)
        else:
            if len(self.lines)>=8+self.logicline1: # check that we're drawing
                for l in np.arange(8): self.lines[l+self.logicline1].set_visible(False)
        print(("dologicanalyzer is now",self.dologicanalyzer))

    def disable_otherline(self, n):
        self.otherlines[n].set_visible(False)
