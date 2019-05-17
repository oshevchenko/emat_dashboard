import HaasoscopeSerialLib
import imp
imp.reload(HaasoscopeSerialLib) # in case you changed it, and to always load some defaults
import Structure
from Structure import EmatGlobalStruct
from ematpage import EmatPage
import time, sys
from serial import SerialException
import HaasoscopeStateMachine
from HaasoscopeStateMachine import HaasoscopeStateMachine as HSM
#Some options
#HaasoscopeLib.num_board = 2 # Number of Haasoscope boards to read out (default is 1)
#HaasoscopeLib.ram_width = 12 # width in bits of sample ram to use (e.g. 9==512 samples (default), 12(max)==4096 samples) (min is 2)
#HaasoscopeLib.max10adcchans = [(0,110),(0,118),(1,110),(1,118)] #max10adc channels to draw (board, channel on board), channels: 110=ain1, 111=pin6, ..., 118=pin14, 119=temp # default is none, []
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('TkAgg')
import tkinter as tk
# from tkinter import tk
import numpy as np
from numpy import arange, sin, pi
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
# implement the default mpl key bindings
#from matplotlib.backend_bases import key_press_handler
from matplotlib.figure import Figure

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
UPDATE_RATE = 10

# num_board = 1 # Number of Haasoscope boards to read out
# ram_width = 9 # width in bits of sample ram to use (e.g. 9==512 samples, 12(max)==4096 samples)
# max10adcchans = []#[(0,110),(0,118),(1,110),(1,118)] #max10adc channels to draw (board, channel on board), channels: 110=ain1, 111=pin6, ..., 118=pin14, 119=temp
# sendincrement=0 # 0 would skip 2**0=1 byte each time, i.e. send all bytes, 10 is good for lockin mode (sends just 4 samples)
# num_chan_per_board = 4 # number of high-speed ADC channels on a Haasoscope board


class EmatGUI(tk.Tk):

    def __init__(self, *args, **kwargs):  #kwargs Dictionary, args - arguments
        tk.Tk.__init__(self, *args, **kwargs)
        tk.Tk.title(self, "EMAT")
        #tk.Tk.iconbitmap(self, default="C:\TuhhSq.ico")
        self.geometry('{}x{}'.format(800, 600))

        container = tk.Frame(self, bg='yellow')
        container.pack(side="top", fill="both", expand = True)
        container.grid_rowconfigure(1, weight=1)
        container.grid_columnconfigure(0, weight=1)
        container.grid_columnconfigure(1, weight=1)
        container.grid_columnconfigure(2, weight=1)
        container.grid_columnconfigure(3, weight=1)

        menubar = tk.Menu(container)
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="New Experiment", command= lambda: popupmsg("that is not defined yet"))
        filemenu.add_separator()
        filemenu.add_command(label="Run From a File", command= quit)
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command= quit)
        menubar.add_cascade(label="File", menu=filemenu)

        tk.Tk.config(self,menu=menubar)


        button1 = tk.Button(container, text="EMAT",
                            command= lambda: self.show_frame() )
        button2 = tk.Button(container, text="Plot2",
                            command= lambda: self.show_frame() )
        button3 = tk.Button(container, text="Plot3",
                            command= lambda: self.show_frame() )
        button4 = tk.Button(container, text="Plot4",
                            command= lambda: self.show_frame() )

        button1.grid(row=0, column=0,  sticky='nsew')
        ###Button Plot2
        button2.grid(row=0, column=1,  sticky='nsew')
        ###Button Plot3
        button3.grid(row=0, column=2,  sticky='nsew')
        ###Button Plot4
        button4.grid(row=0, column=3,  sticky='nsew')


        self.frames = {} #dic

        for F in (EmatPage,):#, Page1, Page2, Page3):
            frame = F(container, self, egs)
            self.frames[F] = frame
            # frame.grid(row=1, column=0, columnspan=4, sticky="nsew")
        self.frame = self.frames[EmatPage]
        self.hsl = HaasoscopeSerialLib.Haasoscope()
        self.hsl.construct()
        if not self.hsl.setup_connections(): sys.exit()
        if not self.hsl.init(1): sys.exit()
        # self.hsl.on_launch()
        # egs.downsample=self.hsl.downsample
        # egs.min_y = self.hsl.min_y
        # egs.max_y = self.hsl.max_y
        egs.selectedchannel = self.hsl.selectedchannel
        # egs.ydatarefchan=self.hsl.ydatarefchan
        # egs.chanlevel = self.hsl.chanlevel
        # egs.acdc = self.hsl.acdc
        egs.havereadswitchdata = self.hsl.havereadswitchdata
        # egs.switchpos = self.hsl.switchpos
        # egs.trigsactive = self.hsl.trigsactive
        # egs.Vmean = self.hsl.Vmean
        # egs.Vrms = self.hsl.Vrms
        # egs.domeasure = self.hsl.domeasure
        # egs.dooversample = self.hsl.dooversample
        # egs.dologicanalyzer = self.hsl.dologicanalyzer
        # egs.xdata = self.hsl.xdata
        # egs.xdata2 = self.hsl.xdata2
        # egs.xdata4 = self.hsl.xdata4
        # egs.yscale = self.hsl.yscale
        # egs.sincresample = self.hsl.sincresample
        # egs.xydata = self.hsl.xydata
        # egs.domaindrawing = self.hsl.domaindrawing
        # egs.gain = self.hsl.gain
        # egs.supergain = self.hsl.supergain
        self.hsm=HSM(self.frame, self.hsl)
        self.updater()

    def show_frame(self):
        self.frame.tkraise()

    def on_key_press(self):
        print("Not implemented")

    def updater(self):
        # print("Tick.")
        if not self.hsl.getchannels(1): print("Tick.")
        self.hsm.process_queue()
        self.after(UPDATE_RATE, self.updater)





egs=EmatGlobalStruct(num_board=1, ram_width=9, max10adcchans=[], sendincrement=0, num_chan_per_board=4, clkrate=125.0)
# egs=EmatGlobalStruct(num_board=1, ram_width=9, sendincrement=0, num_chan_per_board=4)
# egs=EmatGlobalStruct(num_board=1, ram_width=9, sendincrement=0, num_chan_per_board=4)
print(("egs.num_board=",egs.num_board))
print(("egs.num_samples=",egs.num_samples))
# d = HaasoscopeSerialLib.Haasoscope()
# d.construct()
# if not d.setup_connections(): sys.exit()
# if not d.init(): sys.exit()
# d.on_launch()

app = EmatGUI()
app.mainloop()