# live plot system log files
from sh import tail
import time, json, datetime, math
from collections import defaultdict

import numpy as np

import matplotlib.pyplot as plt
import matplotlib.dates as mpdates
from matplotlib import rcParams
rcParams['timezone'] = 'Canada/Eastern'
rcParams['font.family'] = 'sans-serif'
rcParams.update({'font.size': 8})

from tkinter import filedialog
import tkinter as tk

from uncertainties import ufloat


MINUTE = 60
HOUR = 60 * MINUTE

##### PARAMETERS #####
# duration to plot.
duration = 10 * MINUTE #2 * HOUR

# skip every x points.
skip_points = 1

# how fast the publisher is
publisher_rate = 1/2 # Hertz

# Map from plot labels (name, unit) to paths in data
# Uncomment any fields you want to see.
# Traces will be grouped by units. (You can 'hack' this by putting spaces in the units.)
fields = {
    ('pressure', 'torr'): ('pressure',),

    ('buffer flow', 'sccm'): ('flows', 'cell'),
    ('neon flow', 'sccm'): ('flows', 'neon'),

    ('reflection', 'V'): ('refl',),

    ('transmission (overall, from photodiode)', '%'): ('trans', 'pd'),
    ('transmission (overall, from spectrometer)', '%'): ('trans', 'spec'),
    ('transmission (non-roughness sources only)', '%'): ('trans', 'unexpl'),

#    ('BaF Laser', 'GHz'): ('freq', 'baf'),
    ('Ca Laser', 'GHz'): ('freq', 'calcium'),

    ('rms roughness (from spectrometer)', 'nm'): ('rough',),

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
    'GHz',
    'torr',
    'sccm',
    'V',
    '%',
    'nm',
    'W',
    'K',
    'K ',
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
bands = [None] * len(fields)
colors = defaultdict(int)
for j, field in enumerate(fields):
    name, unit = field

    i = axis_labels.index(unit)
    color = colors[i]
    graph = axes[i].plot_date(
        num_points * [None], num_points * [None],
        linestyle='solid', linewidth=1,
        marker=None, label=name,
        color=f'C{color}'
    )[0]
    colors[i] += 1
    graphs.append((i, color, graph))

# Subplot tweaks
for axis, label in zip(axes, axis_labels):
    axis.legend(loc='upper left')
    axis.margins(0,0.1)
    axis.set_ylabel(label)


# set data formatter
locator = mpdates.AutoDateLocator()
formatter = mpdates.ConciseDateFormatter(locator)
plt.gca().xaxis.set_major_formatter(formatter)

axes[axis_labels.index('torr')].set_yscale('log') # set pressure as log
#axes[axis_labels.index('V')].set_yscale('log') # set reflection as log

##### animated plot #####
times = np.array([datetime.datetime.now()] * num_points)
data = np.zeros((num_points, len(fields), 2))

last = 0
for i, line in enumerate(tail('-n', num_points * skip_points, '-f', filepath, _iter=True)):
    if i % skip_points == 0:
        timestamp, raw_data = line.split(']', 1)
        timestamp = datetime.datetime.strptime(timestamp[1:], '%Y-%m-%d %H:%M:%S.%f')
        timestamp += datetime.timedelta(hours=4) # fix timezone (correct in logs, wrong on plot?)

        raw_data = json.loads(raw_data)

        # Filter out relevant fields
        processed_data = []
        for path in fields.values():
            try:
                value = raw_data
                for entry in path:
                    value = value[entry]
            except:
                value = None

            if isinstance(value, str): value = None

            if not isinstance(value, list):
                value = (value, 0)

            processed_data.append(value)
        processed_data = np.array(processed_data)

        # Add datapoint
        times[:-1] = times[1:]
        times[-1] = timestamp

        data[:-1] = data[1:]
        data[-1] = processed_data

    if (
        time.monotonic() - last < 1 # Avoid plot bottlenecking data read
        and
        abs(i/skip_points - num_points) > 2 # Update a few times manually to get the initial plot
    ): continue

    fig.canvas.flush_events()
    time.sleep(0.05)

    if i % skip_points == 0:
        # Plot data
        start_time = time.monotonic()
        for j, entry in enumerate(graphs):
            k, color, graph = entry
            trace, uncertainty = data[:, j].T
            graph.set_xdata(times)
            graph.set_ydata(trace)

            if bands[j] is not None:
                bands[j].remove()
            bands[j] = axes[k].fill_between(
                times,
                trace - 2*uncertainty,
                trace + 2*uncertainty,
                alpha=0.3,
                color=f'C{color}',
                zorder=-10
            )

        for axis in axes:
            axis.relim()
            axis.autoscale_view()

        fig.canvas.draw()

        if 'running' in raw_data:
            running = raw_data['running']
            pt_status = 'Running' if running['pt'] else 'Off'
            turbo_status = 'Running' if running['turbo'] else 'Off'
            fig.canvas.set_window_title(f'Pulse Tube {pt_status} | Turbo {turbo_status} | {time.asctime(time.localtime())}')

        last = time.monotonic()

        print(f'Plot took {last - start_time:.3f} s')
