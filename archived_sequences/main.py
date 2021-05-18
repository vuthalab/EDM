"""
Main experiment sequence.

The sequence file will automatcally copy itself into /home/vuthalab/Desktop/edm_data/logs/sequences
for record-keeping purposes.

Author: Samuel Li
Date: May 11, 2021
Adapted from old sequence files.
"""

import time
import os, shutil
from pathlib import Path

import numpy as np


#Import class objects
from headers.CTC100 import CTC100
from headers.mfc import MFC


# Log a copy of this sequence file
root_dir = Path('~/Desktop/edm_data/logs/sequences/').expanduser()
root_dir.mkdir(parents=True, exist_ok=True)
filename = root_dir / (time.strftime('%Y-%m-%d %H꞉%M꞉%S') + '.py')

print('Cloning sequence file to', filename)
shutil.copy(__file__, filename)


##### Main Sequencer #####
def melt(low_temp, high_temp, heat_rate, cool_rate, hold_time, wait_time):
    T1.enable_output()
    T1.ramp_temperature('heat saph', high_temp, heat_rate)
    initial_temp = T1.read('saph')

    heat_time = (high_temp - initial_temp) / heat_rate
    print(f'Beginning melt. Time is {time.asctime(time.localtime())}. Ramping from {initial_temp:.2f} K to {high_temp:.2f} K in {heat_time:.2f} s.')
    time.sleep(heat_time)

    print(f'Heating complete. Time is {time.asctime(time.localtime())}. Holding for {hold_time:.2f} s.')
    time.sleep(hold_time)
    T1.ramp_temperature('heat saph', low_temp, cool_rate)
    final_temp = T1.read('saph')

    cool_time = (final_temp - low_temp) / cool_rate
    print(f'Beginning cooldown. Time is {time.asctime(time.localtime())}. Ramping from {final_temp:.2f} K to {low_temp:.2f} K in {cool_time:.2f} s.')
    time.sleep(cool_time)

    print(f'Cooling complete. Time is {time.asctime(time.localtime())}. Holding for {wait_time:.2f} s.')
    time.sleep(wait_time)
    print(f'Melt complete. Time is {time.asctime(time.localtime())}.')


def grow(buffer_rate, neon_line_rate, growth_time, growth_temperature):
    print(f'Beginning growth. Time is {time.asctime(time.localtime())}. Growing at {growth_temperature:.1f} K, {buffer_rate:.2f} sccm in buffer cell, {neon_line_rate:.2f} sccm in neon line, for {growth_time:.1f} s.')
    T1.enable_output()
    T1.ramp_temperature('heat saph', growth_temperature, 0.1)
    mfc.flow_rate_cell = buffer_rate
    mfc.flow_rate_neon_line = neon_line_rate
    time.sleep(growth_time)
    T1.disable_output()
    mfc.off()
    print(f'Growth complete. Time is {time.asctime(time.localtime())}')


# Initialize devices.
# Port numbers are defined in multiplexer.py.
T1 = CTC100(31415)
T2 = CTC100(31416)
mfc = MFC(31417)


#Start the sequence. Enable heaters.
print(f'Running sequence. Time is {time.asctime(time.localtime())}')
mfc.off()

# Define static parameters.
# There is no need to log these manually,
# since the entire sequence file is logged on each run
MINUTE = 60
HOUR = 60 * MINUTE
params_dict = {
    'low_temp': 5.0,
    'high_temp': 25.0,
    'heat_rate': 0.1,
    'cool_rate': 0.05,
    'hold_time': 5.0 * MINUTE,
    'wait_time': 5.0 * MINUTE,

    'buffer_flow': 10.0,
    'neon_flow': 0.0,
    'growth_time': 3.0 * HOUR,
    'growth_temperature': 5.0,
}


# Perform individual sequences.
try:
    if False:
        melt(
            params_dict['low_temp'],
            params_dict['high_temp'],
            params_dict['heat_rate'],
            params_dict['cool_rate'],
            params_dict['hold_time'],
            params_dict['wait_time']
        )


    if True:
        grow(
            params_dict['buffer_flow'],
            params_dict['neon_flow'],
            params_dict['growth_time'],
            params_dict['growth_temperature']
        )

    # Custom fringe code
  #  mfc.flow_rate_cell = 0
   # n_fringes = 20
   # for i in range(4): # split up in case the crystal cracks halfway through
   #     for i in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]:
    #        estimated_period = 77 / i
    #        estimated_duration = n_fringes * estimated_period
    #        print(time.asctime(time.localtime()), i, estimated_duration)
    #        mfc.flow_rate_neon_line = i
    #        time.sleep(estimated_duration)

    #End of the sequence.
    print(f'Sequence complete. Time is {time.asctime(time.localtime())}.')
finally:
    # Clean up.
    T1.disable_output()
    T2.disable_output()
    mfc.off()
