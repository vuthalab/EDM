import time
import itertools
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

from headers.CTC100 import CTC100
from headers.mfc import MFC
from headers.rigol_ds1102e import RigolDS1102e

##### Parameters #####
root_dir = Path('~/Desktop/edm_data/logs/scope/').expanduser()
log_dir = root_dir / 'fringe-log-during-growth.txt'
log_dir.mkdir(exist_ok=True)

##### Main Program #####
# Initialize connection
#with RigolDS1102e(address='/dev/usbtmc1') as scope1:
if True:
    with RigolDS1102e(address='/dev/usbtmc5') as scope2:

#        times1 = scope1.times
        times2 = scope2.times

        for i in itertools.count():
            times = []

#            s1_ch1_traces = []
#            s1_ch2_traces = []

            s2_ch1_traces = []
            s2_ch2_traces = []

            for j in range(30):
                print(i, j)
#                scope1.active_channel = 1
                scope2.active_channel = 1
#                s1_ch1_traces.append(scope1.trace)
                s2_ch1_traces.append(scope2.trace)

#                scope1.active_channel = 2
                scope2.active_channel = 2
#                s1_ch2_traces.append(scope1.trace)
                s2_ch2_traces.append(scope2.trace)

                times.append(time.time())

                time.sleep(0.5)

            np.savez(
                str(log_dir / f'{i:03d}.npz'),
                times=times,
#                times1=times1,
                times2=times2,
#                s1_ch1 = np.array(s1_ch1_traces),
#                s1_ch2 = np.array(s1_ch2_traces),
                s2_ch1 = np.array(s2_ch1_traces),
                s2_ch2 = np.array(s2_ch2_traces),
            )
