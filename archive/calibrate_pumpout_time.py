import time
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

from headers.mfc import MFC
from headers.rigol_ds1102e import RigolDS1102e

##### Parameters #####
root_dir = Path('~/Desktop/edm_data/logs/scope/').expanduser()
log_dir = root_dir / 'pumpout-dual'
log_dir.mkdir(exist_ok=True)

mfc = MFC(31417)
flow_rates = [2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30]
np.random.shuffle(flow_rates)

mfc.flow_rate_cell = 10
input('Press enter to start.')

##### Main Program #####
try:
    # Initialize connection
    with RigolDS1102e(address='/dev/usbtmc1') as scope1:
        with RigolDS1102e(address='/dev/usbtmc5') as scope2:
            times1 = scope1.times
            times2 = scope2.times

            for flow_rate in flow_rates:
                print(flow_rate)
                mfc.flow_rate_cell = flow_rate
                time.sleep(5)
                save_path = str(log_dir / f'{flow_rate:02d}.npz')

                s1_ch1_traces = []
                s1_ch2_traces = []

                s2_ch1_traces = []
                s2_ch2_traces = []

                for i in range(60):
                    print(i, end='\r', flush=True)

                    # Get data
                    scope1.active_channel = 1
                    scope2.active_channel = 1
                    s1_ch1_traces.append(scope1.trace)
                    s2_ch1_traces.append(scope2.trace)

                    scope1.active_channel = 2
                    scope2.active_channel = 2
                    s1_ch2_traces.append(scope1.trace)
                    s2_ch2_traces.append(scope2.trace)

                    time.sleep(0.5)
                print()

                np.savez(
                    save_path,

                    times1=times1,
                    times2=times2,
                    s1_ch1 = np.array(s1_ch1_traces),
                    s1_ch2 = np.array(s1_ch2_traces),
                    s2_ch1 = np.array(s2_ch1_traces),
                    s2_ch2 = np.array(s2_ch2_traces),
                )
finally:
    mfc.off()
