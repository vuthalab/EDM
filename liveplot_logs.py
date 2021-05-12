# live plot system log files
from sh import tail
import time, json, datetime, math

import matplotlib.pyplot as plt
import matplotlib.dates as mpdates
from matplotlib import rcParams
rcParams['timezone'] = 'Canada/Eastern'
rcParams['font.family'] = 'sans-serif'
rcParams.update({'font.size': 8})

from tkinter import filedialog
import tkinter as tk


##### PARAMETERS #####
# number of past points to plot
num_points = 250#1500

# Map from plot labels (name, unit) to paths in data
fields = {
    ('pressure', 'torr'): ('pressures', 'chamber'),

    ('buffer flow', 'sccm'): ('flows', 'cell'),
    ('neon flow', 'sccm'): ('flows', 'neon'),

    ('reflection', 'V'): ('voltages', 'AIN1'),

    ('transmission', 'V '): ('voltages', 'AIN2'),

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
print('Opening file dialog...')
root_window = tk.Tk()
filepath = filedialog.askopenfilename(
    title="Pick file to log",
    initialdir="/home/vuthalab/Desktop/edm_data/logs/system_logs/",
    filetypes=[('Text Files', '*.txt')],
    parent=root_window
)
root_window.destroy()
print('Logging', filepath)

###### initial plot #####
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
times = []
data = []

last = 0
for i, line in enumerate(tail('-n', num_points, '-f', filepath, _iter=True)):
    timestamp, raw_data = line.split(']')
    timestamp = datetime.datetime.strptime(timestamp[1:], '%Y-%m-%d %H:%M:%S')
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
    times.append(timestamp)
    data.append(processed_data)

    # Avoid plot bottlenecking data read
    if time.time() - last < 2: continue

    # Plot data
    x_padding = [datetime.datetime.now()] * (num_points - len(data))
    y_padding = [None] * (num_points - len(data))
    for j, graph in enumerate(graphs):
        xdata = x_padding + times[-num_points:]
        ydata = y_padding + [row[j] for row in data[-num_points:]]

        graph.set_xdata(xdata)
        graph.set_ydata(ydata)
    
    for axis in axes:
        axis.relim()
        axis.autoscale_view()

    fig.canvas.draw()
    fig.canvas.flush_events()
    last = time.time()
    time.sleep(0.03)
