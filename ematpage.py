import message_queue as mq
import tkinter as tk
from matplotlib.figure import Figure
from numpy import arange, sin, pi
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import numpy as np

class EmatPage(tk.Frame) :
    keyResample=False
    keysettriggertime=False
    keySPI=False
    keyi2c=False
    keyLevel=False
    keyShift=False
    keyAlt=False
    keyControl=False

    def __init__(self, parent, controller, egs):
        tk.Frame.__init__(self,parent)
        self.mq_adapter1 = mq.Adapter('serial_to_draw')
        self.mq_subscriber = mq.Subscriber(self.mq_adapter1)
        # >>>>>>>>>>>>>>>>>>>>>>>>>
        self.chtext = "Ch." #the text in the legend for each channel
        self.lines = []
        self.fitline1 = -1 # set to >-1 to draw a risetime fit
        self.logicline1 = -1 # to remember which is the first logic analyzer line
        self.otherlines = []
        self.texts = []
        # >>>>>>>>>>>>>>>>>>>>>>>>>
        self.grid(row=1, column=0, columnspan=4, sticky="nsew")
        self.db = True
        ###Matplotlib
        self.egs = egs
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
                            command=lambda: controller.on_key_press())
        button_hv_on.grid(row=4, column=2, padx=5, pady=5, sticky='nsew')

        button_hv_off = tk.Button(self, text="OFF",
                            command=lambda: controller.on_key_press())
        button_hv_off.grid(row=5, column=2, padx=5, pady=5,  sticky='nsew')

        button_pulse = tk.Button(self, text="PULSE",
                            command=lambda: controller.on_key_press())
        button_pulse.grid(row=6, column=1, columnspan=2, padx=5, pady=5, sticky='nsew')


        ###Lab
        textbox1 = tk.Entry(self)
        textbox1.grid(row=7, column=0, columnspan=3, sticky='nsew')
        textbox1.insert('end', "Hello Emat!")

    firstdrawtext=True
    needtoredrawtext=False
    havereadswitchdata=False
    def chantext(self):
        text ="Channel: "+str(self.egs.selectedchannel)
        if self.egs.ydatarefchan>=0: text += " - ref "+str(int(self.egs.ydatarefchan))
        text +="\nLevel="+str(int(self.egs.chanlevel[self.egs.selectedchannel]))
        if self.egs.acdc[self.egs.selectedchannel]:
            text +="\nDC coupled"
        else:
            text +="\nAC coupled"
        chanonboard = self.egs.selectedchannel%self.egs.num_chan_per_board
        theboard = self.egs.num_board-1-self.egs.selectedchannel/self.egs.num_chan_per_board
        # if self.havereadswitchdata:
        #     if self.testBit(self.egs.switchpos[theboard],chanonboard):
        #         text += ", 1M"
        #     else:
        #         text += ", 50"
        text +="\nTriggering="+str(self.egs.trigsactive[self.egs.selectedchannel])
        if self.egs.domeasure:
            if abs(self.egs.Vmean[self.egs.selectedchannel])>.9: text +="\nMean={0:1.3g} V".format(self.egs.Vmean[self.egs.selectedchannel])
            else: text +="\nMean={0:1.3g} mV".format(1000.*self.egs.Vmean[self.egs.selectedchannel])
            if abs(self.egs.Vrms[self.egs.selectedchannel])>.9: text +="\nRMS={0:1.3g} V".format(self.egs.Vrms[self.egs.selectedchannel])
            else: text +="\nRMS={0:1.3g} mV".format(1000.*self.egs.Vrms[self.egs.selectedchannel])
        if chanonboard<2:
            if self.egs.dooversample[self.egs.selectedchannel]==1: text+= "\nOversampled x2"
            if self.egs.dooversample[self.egs.selectedchannel]==9: text+= "\nOversampled x4"
        else:
            if self.egs.selectedchannel>1 and self.egs.dooversample[self.egs.selectedchannel-2]: text+= "\nOff (oversamp)"
        if len(self.egs.max10adcchans)>0:
            text+="\n"
            text+="\nSlow chan: "+str(self.selectedmax10channel)
        return text

    def drawtext(self):
        height = 0.25 # height up from bottom to start drawing text
        xpos = 1.02 # how far over to the right to draw
        if self.firstdrawtext:
            self.texts.append(self.ax.text(xpos, height, self.chantext(),horizontalalignment='left', verticalalignment='top',transform=self.ax.transAxes))
            self.firstdrawtext=False
        else:
            self.texts[0].remove()
            self.texts[0]=(self.ax.text(xpos, height, self.chantext(),horizontalalignment='left', verticalalignment='top',transform=self.ax.transAxes))
            #for txt in self.ax.texts: print txt # debugging
        self.needtoredrawtext=True
        self.canvas.draw()

    def setxaxis(self):
        xscale =  self.egs.num_samples/2.0*(1000.0*pow(2,self.egs.downsample)/self.egs.clkrate)
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
        self.ax.set_ylim(self.egs.min_y, self.egs.max_y)
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

    def on_launch_draw(self):
        plt.ion() #turn on interactive mode
        self.nlines = self.egs.num_chan_per_board*self.egs.num_board+len(self.egs.max10adcchans)
        if self.db: print(("nlines=",self.nlines))
        for l in np.arange(self.nlines):
            maxchan=l-self.egs.num_chan_per_board*self.egs.num_board
            c=(0,0,0)
            if maxchan>=0: # these are the slow ADC channels
                if self.egs.num_board>1:
                    board = int(self.egs.num_board-1-self.egs.max10adcchans[maxchan][0])
                    if board%4==0: c=(1-0.1*maxchan,0,0)
                    if board%4==1: c=(0,1-0.1*maxchan,0)
                    if board%4==2: c=(0,0,1-0.1*maxchan)
                    if board%4==3: c=(1-0.1*maxchan,0,1-0.1*maxchan)
                else:
                    c=(0.1*(maxchan+1),0.1*(maxchan+1),0.1*(maxchan+1))
                line, = self.ax.plot([],[], '-', label=str(self.egs.max10adcchans[maxchan]), color=c, linewidth=0.5, alpha=.5)
            else: # these are the fast ADC channels
                chan=l%4
                if self.egs.num_board>1:
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
        self.setxaxis()
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
        # self.canvas.mpl_connect('button_press_event', self.onclick)
        # self.canvas.mpl_connect('key_press_event', self.onpress)
        # self.canvas.mpl_connect('key_release_event', self.onrelease)
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
        self.drawtext()
        # self.canvas.mpl_connect('close_event', self.handle_main_close)
        self.canvas.draw()

    def toggletriggerchan(self,tp):
        # tell it to trigger or not trigger on a given channel
        # TODO: Add queue to send command over serial interface.
        self.egs.trigsactive[tp] = not self.egs.trigsactive[tp]

        origline,legline,channum = self.lined[tp]
        if self.egs.trigsactive[tp]: self.leg.get_texts()[tp].set_color('#000000')
        else: self.leg.get_texts()[tp].set_color('#aFaFaF')
        self.canvas.draw()
        if self.db: print(("Trigger toggled for channel",tp))


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
        if channum < self.egs.num_board*self.egs.num_chan_per_board: # it's an ADC channel (not a max10adc channel or other thing)
            if self.db: print("picked a real ADC channel")
            self.egs.selectedchannel=channum
            if self.keyShift: self.toggletriggerchan(channum)
        else:
            if self.db: print("picked a max10 ADC channel")
            self.selectedmax10channel=channum - num_board*num_chan_per_board
        self.drawtext()

    def onpick(self,event):
        if event.mouseevent.button==1: #left click
            if self.keyControl: self.togglechannel(event.artist)
            else:self.pickline(event.artist)
            self.canvas.draw()

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

    def on_running(self, theydata, board): #update data for main plot for a board
        if board<0: #hack to tell it the max10adc channel
            chantodraw=-board-1 #draw chan 0 first (when board=-1)
            posi=chantodraw+self.egs.num_board*self.egs.num_chan_per_board
            if self.db: print((time.time()-self.oldtime,"drawing line",posi))
            #if self.db: print "ydata[0]=",theydata[0]
            xdatanew=(self.xsampdata-self.egs.num_samples/2.)*(1000.0*pow(2,max(self.egs.downsample,0))/self.egs.clkrate/self.xscaling) #downsample isn't less than 0 for xscaling
            ydatanew=theydata*(3.3/256)#full scale is 3.3V
            if len(self.lines)>posi: # we may not be drawing, so check!
                self.lines[posi].set_xdata(xdatanew)
                self.lines[posi].set_ydata(ydatanew)
            self.xydataslow[chantodraw][0]=xdatanew
            self.xydataslow[chantodraw][1]=ydatanew
        else:
            if self.egs.dologicanalyzer and self.logicline1>=0 and hasattr(self,"ydatalogic"): #this draws logic analyzer info
                xlogicshift=12.0/pow(2,max(self.egs.downsample,0)) # shift the logic analyzer data to the right by this number of samples (to account for the ADC delay) #downsample isn't less than 0 for xscaling
                xdatanew = (self.egs.xdata+xlogicshift-self.egs.num_samples/2.)*(1000.0*pow(2,max(self.egs.downsample,0))/self.egs.clkrate/self.xscaling) #downsample isn't less than 0 for xscaling
                for l in np.arange(8):
                    a=np.array(self.ydatalogic,dtype=np.uint8)
                    b=np.unpackbits(a)
                    bl=b[7-l::8] # every 8th bit, starting at 7-l
                    ydatanew = bl*.3 + (l+1)*3.2/8. # scale it and shift it
                    self.lines[l+self.logicline1].set_xdata(xdatanew)
                    self.lines[l+self.logicline1].set_ydata(ydatanew)
            for l in np.arange(self.egs.num_chan_per_board): #this draws the 4 fast ADC data channels for each board
                thechan=l+(self.egs.num_board-board-1)*self.egs.num_chan_per_board
                #if self.db: print time.time()-self.oldtime,"drawing adc line",thechan
                if len(theydata)<=l: print(("don't have channel",l,"on board",board)); return
                if self.egs.dooversample[thechan]==1: # account for oversampling
                    xdatanew = (self.egs.xdata2-self.egs.num_samples)*(1000.0*pow(2,max(self.egs.downsample,0))/self.egs.clkrate/self.xscaling/2.) #downsample isn't less than 0 for xscaling
                    theydata2=np.concatenate([theydata[l],theydata[l+2]]) # concatenate the 2 lists
                    ydatanew=(127-theydata2)*(self.egs.yscale/256.) # got to flip it, since it's a negative feedback op amp
                elif self.egs.dooversample[thechan]==9: # account for over-oversampling
                    xdatanew = (self.egs.xdata4-self.egs.num_samples*2)*(1000.0*pow(2,max(self.egs.downsample,0))/self.egs.clkrate/self.xscaling/4.) #downsample isn't less than 0 for xscaling
                    theydata4=np.concatenate([theydata[l],theydata[l+1],theydata[l+2],theydata[l+3]]) # concatenate the 4 lists
                    ydatanew=(127-theydata4)*(self.egs.yscale/256.) # got to flip it, since it's a negative feedback op amp
                else:
                    xdatanew = (self.egs.xdata-self.egs.num_samples/2.)*(1000.0*pow(2,max(self.egs.downsample,0))/self.egs.clkrate/self.xscaling) #downsample isn't less than 0 for xscaling
                    ydatanew=(127-theydata[l])*(self.egs.yscale/256.) # got to flip it, since it's a negative feedback op amp
                    if self.egs.ydatarefchan>=0: ydatanew -= (127-theydata[self.egs.ydatarefchan])*(self.egs.yscale/256.) # subtract the board's reference channel ydata from this channel's ydata
                if self.egs.sincresample>0:
                    (ydatanew,xdatanew) = resample(ydatanew, len(xdatanew)*self.egs.sincresample, t = xdatanew)
                    xdatanew = xdatanew[1*self.egs.sincresample:len(xdatanew)*self.egs.sincresample]
                    ydatanew = ydatanew[1*self.egs.sincresample:len(ydatanew)*self.egs.sincresample]
                else:
                    xdatanew = xdatanew[1:len(xdatanew)]
                    ydatanew = ydatanew[1:len(ydatanew)]
                if self.egs.dooversample[thechan]==1: # account for oversampling, take the middle-most section
                    if self.egs.sincresample>0:
                        self.egs.xydata[l][0]=xdatanew[self.egs.sincresample+self.egs.num_samples*self.egs.sincresample/2:3*self.egs.num_samples*self.egs.sincresample/2:1] # for printing out or other analysis
                        self.egs.xydata[l][1]=ydatanew[self.egs.sincresample+self.egs.num_samples*self.egs.sincresample/2:3*self.egs.num_samples*self.egs.sincresample/2:1]
                    else:
                        self.egs.xydata[l][0]=xdatanew[1+self.egs.num_samples/2:3*self.egs.num_samples/2:1] # for printing out or other analysis
                        self.egs.xydata[l][1]=ydatanew[1+self.egs.num_samples/2:3*self.egs.num_samples/2:1]
                elif self.egs.dooversample[thechan]==9: # account for over-oversampling, take the middle-most section
                     if self.egs.sincresample>0:
                         self.egs.xydata[l][0]=xdatanew[self.egs.sincresample+3*self.egs.num_samples*self.egs.sincresample/2:5*self.egs.num_samples*self.egs.sincresample/2:1] # for printing out or other analysis
                         self.egs.xydata[l][1]=ydatanew[self.egs.sincresample+3*self.egs.num_samples*self.egs.sincresample/2:5*self.egs.num_samples*self.egs.sincresample/2:1]
                     else:
                        self.egs.xydata[l][0]=xdatanew[1+3*self.egs.num_samples/2:5*self.egs.num_samples/2:1] # for printing out or other analysis
                        self.egs.xydata[l][1]=ydatanew[1+3*self.egs.num_samples/2:5*self.egs.num_samples/2:1]
                else: # the full data is stored
                    self.egs.xydata[l][0]=xdatanew # for printing out or other analysis
                    self.egs.xydata[l][1]=ydatanew
                if len(self.lines)>thechan and self.egs.domaindrawing: # we may not be drawing, so check!
                    self.lines[thechan].set_xdata(xdatanew)
                    self.lines[thechan].set_ydata(ydatanew)
                if self.egs.domeasure:
                    self.egs.Vmean[thechan] = np.mean(ydatanew)
                    self.egs.Vrms[thechan] = np.sqrt(np.mean((ydatanew-self.egs.Vmean[thechan])**2))
                    gain=1
                    if self.egs.gain[thechan]==0: gain*=10
                    if self.egs.supergain[thechan]==0: gain*=100
                    if gain>1:
                        self.egs.Vmean[thechan]/=gain
                        self.egs.Vrms[thechan]/=gain
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

    def process_queue(self):
        while True:
            message = self.mq_subscriber.consume()
            if not message: break
            message_content = message.get_content_body()
            msg_id = message_content['id']
            print ("message id:", msg_id)
            if msg_id==1:
                ydata = message_content['ydata']
                bn = message_content['bn']
                self.on_running(ydata, bn)
            elif msg_id==2:
                self.drawtext()


        pass

     # Number of Haasoscope boards to read out

    #[(0,110),(0,118),(1,110),(1,118)] #max10adc channels to draw (board, channel on board), channels: 110=ain1, 111=pin6, ..., 118=pin14, 119=temp
     # 0 would skip 2**0=1 byte each time, i.e. send all bytes, 10 is good for lockin mode (sends just 4 samples)
     # number of high-speed ADC channels on a Haasoscope board
