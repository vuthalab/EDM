# live plot system log files
from sh import tail
import time, json, datetime, math, sys
from collections import defaultdict

# Whether to show plot or upload to server
HEADLESS = len(sys.argv) > 1

import subprocess

import numpy as np

import matplotlib
if HEADLESS: matplotlib.use('Agg')
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
duration = 2 * HOUR

if HEADLESS:
    duration = float(sys.argv[1]) * HOUR


# skip every x points.
skip_points = max(1, round(duration / (2 * HOUR)))


# how fast the publisher is
publisher_rate = 1.4/2 # Hertz


# how often to update plot.
PLOT_INTERVAL = 30 if HEADLESS else 2



# Map from plot labels (name, unit) to paths in data
# Uncomment any fields you want to see.
# Traces will be grouped by units. (You can 'hack' this by putting spaces in the units.)
fields = {
    ('pressure', 'torr'): ('pressure',),

    ('neon flow', 'sccm'): ('flows', 'neon'),
    ('buffer flow (total)', 'sccm'): ('flows', 'cell'),
    ('buffer flow (mfc 1)', 'sccm'): ('flows', 'cell1'),
    ('buffer flow (mfc 2)', 'sccm'): ('flows', 'cell2'),

#    ('intensity (broadband)', 'V '): ('intensities', 'broadband'),
#    ('intensity (LED)', 'V '): ('intensities', 'LED'),

#    ('reflection (from camera, centroid)', 'V'): ('refl', 'cam'),
#    ('reflection (from camera, neural network)', 'V'): ('refl', 'ai'),

#    ('fringe count', 'fringes'): ('fringe', 'count'),
#    ('fringe amplitude', '%  '): ('fringe', 'ampl'),

#    ('transmission (overall, from spectrometer)', '%'): ('trans', 'spec'),
#    ('transmission (non-roughness sources only)', '%'): ('trans', 'unexpl'),

    ('BaF Laser', 'GHz '): ('freq', 'baf'),
    ('Ti:Sapphire Laser (from wavemeter)', 'GHz'): ('freq', 'ti-saph'),
    ('Ti:Sapphire Laser (from spectrometer)', 'GHz'): ('freq', 'ti-saph-spec'),
#    ('Ca Laser', 'GHz '): ('freq', 'calcium'),

    ('BaF error signal', 'mV'): ('error-signals', 'baf'),

    ('BaF Laser', 'uW into wavemeter'): ('intensities', 'baf'),
    ('Ti:Sapphire Laser', 'uW into wavemeter'): ('intensities', 'ti-saph'),
#    ('Ca Laser', 'uW into wavemeter'): ('intensities', 'calcium'),

    ('Ti:Sapphire linewidth (from spectrometer)', 'nm '): ('ti-saph', 'linewidth'),

#    ('pump beam power, total', 'mW'): ('pump', 'power'),
#    ('pump beam power, vertically polarized component', 'mW'): ('pump', 'power-vert'),
#    ('pump beam power, horizontally polarized component', 'mW'): ('pump', 'power-horiz'),

#    ('pump beam angle (from photodiode calibration)', 'degrees'): ('pump', 'angle'),
#    ('pump beam angle (from EOM gain calibration) ', 'degrees'): ('pump', 'angle-model'),

    ('PMT current', 'uA'): ('pmt', 'current'),
    ('PMT gain', 'V'): ('pmt', 'gain'),


#    ('rms roughness (from spectrometer)', 'nm'): ('rough', 'surf'),
#    ('second-order roughness coefficient', 'micron$^2$'): ('rough', 'second-order'),
#    ('fourth-order roughness coefficient (rayleigh $- K \sigma^4$)', 'micron nm$^3$'): ('rough', 'fourth-order'),
    ('crystal thickness (dead reckoning)', 'micron'): ('height',),

#    ('roughness reduced-$\\chi^2$', ''): ('rough', 'chisq'),
#    ('oceanfx hdr reduced-$\\chi^2$', ''): ('rough', 'hdr-chisq'),

    ('saph heat', 'W'): ('heaters', 'heat saph'),
    ('nozzle heat', 'W'): ('heaters', 'heat coll'),
    ('45K heat', 'W'): ('heaters', 'srb45k out'),
    ('4K heat', 'W'): ('heaters', 'srb4k out'),

    ('bottom hs', 'K'): ('temperatures', 'bott hs'),
    ('buffer cell', 'K'): ('temperatures', 'cell'),
    ('45K sorb', 'K'): ('temperatures', 'srb45k'),
    ('45K plate', 'K'): ('temperatures', '45k plate'),
    ('nozzle', 'K'): ('temperatures', 'coll'),

    ('sapphire mount', 'K '): ('temperatures', 'saph'),
    ('4K sorb', 'K '): ('temperatures', 'srb4k'),
    ('4K plate', 'K '): ('temperatures', '4k plate'),

    ('highfinesse wavemeter', '°C'): ('temperatures', 'wavemeter'),
    ('verdi power', 'W'): ('verdi', 'power'),

#    ('beam center x (from camera)', '% '): ('center', 'x'),
#    ('beam center y (from camera)', '% '): ('center', 'y'),

    ('ablation position x (from camera)', 'pixels'): ('ablation', 'center', 'x'),
    ('ablation position y (from camera)', 'pixels'): ('ablation', 'center', 'y'),
    ('ablation HeNe reflection intensity (from camera)', 'arbitrary'): ('ablation', 'intensity'),

#    ('camera integration time', 'μs'): ('center', 'exposure'),
    ('publisher uptime', 'hr'): ('debug', 'uptime'),
    ('interlock uptime', 'hr'): ('interlock-uptime',),
    ('publisher memory usage', 'KB'): ('debug', 'memory'),
    ('system memory usage', 'KB'): ('debug', 'system-memory'),

    ('fridge temperature', '°C  '): ('temperatures', 'fridge'),
    ('QE Pro CCD temperature', '°C  '): ('temperatures', 'qe-pro'),
    ('fridge RH', ' % '): ('fridge', 'relative_humidity'),
    ('fridge absolute humidity', 'g/m$^3$'): ('fridge', 'absolute_humidity'),

#    ('turbo speed', 'Hz'): ('turbo', 'frequency'),
    ('turbo current', 'mA'): ('turbo', 'current'),

    ('pulsetube coolant in', '°C '): ('pt', 'coolant in temp [C]'),
    ('pulsetube coolant out', '°C '): ('pt', 'coolant out temp [C]'),
    ('pulsetube helium', '°C '): ('pt', 'helium temp [C]'),
    ('pulsetube oil', '°C '): ('pt', 'oil temp [C]'),
    ('verdi baseplate', '°C '): ('temperatures', 'verdi', 'baseplate'),
    ('verdi vanadate', '°C '): ('temperatures', 'verdi', 'vanadate'),

    ('pulsetube high pressure', 'psi'): ('pt', 'high pressure [psi]'),
    ('pulsetube low pressure', 'psi'): ('pt', 'low pressure [psi]'),
}

