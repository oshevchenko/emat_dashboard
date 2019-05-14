import tkinter as tk
from matplotlib.figure import Figure
from numpy import arange, sin, pi
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import numpy as np

class EmatPage(tk.Frame) :

    def __init__(self, parent, controller, egs):
        tk.Frame.__init__(self,parent)
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
        # self.canvas.mpl_connect('pick_event', self.onpick)
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

     # Number of Haasoscope boards to read out

    #[(0,110),(0,118),(1,110),(1,118)] #max10adc channels to draw (board, channel on board), channels: 110=ain1, 111=pin6, ..., 118=pin14, 119=temp
     # 0 would skip 2**0=1 byte each time, i.e. send all bytes, 10 is good for lockin mode (sends just 4 samples)
     # number of high-speed ADC channels on a Haasoscope board
