# live plot system log files
from sh import tail
import time, json, datetime, math

import numpy as np

import matplotlib.pyplot as plt
import matplotlib.dates as mpdates
from matplotlib import rcParams
rcParams['timezone'] = 'Canada/Eastern'
rcParams['font.family'] = 'sans-serif'
rcParams.update({'font.size': 8})

from tkinter import filedialog
import tkinter as tk

MINUTE = 60
HOUR = 60 * MINUTE

##### PARAMETERS #####
# duration to plot.
duration = 2 * HOUR 

# skip every x points.
skip_points = 1

# how fast the publisher is
publisher_rate = 0.5 # Hertz

# Map from plot labels (name, unit) to paths in data
# Uncomment any fields you want to see.
# Traces will be grouped by units. (You can 'hack' this by putting spaces in the units.)
fields = {
    ('pressure', 'torr'): ('pressures', 'chamber'),

    ('buffer flow', 'sccm'): ('flows', 'cell'),
    ('neon flow', 'sccm'): ('flows', 'neon'),

    ('reflection', 'V'): ('voltages', 'AIN1'),

    ('transmission', 'V '): ('voltages', 'AIN2'),

#    ('frequency', 'GHz'): ('frequencies', 'BaF_Laser'),

    ('saph heat', 'W'): ('heaters', 'heat saph'),
    ('collimator heat', 'W'): ('heaters', 'heat coll'),
    ('45K heat', 'W'): ('heaters', 'srb45k out'),
    ('4K heat', 'W'): ('heaters', 'srb4k out'),

    ('bottom hs', 'K'): ('temperatures', 'bott hs'),
    ('buffer cell', 'K'): ('temperatures', 'cell'),
    ('45K sorb', 'K'): ('temperatures', 'srb45k'),
    ('45K plate', 'K'): ('temperatures', '45k plate'),

    ('sapphire mount', 'K '): ('temperatures', 'saph'),
    ('collimator', 'K '): ('temperatures', 'coll'),
    ('4K sorb', 'K '): ('temperatures', 'srb4k'),
    ('4K plate', 'K '): ('temperatures', '4k plate'),
}

axis_labels = [
    'torr',
    'sccm',
    'V',
    'V ',
    'W',
    'K',
    'K '
]



##### BEGIN CODE #####
# pick the directory containing the log file

#print('Opening file dialog...')
#root_window = tk.Tk()
#filepath = filedialog.askopenfilename(
#    title="Pick file to log",
#    initialdir="/home/vuthalab/Desktop/edm_data/logs/system_logs/",
#    filetypes=[('Text Files', '*.txt')],
#    parent=root_window
#)
#root_window.destroy()
#print('Logging', filepath)

filepath = '/home/vuthalab/Desktop/edm_data/logs/system_logs/continuous.txt'


###### initial plot #####
num_points = round(publisher_rate * duration / skip_points)
print(f'Showing last {num_points * skip_points} points (skip every {skip_points}).')
plt.ion()
fig = plt.figure(figsize=(10,8))
gs = fig.add_gridspec(
    len(axis_labels),
    hspace=0.1,
    left=0.1, right=0.95, top=0.95, bottom=0.05)
axes = gs.subplots(sharex=True, sharey=False)

# Initialize empty plots
graphs = []
for field in fields:
    name, unit = field

    i = axis_labels.index(unit)
    graph = axes[i].plot_date(
        num_points * [None], num_points * [None],
        linestyle='solid', lw=2,
        marker=None,
        label=name
    )[0]
    graphs.append(graph)

# Subplot tweaks
for axis, label in zip(axes, axis_labels):
    axis.legend(loc='upper left')
    axis.margins(0,0.1)
    axis.set_ylabel(label)


# set data formatter
locator = mpdates.AutoDateLocator()
formatter = mpdates.ConciseDateFormatter(locator)
plt.gca().xaxis.set_major_formatter(formatter)

axes[0].set_yscale('log') # set pressure as log

##### animated plot #####
times = np.array([datetime.datetime.now()] * num_points)
data = np.full((num_points, len(fields)), None)

last = 0
for i, line in enumerate(tail('-n', num_points * skip_points, '-f', filepath, _iter=True)):
    if i % skip_points == 0:
        timestamp, raw_data = line.split(']')
        timestamp = datetime.datetime.strptime(timestamp[1:], '%Y-%m-%d %H:%M:%S.%f')
        timestamp += datetime.timedelta(hours=4) # fix timezone (correct in logs, wrong on plot?)

        raw_data = json.loads(raw_data)

        # Filter out relevant fields
        processed_data = []
        for path in fields.values():
            value = raw_data
            for entry in path:
                value = value[entry]
            processed_data.append(value)

        # Add datapoint
        times[:-1] = times[1:]
        times[-1] = timestamp

        data[:-1] = data[1:]
        data[-1] = processed_data

    if (
        time.monotonic() - last < 1.5 # Avoid plot bottlenecking data read
        and
        abs(i/skip_points - num_points) > 2 # Update a few times manually to get the initial plot
    ): continue

    fig.canvas.flush_events()
    time.sleep(0.05)

    if i % skip_points == 0:
        # Plot data
        start_time = time.monotonic()
        for j, graph in enumerate(graphs):
            graph.set_xdata(times)
            graph.set_ydata(data[:, j])

        for axis in axes:
            axis.relim()
            axis.autoscale_view()

        fig.canvas.draw()

        pt_status = 'Running' if raw_data['pulsetube']['running'] else 'Off'
        fig.canvas.set_window_title(f'Pulse Tube {pt_status}')
        last = time.monotonic()

        print(f'Plot took {last - start_time:.3f} s')
