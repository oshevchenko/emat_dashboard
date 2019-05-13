import matplotlib
matplotlib.use('TkAgg')

import tkinter as tk
# from tkinter import tk

from numpy import arange, sin, pi
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
# implement the default mpl key bindings
#from matplotlib.backend_bases import key_press_handler
from matplotlib.figure import Figure

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
                            command= lambda: self.show_frame(EmatPage) )
        button2 = tk.Button(container, text="Plot2",
                            command= lambda: self.show_frame(Page1) )
        button3 = tk.Button(container, text="Plot3",
                            command= lambda: self.show_frame(Page1) )
        button4 = tk.Button(container, text="Plot4",
                            command= lambda: self.show_frame(Page1) )

        button1.grid(row=0, column=0,  sticky='nsew')
        ###Button Plot2
        button2.grid(row=0, column=1,  sticky='nsew')
        ###Button Plot3
        button3.grid(row=0, column=2,  sticky='nsew')
        ###Button Plot4
        button4.grid(row=0, column=3,  sticky='nsew')


        self.frames = {} #dic

        for F in (EmatPage,):#, Page1, Page2, Page3):
            frame = F(container, self)
            self.frames[F] = frame
            # frame.grid(row=1, column=0, columnspan=4, sticky="nsew")

        self.show_frame(EmatPage)

    def show_frame(self, cont):

        frame = self.frames[cont]
        frame.tkraise()

    def on_key_press(self):
        print("Not implemented")



class EmatPage(tk.Frame) :

    def __init__(self, parent, controller):
        tk.Frame.__init__(self,parent)
        self.grid(row=1, column=0, columnspan=4, sticky="nsew")

        ###Matplotlib

        f = Figure(figsize=(5, 5), dpi=100)
        a = f.add_subplot(111)
        t = arange(0.0, 3.0, 0.01)
        s = sin(2*pi*t)

        a.plot(t, s)

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


        canvas = FigureCanvasTkAgg(f, master=fr)
        canvas.draw()
        canvas.get_tk_widget().pack()

        toolbar = NavigationToolbar2Tk(canvas, fr)
        toolbar.update()
        canvas._tkcanvas.pack()

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

app = EmatGUI()
app.mainloop()