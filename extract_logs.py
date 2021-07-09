# live plot system log files
from pathlib import Path
import json, datetime

import numpy as np

from colorama import Style, Fore


##### PARAMETERS #####
# What period of logs to dump.
# Date format must be YYYY-MM-DD
# Time format must be HH:MM:SS (24-hour format)
# End time can be in the future to get all data after a certain point
START_TIME = ('2021-07-08', '10:00:00')
END_TIME = ('2021-07-08', '23:00:00')

# Map from plot labels (name, unit) to paths in data
# Choose which fields you want to extract here
fields = {
#    ('pressure', 'torr'): ('pressure',),

    ('buffer flow', 'sccm'): ('flows', 'cell'),
    ('neon flow', 'sccm'): ('flows', 'neon'),

#    ('intensity (broadband)', 'V '): ('intensities', 'broadband'),
#    ('intensity (LED)', 'V '): ('intensities', 'LED'),

#    ('reflection (from photodiode)', 'V'): ('refl', 'pd'),
#    ('reflection (from camera, centroid)', 'V'): ('refl', 'cam'),
#    ('reflection (from camera, neural network)', 'V'): ('refl', 'ai'),

    ('fringe count', 'fringes'): ('fringe', 'count'),
    ('fringe amplitude', '%  '): ('fringe', 'ampl'),


#    ('transmission (photodiode)', '%'): ('trans', 'pd'),
#    ('transmission (spectrometer)', '%'): ('trans', 'spec'),
#    ('transmission (non-roughness sources)', '%'): ('trans', 'unexpl'),

#    ('BaF Laser', 'GHz'): ('freq', 'baf'),
#    ('Ca Laser', 'GHz'): ('freq', 'calcium'),

    ('rms roughness (spectrometer)', 'nm'): ('rough', 'surf'),

#    ('saph heat', 'W'): ('heaters', 'heat saph'),
#    ('nozzle heat', 'W'): ('heaters', 'heat coll'),
#    ('45K heat', 'W'): ('heaters', 'srb45k out'),
#    ('4K heat', 'W'): ('heaters', 'srb4k out'),

#    ('bottom hs', 'K'): ('temperatures', 'bott hs'),
#    ('buffer cell', 'K'): ('temperatures', 'cell'),
#    ('45K sorb', 'K'): ('temperatures', 'srb45k'),
#    ('45K plate', 'K'): ('temperatures', '45k plate'),

    ('sapphire mount', 'K'): ('temperatures', 'saph'),
    ('nozzle', 'K'): ('temperatures', 'coll'),
#    ('4K sorb', 'K'): ('temperatures', 'srb4k'),
#    ('4K plate', 'K'): ('temperatures', '4k plate'),

#    ('beam center x (from camera)', '% '): ('center', 'x'),
#    ('beam center y (from camera)', '% '): ('center', 'y'),
#    ('image entropy', 'bytes'): ('center', 'entropy'),

#    ('loop time', 's'): ('debug', 'loop'),
#    ('uptime', 'hr'): ('debug', 'uptime'),
#    ('memory usage', 'KB'): ('debug', 'memory'),
}


##### Begin Extract #####
assert START_TIME < END_TIME
print(f'Extracting logs on from {START_TIME[0]} {START_TIME[1]} to {END_TIME[0]} {END_TIME[1]}...')
log_dir = Path('~/Desktop/edm_data/logs/system_logs').expanduser() 

processed_data = []
for path in sorted(log_dir.glob('*.txt')):
    if START_TIME[0] > path.stem or END_TIME[0] < path.stem: continue

    with path.open('r') as f:
        for i, line in enumerate(f):
            timestamp, data = line.split(']', 1)
            timestamp = timestamp[1:]
            time_only = timestamp.split(' ')[1]
            if START_TIME[0] == path.stem and START_TIME[1] > time_only: continue
            if END_TIME[0] == path.stem and END_TIME[1] < time_only: continue

            data = json.loads(data)

            entries = []
            uncertainties = []
            try:
                for data_path in fields.values():
                    value = data
                    for entry in data_path:
                        value = value[entry]

                    if isinstance(value, list):
                        entries.append(value[0])
                        uncertainties.append(value[1])
                    else:
                        entries.append(value)
                        uncertainties.append(0)
            except KeyError:
                continue


            if i % 1234 == 0:
                print(f'\r[{timestamp}] {Style.BRIGHT}{len(processed_data):10d}{Style.RESET_ALL} {Fore.YELLOW}entries processed{Style.RESET_ALL}', end='')

            try:
                timestamp = datetime.datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S.%f')
            except:
                try:
                    timestamp = datetime.datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
                except:
                    continue

            if all(isinstance(x, float) for x in entries):
                processed_data.append([timestamp.timestamp(), *entries, *uncertainties])

print()
print(f'Writing {len(processed_data)} entries to extract.txt...')
processed_data = np.array(processed_data)
np.savetxt(
    'extract.txt',
    processed_data,
    header=', '.join(
        ['unix timestamp'] +
        [f'{name} [{unit}]' for name, unit in fields.keys()] +
        [f'{name} uncertainty [{unit}]' for name, unit in fields.keys()]
    )
)
