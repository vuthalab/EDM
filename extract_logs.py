# live plot system log files
from pathlib import Path
import json, datetime

import numpy as np


##### PARAMETERS #####
# What period of logs to dump. must start and end on same day.
# Date format must be YYYY-MM-DD
# Time format must be HH:MM:SS
# End time can be in the future to get all data after a certain point
date = '2021-05-19'
start_time = '19:26:00'
end_time = '22:20:00'

# Map from plot labels (name, unit) to paths in data
# Choose which fields you want to extract here
fields = {
   ('pressure', 'torr'): ('pressures', 'chamber'),

   ('buffer flow', 'sccm'): ('flows', 'cell'),
   ('neon flow', 'sccm'): ('flows', 'neon'),

   ('reflection', 'V'): ('voltages', 'AIN1'),

   ('transmission', 'V '): ('voltages', 'AIN2'),

#   ('frequency', 'GHz'): ('frequencies', 'BaF_Laser'),


#   ('saph heat', 'W'): ('heaters', 'heat saph'),
#   ('collimator heat', 'W'): ('heaters', 'heat coll'),
#   ('45K heat', 'W'): ('heaters', 'srb45k out'),
#   ('4K heat', 'W'): ('heaters', 'srb4k out'),

#   ('bottom hs', 'K'): ('temperatures', 'bott hs'),
#   ('buffer cell', 'K'): ('temperatures', 'cell'),
#   ('45K sorb', 'K'): ('temperatures', 'srb45k'),
#   ('45K plate', 'K'): ('temperatures', '45k plate'),

   ('sapphire mount', 'K '): ('temperatures', 'saph'),
#   ('collimator', 'K '): ('temperatures', 'coll'),
#   ('4K sorb', 'K '): ('temperatures', 'srb4k'),
#   ('4K plate', 'K '): ('temperatures', '4k plate'),
}


##### Begin Extract #####
assert start_time < end_time
print(f'Extracting logs on {date} from {start_time} to {end_time}...')
processed_data = []
with open(Path('~/Desktop/edm_data/logs/system_logs').expanduser() / f'{date}.txt', 'r') as f:
    for line in f:
        timestamp, data = line.split(']')
        timestamp = timestamp.split(' ')[1]
        if start_time > timestamp or end_time < timestamp: continue

        data = json.loads(data)

        row = []
        for path in fields.values():
            value = data
            for entry in path:
                value = value[entry]
            row.append(value)

        timestamp = datetime.datetime.strptime(f'{date} {timestamp}', '%Y-%m-%d %H:%M:%S.%f')

        if all(isinstance(x, float) for x in row):
            processed_data.append([timestamp.timestamp(), *row])

print(f'Writing {len(processed_data)} entries to extract.txt...')
processed_data = np.array(processed_data)
np.savetxt(
    'extract.txt',
    processed_data,
    header=', '.join(
        ['unix timestamp'] +
        [f'{name} [{unit}]' for name, unit in fields.keys()]
    )
)
