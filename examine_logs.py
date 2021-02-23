# examine system log files
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
directory = filedialog.askdirectory(title="pick directory to log",initialdir="/home/vuthalab/Desktop/edm_data/logs/full_system/2020",parent=root_window)
root_window.destroy()
logfile = directory+"/pressure_log.txt"

## plot log file
data = np.loadtxt(logfile,unpack=True)
data[0] = mpdates.epoch2num(data[0])   # convert to convenient matplotlib format
locator = mpdates.AutoDateLocator()
formatter = mpdates.ConciseDateFormatter(locator)

plot_every = 50
num_fields = len(data)-1    # number of plots to show
field_names = ["time","$p$ [torr]","$T_1$ [K]","$T_2$ [K]","$T_3$ [K]","$T_4$ [K]"]
labels=["","","sapphire mount","4 K breadboard","4 K plate","40 K plate"]
traces = [0]*(num_fields)
fig, axes = plt.subplots(num_fields,sharex=True,figsize=(10,8))

for i in range(num_fields):
    traces[i], = axes[i].plot_date(data[0][::plot_every],data[i+1][::plot_every],
                                    color=f'C{i}',
                                    linestyle='solid',
                                    lw=2,marker='None',
                                    label=labels[i+1])
    axes[i].set_ylabel(field_names[i+1])
    axes[i].legend()
    axes[i].margins(0,0.1)
plt.gca().xaxis.set_major_formatter(formatter)
axes[0].set_yscale('log')
plt.tight_layout()
plt.show()