axis_labels = [
    '°C',

    'W',
    'K',
    'K ',

    'torr',
    'sccm',

    'GHz',
    'GHz ',
    'mV',
    'uW into wavemeter',
    'nm ',

#    'mW',
#    'degrees',

#    'V',
#    '%',

    'uA',
    'V',

#    'nm',
#    'micron$^2$',
#    'micron nm$^3$',
    'micron',

#    'fringes',
#    '%  ',

#    'V ',
#    '% ',

    'pixels',
    'arbitrary',

#    '',
#    'μs',
    'hr',
    'KB',

    '°C  ',
    ' % ',
    'g/m$^3$',

#    'Hz',
    'mA',

    '°C ',
    'psi',
]



##### BEGIN CODE #####
filepath = '/home/vuthalab/Desktop/edm_data/logs/system_logs/continuous.txt'
#filepath = '/home/vuthalab/Desktop/edm_data/logs/system_logs/2021-11-24.txt'


###### initial plot #####
num_points = round(publisher_rate * duration / skip_points)
print(f'Showing last {num_points * skip_points} points (skip every {skip_points}).')

if not HEADLESS: plt.ion()

figsize = (6, 40) if HEADLESS else (10, 8)
fig = plt.figure(figsize=figsize)
gs = fig.add_gridspec(
    len(axis_labels),
    hspace=0.1,
    left=0.15, right=0.95, top=0.95, bottom=0.05)
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
    axis.grid(alpha=0.3)


# set data formatter
locator = mpdates.AutoDateLocator()
formatter = mpdates.ConciseDateFormatter(locator)
plt.gca().xaxis.set_major_formatter(formatter)

for label in ['torr', 'uW into wavemeter']:#, 'μs', '']:
    axes[axis_labels.index(label)].set_yscale('log')

##### animated plot #####
times = np.array([datetime.datetime.now()] * num_points)
data = np.zeros((num_points, len(fields), 2))

last = 0
for i, line in enumerate(tail('-n', num_points * skip_points, '-f', filepath, _iter=True)):
    if i % skip_points == 0:
        try:
            timestamp, raw_data = line.split(']', 1)
            timestamp = datetime.datetime.strptime(timestamp[1:], '%Y-%m-%d %H:%M:%S.%f')
            timestamp += datetime.timedelta(hours=4) # fix timezone (correct in logs, wrong on plot?)

            raw_data = json.loads(raw_data)
        except:
            continue

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
        time.monotonic() - last < PLOT_INTERVAL # Avoid plot bottlenecking data read
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

        thread_status = ''
        if 'thread-up' in raw_data:
            threads_down = [name for name, up in raw_data['thread-up'].items() if not up]
            if threads_down:
                thread_status = '\n\n' + ', '.join(threads_down) + ' thread down!'

        if 'running' in raw_data:
            running = raw_data['running']
            def get_status(name):
                return 'Running' if running.get(name, False) else 'Off'

            pt_status = get_status('pt')
            turbo_status = get_status('turbo')
            verdi_status = get_status('verdi')


            title = f'Pulse Tube {pt_status} · Turbo {turbo_status} · Verdi {verdi_status} · {time.asctime(time.localtime())}{thread_status}'

            if HEADLESS:
                axes[0].set_title(title, pad=20)
            else:
                fig.canvas.set_window_title(title)

        fig.canvas.draw()


        last = time.monotonic()

        print(f'Plot took {last - start_time:.3f} s')

        if HEADLESS:
            plt.savefig(f'/tmp/log-{round(duration)}.png', dpi=150)
            subprocess.run(f'scp /tmp/log-{round(duration)}.png celine@143.110.210.120:~/server/', shell=True)
