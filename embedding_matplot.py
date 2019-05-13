import matplotlib
matplotlib.use('TkAgg')

import tkinter as tk
from tkinter import ttk

from numpy import arange, sin, pi
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
# implement the default mpl key bindings
#from matplotlib.backend_bases import key_press_handler
from matplotlib.figure import Figure

class moshGUI(tk.Tk):

    def __init__(self, *args, **kwargs):  #kwargs Dictionary, args - arguments
        tk.Tk.__init__(self, *args, **kwargs)
        tk.Tk.title(self, "mosh_GUI")
        #tk.Tk.iconbitmap(self, default="C:\TuhhSq.ico")

        container = tk.Frame(self, bg='yellow')
        container.pack(side="top", fill="both", expand = True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        menubar = tk.Menu(container)
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="New Experiment", command= lambda: popupmsg("that is not defined yet"))
        filemenu.add_separator()
        filemenu.add_command(label="Run From a File", command= quit)
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command= quit)
        menubar.add_cascade(label="File", menu=filemenu)

        tk.Tk.config(self,menu=menubar)

        self.frames = {} #dic

        for F in (Startpage,):#, Page1, Page2, Page3):
            frame = F(container, self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame(Startpage)

    def show_frame(self, cont):

        frame = self.frames[cont]
        frame.tkraise()


class Startpage(tk.Frame) :

    def __init__(self, parent, controller):
        tk.Frame.__init__(self,parent,bg='lavender')

        ###Button Plot1

        button1 = ttk.Button(self, text="Plot1",
                            command= lambda: controller.show_frame(Page1) )
        button1.grid(row=0, column=0)
        ###Button Plot2

        button2 = ttk.Button(self, text="Plot2",
                            command= lambda: controller.show_frame(Page1) )
        button2.grid(row=0, column=1)

        ###Button Plot3

        button3 = ttk.Button(self, text="Plot3",
                            command= lambda: controller.show_frame(Page1) )
        button3.grid(row=0, column=2)

        ###Button Plot4

        button4 = ttk.Button(self, text="Plot4",
                            command= lambda: controller.show_frame(Page1) )
        button4.grid(row=0, column=3)

        ###Matplotlib

        f = Figure(figsize=(5, 4), dpi=100)
        a = f.add_subplot(111)
        t = arange(0.0, 3.0, 0.01)
        s = sin(2*pi*t)

        a.plot(t, s)

        fr = tk.Frame(self)
        fr.grid(row=1, column=0, columnspan=4)

        canvas = FigureCanvasTkAgg(f, master=fr)
        canvas.draw()
        canvas.get_tk_widget().pack()

        toolbar = NavigationToolbar2Tk(canvas, fr)
        toolbar.update()
        canvas._tkcanvas.pack()

        ###Entry
        textbox1 = tk.Entry(self, width= 75)
        textbox1.grid(row=2, column=0, columnspan=4)
        textbox1.insert('end', "Hello World! --- Hello Tkinter! --- Hello Matplotlib!")

app = moshGUI()
app.mainloop()