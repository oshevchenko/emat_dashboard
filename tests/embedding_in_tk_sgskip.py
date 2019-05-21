"""
===============
Embedding In Tk
===============

"""

import tkinter
from tkinter import Frame, Tk, Button,Canvas

from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, NavigationToolbar2Tk)
# Implement the default Matplotlib key bindings.
from matplotlib.backend_bases import key_press_handler
from matplotlib.figure import Figure

import numpy as np

canvas_extents = (400, 400)
world_extents = (2000.0, 2000.0)
# The extents of the sensor canvas.
sensor_canvas_extents = canvas_extents
root = tkinter.Tk()
root.wm_title("Embedding in Tk")

fig = Figure(figsize=(4, 4), dpi=100)
t = np.arange(0, 3, .01)
fig.add_subplot(111).plot(t, 2 * np.sin(2 * np.pi * t))

frame1 = Frame(root)
frame1.pack(side=tkinter.BOTTOM)
frame2 = Frame(root)
frame2.pack(side=tkinter.TOP)

world_canvas = Canvas(frame1,width=canvas_extents[0],height=canvas_extents[1],bg="white")
world_canvas.pack(side=tkinter.LEFT)
sensor_canvas = Canvas(frame1,width=sensor_canvas_extents[0],height=sensor_canvas_extents[1],bg="white")
sensor_canvas.pack(side=tkinter.RIGHT)

canvas = FigureCanvasTkAgg(fig, master=frame1)  # A tk.DrawingArea.
canvas.draw()
canvas.get_tk_widget().pack(side=tkinter.BOTTOM, fill=tkinter.BOTH, expand=1)

toolbar = NavigationToolbar2Tk(canvas, frame1)
toolbar.update()
canvas._tkcanvas.pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=1)


def on_key_press(event):
    print("you pressed {}".format(event.key))
    key_press_handler(event, canvas, toolbar)


canvas.mpl_connect("key_press_event", on_key_press)


def _quit():
    root.quit()     # stops mainloop
    root.destroy()  # this is necessary on Windows to prevent
                    # Fatal Python Error: PyEval_RestoreThread: NULL tstate

button = tkinter.Button(master=frame2, text="Quit", command=_quit)
button.pack(side=tkinter.RIGHT)

tkinter.mainloop()
# If you put root.destroy() here, it will cause an error if the window is
# closed with the window manager.
