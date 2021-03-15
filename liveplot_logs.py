# live plot system log files

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import matplotlib.dates as mpdates
from matplotlib import rcParams
rcParams['timezone'] = 'Canada/Eastern'
rcParams['font.family'] = 'sans-serif'
# rcParams['font.sans-serif'] = ['Lato']

from tkinter import filedialog
import tkinter as tk
import numpy as np

# pick the directory containing the log file
root_window = tk.Tk()
directory = filedialog.askdirectory(title="pick directory to log",initialdir="/home/vuthalab/Desktop/edm_data/logs/full_system/2021",parent=root_window)
root_window.destroy()
logfile = directory+"/system_log.txt"

## animated plot
num_points = 30000
plot_every = 1        # plot one out of every .. points
data = np.loadtxt(logfile,unpack=True)
data[0] = mpdates.epoch2num(data[0])   # convert to convenient matplotlib format
locator = mpdates.AutoDateLocator()
formatter = mpdates.ConciseDateFormatter(locator)

num_fields = len(data)-1    # number of plots to show
field_names = ["time", "$p$ [torr]", "$p$ [torr]","$V$ [volts]","$V$ [volts]","$Q_1$","$Q_2$","$Q_3$","$Q_4$","$T_1$ [K]","$T_2$ [K]","$T_3$ [K]","$T_4$ [K]","$T_5$ [K]","$T_6$ [K]","$T_7$ [K]","$T_8$ [K]"]
labels=["","agilent","hornet","pd","trans","saph heat", "coll heat", "45K heat", "4K heat", "sapphire mount","collimator","bottom hs","buffer cell","4K sorb","45K sorb","45K plate","4K plate"]
# labels=["","","","north HS", "buffer cell", "45k plate", "4k plate"]
traces = [0]*(num_fields)
fig, axes = plt.subplots(nrows=num_fields,sharex=True,figsize=(10,8))


for i in range(num_fields):
    traces[i], = axes[i].plot_date(data[0][-num_points::plot_every],data[i+1][-num_points::plot_every],
                                    color=f'C{i}',
                                    linestyle='solid',
                                    lw=2,marker='None',
                                    label=labels[i+1])
    axes[i].set_ylabel(field_names[i+1])
    axes[i].legend(loc='upper left')
    axes[i].margins(0,0.3)
plt.gca().xaxis.set_major_formatter(formatter)
axes[0].set_yscale('log')
axes[1].set_yscale('log')
plt.tight_layout()

def animate(i):
    # update data
    data = np.loadtxt(logfile,unpack=True)
    data[0] = mpdates.epoch2num(data[0])   # convert to convenient matplotlib format
    for i in range(num_fields):
        traces[i].set_xdata(data[0][-num_points::plot_every])
        traces[i].set_ydata(data[i+1][-num_points::plot_every])
        axes[i].relim()
        axes[i].autoscale_view()
    return traces

ani = FuncAnimation(fig,animate,interval=500)  # interval is in ms
plt.show()