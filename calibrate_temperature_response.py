import time

import numpy as np
import matplotlib.pyplot as plt

from headers.CTC100 import CTC100
from headers.edm_util import countdown_for

import sys

N = int(sys.argv[1])


T1 = CTC100(31415)
T2 = CTC100(31416)

ctc, name = [
    (T1, 'saph'),
    (T2, 'cell'),
][N]


keys = [
    (T1, 'saph'),
    (T1, 'mirror'),
    (T1, 'srb4k'),
    (T2, 'cell'),
    (T2, '4k plate'),

    (ctc, f'heat {name}')
]

T1.ramp_temperature('heat saph', 3, 0.5)
T1.ramp_temperature('heat mirror', 3, 0.5)
T1.enable_output()
T2.ramp_temperature('heat cell', 3, 0.5)
T2.enable_output()


# CHANGE THIS
if N == 0:
    temps = np.linspace(7, 12, 51)
else:
    temps = np.linspace(19, 25, 31)

np.random.shuffle(temps)

with open(f'calibration/temperature-response-{name}.txt', 'a') as f:
    for temp in temps:
        print(temp)

        ctc.ramp_temperature(f'heat {name}', temp, 0.5)

#        while True:
#            curr = ctc.read(name)
#            print(curr, end='\r')
#            time.sleep(0.5)

#            if abs(curr - temp) < 0.010: break
#        print()

        countdown_for(5*60)

        points = {key: [] for (_, key) in keys}
        for i in range(60):
            for obj, key in keys:
                points[key].append(obj.read(key))
                time.sleep(0.05)

            preview = ' | '.join(f'{x[-1]:.3f}' for x in points.values())
            print(f'Data {i} | {preview}', end='\r')

            time.sleep(0.5)
        print()

        means = [np.mean(x) for x in points.values()]
        stdevs = [np.std(x) for x in points.values()]

        print(temp, *means)
        print(temp, *means, *stdevs, file=f, flush=True)
