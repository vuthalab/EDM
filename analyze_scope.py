import datetime

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mpdates
from matplotlib import rcParams
rcParams['timezone'] = 'Canada/Eastern'
rcParams['font.family'] = 'sans-serif'

from tkinter import filedialog
import tkinter as tk


print('Opening file dialog...')
root_window = tk.Tk()
filepath = filedialog.askopenfile(
    title="Pick file to log",
    initialdir="/home/vuthalab/Desktop/edm_data/logs/scope/",
    filetypes=[('Text Files', '*.txt')],
    parent=root_window
).name
root_window.destroy()
print('Logging', filepath)


times = []
dips = []
peak_locs = []
with open(filepath, 'r') as f:
    time_offset, time_scale = map(float, next(f).split())
    for line in f:
        time, *voltages = line.split()
        time = float(time)
        voltages = np.array([float(x) for x in voltages])

        dip = 1 - np.min(voltages) / np.max(voltages)
        peak_loc = 6*time_scale*(np.argmin(voltages)/len(voltages) - 0.5) + time_offset

        times.append(time)
        dips.append(dip)
        peak_locs.append(peak_loc)

# Convert data
dips = 100 * np.array(dips)
dips = np.convolve(dips, np.ones(16) / 16, mode='same')

peak_locs = 1000 * np.array(peak_locs) # in ms

processed_times = [
    datetime.datetime.fromtimestamp(time) + datetime.timedelta(hours=4)
    for time in times
]

##### Plot Data #####
fig = plt.figure()
gs = fig.add_gridspec(2, hspace=0.1, left=0.1, right=0.95, top=0.95, bottom=0.05)
axes = gs.subplots(sharex=True, sharey=False)

axes[0].plot(processed_times, dips)
axes[0].set_ylabel('Dip Size (%)')

axes[1].plot(processed_times, peak_locs)
axes[1].set_ylabel('Peak Absorption Location (ms)')

# Dump data
data = np.array([times, dips, peak_locs])
np.savetxt(
    'scope-dump.txt', data,
    delimiter='\t',
    header='unix timestamp\tdip size (%)\tpeak absorption location (ms)'
)


# Format as dates
locator = mpdates.AutoDateLocator()
formatter = mpdates.ConciseDateFormatter(locator)
plt.gca().xaxis.set_major_formatter(formatter)

plt.xlabel('Time')
plt.show()
