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
num_points = 1000

# Map from plot labels (name, unit) to paths in data
fields = {
    ('pressure', 'torr'): ('pressures', 'chamber'),

    ('buffer flow', 'sccm'): ('flows', 'cell'),
    ('neon flow', 'sccm'): ('flows', 'neon'),

    ('reflection', 'V'): ('voltages', 'AIN1'),
    ('transmission', 'V'): ('voltages', 'AIN2'),

    ('saph heat', 'W'): ('heaters', 'heat saph'),
    ('collimator heat', 'W'): ('heaters', 'heat coll'),
    ('45K heat', 'W'): ('heaters', 'srb45k out'),
    ('4K heat', 'W'): ('heaters', 'srb4k out'),

    ('sapphire mount', 'K'): ('temperatures', 'saph'),
    ('collimator', 'K'): ('temperatures', 'coll'),
    ('bottom hs', 'K'): ('temperatures', 'bott hs'),
    ('buffer cell', 'K'): ('temperatures', 'cell'),
    ('4K sorb', 'K'): ('temperatures', 'srb4k'),
    ('45K sorb', 'K'): ('temperatures', 'srb45k'),
    ('4K plate', 'K'): ('temperatures', '4k plate'),
    ('45K plate', 'K'): ('temperatures', '45k plate'),
}

#field_names = ["time", "Torr", "sccm", "sccm", "$V$" ,"$V$", "W", "W", "W", "W","K","K","K","K","K","K","K","K"]
#labels=["","pressure","buffer flow","neon flow","refl","trans","saph heat", "coll heat", "45K heat", "4K heat", "sapphire mount","collimator","bottom hs","buffer cell","4K sorb","45K sorb","45K plate","4K plate"]

##### BEGIN CODE #####
# pick the directory containing the log file
print('Opening file dialog...')
if False:
    root_window = tk.Tk()
    filepath = filedialog.askopenfile(
        title="Pick file to log",
        initialdir="/home/vuthalab/Desktop/edm_data/logs/system_logs/",
        parent=root_window
    ).name
    root_window.destroy()
filepath = '/home/vuthalab/Desktop/edm_data/logs/system_logs/2021-05-11.txt'
print('Logging', filepath)

###### initial plot #####
plt.ion()
fig = plt.figure(figsize=(10,8))
gs = fig.add_gridspec(len(fields), hspace=0.5, left=0.1, right=0.95, top=0.95, bottom=0.05)
axes = gs.subplots(sharex=True, sharey=False)

# initialize empty plots
graphs = []
for i, field in enumerate(fields):
    name, units = field
    graph = axes[i].plot_date(
        num_points * [None], num_points * [None],
        color=f'C{i}',
        linestyle='solid', lw=2,
        marker=None,
        label=name
    )[0]
    axes[i].set_ylabel(units)
    axes[i].legend(loc='upper left')
    axes[i].margins(0,0.1)
    graphs.append(graph)

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

    # Don't show plot until initial points are loaded
    if i < num_points: continue

    # Avoid plot bottlenecking data read
    if time.time() - last < 3: continue

    # Plot data
    x_padding = [datetime.datetime.now()] * (num_points - len(data))
    y_padding = [None] * (num_points - len(data))
    for j, graph in enumerate(graphs):
        xdata = x_padding + times[-num_points:]
        ydata = y_padding + [row[j] for row in data[-num_points:]]

        graph.set_xdata(xdata)
        graph.set_ydata(ydata)

        axes[j].relim()
        axes[j].autoscale_view()

    fig.canvas.draw()
    fig.canvas.flush_events()
    last = time.time()
    time.sleep(0.01)
