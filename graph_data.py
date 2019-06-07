import matplotlib as plt
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure

plt.use('TkAgg')

#Adapted for python3 and contec data graphing from
# https://stackoverflow.com/questions/43114508/can-a-pyqt-embedded-matplotlib-graph-be-interactive

import tkinter as tk 
from tkinter import ttk 

class My_GUI:

    def __init__(self,master):
        self.master=master
        master.title("Data from Contex")
        data = np.loadtxt("contec_data.csv", skiprows = 1, delimiter=',')
        time, spo2, pulse = data[:,0], data[:,2], data[:,3]
        minutes = time/60.
        f = Figure(figsize=(8,5), dpi=100)
        ax1 = f.add_subplot(111)

        # plot the spO2 values in red
        color = 'tab:red'
        ax1.set_xlabel('time (minutes)')
        ax1.set_ylabel('spO2', color=color)
        ax1.plot(minutes,spo2,label='spO2',color=color)
        ax1.tick_params(axis='y', labelcolor=color)
        ax1.set_ylim(85,100)

        ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis
        # plot the heart rate values in blue
        color = 'tab:blue'
        ax2.set_ylabel('Pulse', color=color)  # we already handled the x-label with ax1
        ax2.plot(minutes, pulse, color=color, label = 'pulse', picker=False)
        ax2.tick_params(axis='y', labelcolor=color,  color=color)
        ax2.set_xlabel('Time (sec)')
        ax2.set_ylim(30,120)


        canvas1=FigureCanvasTkAgg(f,master)
        canvas1.draw()
        canvas1.get_tk_widget().pack(side="top",fill='x',expand=True)
        f.canvas.mpl_connect('pick_event',self.onpick)

        toolbar=NavigationToolbar2Tk(canvas1,master)
        toolbar.update()
        toolbar.pack(side='top',fill='x')

        # Set "picker=True" in call to plot() to enable pick events
    def onpick(self,event):
        #do stuff
        print("My OnPick Event Worked!")
        return True

root=tk.Tk()
gui=My_GUI(root)
root.mainloop()
