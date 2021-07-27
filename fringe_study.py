"""
The sequence file will automatcally copy itself into /home/vuthalab/Desktop/edm_data/logs/sequences
for record-keeping purposes.

Systematic study of fringe growth.

Author: Samuel Li
Date: May 17, 2021
"""

import time
import os, shutil
import random
from pathlib import Path

import numpy as np

from uncertainties import ufloat


#Import class objects
import headers.usbtmc as usbtmc
from headers.CTC100 import CTC100
from headers.mfc import MFC

from headers.util import display, unweighted_mean
from headers.edm_util import countdown_for, countdown_until, wait_until_quantity

from calibrate_oceanfx import calibrate as calibrate_oceanfx



# If uncommented, then don't actually do anything
# usbtmc.DRY_RUN = True



# Log a copy of this sequence file
LOG_DIR = Path('~/Desktop/edm_data/logs').expanduser()
root_dir = LOG_DIR / 'sequences'
root_dir.mkdir(parents=True, exist_ok=True)
filename = root_dir / (time.strftime('%Y-%m-%d %H꞉%M꞉%S') + '.py')

print('Cloning sequence file to', filename)
shutil.copy(__file__, filename)



##### Main Sequencer #####
MINUTE = 60
HOUR = 60 * MINUTE

def deep_clean():
    start = time.monotonic()

    print('Starting deep clean. Melting crystal.')
    T1.ramp_temperature('heat saph', 40, 0.5)
    countdown_until(start + 2 * MINUTE)

    print('Holding for 5 minutes.')
    countdown_until(start + 7 * MINUTE)

    print('Cooling crystal.')
    T1.ramp_temperature('heat saph', 4, 0.15)
    countdown_until(start + 11 * MINUTE)

    print('Done.')


# total time: 1.5 minutes.
# for internal use only
def _melt_internal():
    end_time = time.monotonic() + 1.5 * MINUTE
    print('Melting crystal + holding for 30 seconds.')
    T1.ramp_temperature('heat saph', 35, 0.4)
    countdown_until(end_time)


# Total time: 5 minutes
def melt_only(end_temp = 8):
    _melt_internal()

    print('Cooling crystal.')
    end_time = time.monotonic() + 3.5 * MINUTE
    T1.ramp_temperature('heat saph', end_temp, 0.15)

    # Delay a bit, then calibrate OceanFX.
    countdown_for(1.8 * MINUTE)
    calibrate_oceanfx('baseline', time_limit=1.5 * MINUTE)

    # Wait for target temperature.
    wait_until_quantity(('temperatures', 'saph'), '<', end_temp + 0.1, unit='K')


# total time: 6 minutes
def melt_and_anneal(neon_flow = 4, end_temp = 8):
    _melt_internal()

    end_time = time.monotonic() + 3 * MINUTE
    print('Cooling crystal.')
    T1.ramp_temperature('heat saph', 9.4, 0.15)

    # Wait a bit, then calibrate OceanFX.
    countdown_for(1.3 * MINUTE)
    calibrate_oceanfx('baseline', time_limit=1.5 * MINUTE)

    # Wait until annealing temp is reached.
    wait_until_quantity(('temperatures', 'saph'), '<', 9.5, unit='K')

    # Anneal for 1 minute.
    print('Annealing (starting neon line).')
    mfc.flow_rate_neon_line = neon_flow
    countdown_for(1 * MINUTE)

    # Cool down to temp slowly.
    print('Cooling to temperature.')
    T1.ramp_temperature('heat saph', end_temp, 0.1)
    wait_until_quantity(('temperatures', 'saph'), '<', end_temp + 0.1, unit='K')
#    mfc.off() # commented out to avoid pause between anneal + growth



def grow_only(
    start_temp = 8, end_temp = None, # start, end temp (K)
    neon_flow = 4, buffer_flow = 0, # flow rates (sccm)
    growth_time = 30 * MINUTE,
    target_roughness = None
):
    if end_temp is None: end_temp = start_temp

    print(f'Growing crystal at with {neon_flow:.1f} sccm neon line, {buffer_flow:.1f} sccm buffer flow. Will ramp temperature from {start_temp:.1f} K to {end_temp:.1f} K during growth.')
    T1.ramp_temperature('heat saph', start_temp, 0.5)
    mfc.flow_rate_neon_line = neon_flow
    mfc.flow_rate_cell = buffer_flow

    if end_temp != start_temp:
        ramp_rate = abs(end_temp - start_temp) / growth_time
        T1.ramp_temperature('heat saph', end_temp, ramp_rate)

    if target_roughness is None:
        countdown_for(growth_time)
    else:
        wait_for_roughness(
            target_roughness,
            lower_bound = True
        )

    print('Done.')
    mfc.off()


def wait_for_roughness(target_roughness, lower_bound=False):
    wait_until_quantity(
        ('rough', 'surf'),
        '>' if lower_bound else '<',
        target_roughness,
        source='spectrometer'
    )


E_a = 19.94e-3 # eV
k_B = 1.381e-23/1.61e-19 # eV/K
T_0 = 9.6 # K
growth_factor = 0.488 # micron/min/sccm neon line
def stationary_polish(
    flow_rate = 4, # sccm
    target_roughness = 300, # nm
):
    # Compute required temperature from Arrhenius equation
    baseline_growth_rate = flow_rate * growth_factor
    temperature = 1/(1/T_0 - (np.log(baseline_growth_rate) * k_B/E_a))
    print(f'Beginning stationary polish at {flow_rate:.1f} sccm, {temperature:.2f} K.')
    T1.ramp_temperature('heat saph', temperature, 0.5)
    mfc.flow_rate_neon_line = flow_rate

    wait_for_roughness(target_roughness)

    print('Cooling...')
    T1.ramp_temperature('heat saph', 5, 0.5)
    mfc.flow_rate_neon_line = 0
    wait_until_quantity(('temperatures', 'saph'), '<', 5.2, unit='K')
    print('Done.')





def melt_and_grow(anneal=True, start_temp = 8, **args):
    if anneal:
        melt_and_anneal(end_temp=start_temp)
    else:
        melt_only(end_temp=start_temp)
    grow_only(start_temp=start_temp, **args)


# Initialize devices.
# Port numbers are defined in multiplexer.py.
T1 = CTC100(31415)
T2 = CTC100(31416)
mfc = MFC(31417)


# Initial conditions
#mfc.off()
T1.ramp_temperature('heat coll', 60, 0.5) # Keep nozzle at consistent temperature
T1.enable_output()

try:
    deep_clean()

    for temperature in [7]:
        melt_and_grow(
            neon_flow=8,
            buffer_flow=0,
            start_temp=temperature,
            anneal=False,

            target_roughness=3500,
        )

        # Cool down slowly to avoid cracking
        T1.ramp_temperature('heat saph', 5, 0.05)
        wait_until_quantity(('temperatures', 'saph'), '<', 5.2, unit='K')

#        stationary_polish(
#            flow_rate = 8,
#            target_roughness = 0,
#            time_limit = 1 * HOUR,
#        )


finally:
    mfc.off()
    T1.disable_output()
    T2.disable_output()
