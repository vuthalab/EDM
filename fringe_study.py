"""
The sequence file will automatcally copy itself into /home/vuthalab/Desktop/edm_data/logs/sequences
for record-keeping purposes.

Systematic study of fringe growth.

Author: Samuel Li
Date: May 17, 2021
"""

import time
import os, shutil
from pathlib import Path

import numpy as np


#Import class objects
import headers.usbtmc as usbtmc
from headers.CTC100 import CTC100
from headers.mfc import MFC

# If uncommented, then don't actually do anything
# usbtmc.DRY_RUN = True


# Log a copy of this sequence file
root_dir = Path('~/Desktop/edm_data/logs/sequences/').expanduser()
root_dir.mkdir(parents=True, exist_ok=True)
filename = root_dir / (time.strftime('%Y-%m-%d %H꞉%M꞉%S') + '.py')

print('Cloning sequence file to', filename)
shutil.copy(__file__, filename)


##### Main Sequencer #####
MINUTE = 60
HOUR = 60 * MINUTE

total_time = 1 * HOUR # Total time for one trial.

def melt_and_grow(low_temp, neon_flow, grow_while_cooling):
    finish_time = time.monotonic() + total_time

    modifier = '' if grow_while_cooling else 'not '
    print(f'Growing crystal at {low_temp:.1f} K with {neon_flow:.1f} sccm neon flow. Will {modifier}grow while cooling.')
    with open('fringe-log.txt', 'a') as f:
        print(
            time.asctime(time.localtime()), '|', 'start',
            low_temp, neon_flow, grow_while_cooling,
            file=f
        )

    # Melt the crystal.
    T1.ramp_temperature('heat saph', 25, 0.1)
    time.sleep(10 * MINUTE)

    # Cool crystal. Possibly start the neon now.
    if grow_while_cooling: mfc.flow_rate_neon_line = neon_flow
    T1.ramp_temperature('heat saph', low_temp, 0.05)
    time.sleep(10 * MINUTE)

    # Start the neon now if not started while cooling.
    if not grow_while_cooling: mfc.flow_rate_neon_line = neon_flow
    time.sleep(finish_time - time.monotonic())
    with open('fringe-log.txt', 'a') as f:
        print(time.asctime(time.localtime()), '|', 'stop', file=f)


# Initialize devices.
# Port numbers are defined in multiplexer.py.
T1 = CTC100(31415)
T2 = CTC100(31416)
mfc = MFC(31417)


try:
    mfc.off()
    T1.enable_output()

    melt_and_grow(5, 2, False)
    melt_and_grow(5, 2, True)

    melt_and_grow(5, 4, False)
    melt_and_grow(5, 4, True)

    melt_and_grow(5, 8, True)

    melt_and_grow(7, 4, False)
    melt_and_grow(7, 4, True)

    melt_and_grow(7, 2, True)

    # Special run with buffer gas (may not finish but it's fine)
    mfc.flow_rate_cell = 10
    melt_and_grow(5, 4, False)

finally:
    T1.disable_output()
    T2.disable_output()
    mfc.off()
