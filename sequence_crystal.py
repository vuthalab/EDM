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
from headers.turbo import TurboPump

from headers.util import display, unweighted_mean
from headers.edm_util import countdown_for, countdown_until, wait_until_quantity

try:
    from calibrate_oceanfx import calibrate as calibrate_oceanfx
except:
    pass



# If uncommented, then don't actually do anything
# usbtmc.DRY_RUN = True



# Log a copy of this sequence file
LOG_DIR = Path('~/Desktop/edm_data/logs').expanduser()
root_dir = LOG_DIR / 'sequences'
root_dir.mkdir(parents=True, exist_ok=True)
filename = root_dir / (time.strftime('%Y-%m-%d %H꞉%M꞉%S') + '.py')

print('Cloning sequence file to', filename)
shutil.copy(__file__, filename)


def log_entry(line):
    with open('fringe-log.txt', 'a') as f:
        print(line)
        print(time.time(), line, file=f)



##### Main Sequencer #####
MINUTE = 60
HOUR = 60 * MINUTE

def deep_clean():
    start = time.monotonic()
    turbo.off() # To avoid damage

    log_entry('Starting deep clean. Melting crystal.')
    T1.ramp_temperature('heat saph', 40, 0.5)
    countdown_until(start + 2 * MINUTE)

    log_entry('Holding for 5 minutes.')
    countdown_until(start + 7 * MINUTE)

    log_entry('Cooling crystal.')
    T1.ramp_temperature('heat saph', 4, 0.15)
    countdown_until(start + 11 * MINUTE)

    # Wait for pressure to drop before enabling turbo
    wait_until_quantity(('pressure',), '<', 1e-1, unit='torr')
    turbo.on()

    log_entry('Done deep clean.')


def melt_crystal(speed = 0.1, end_temp = 9):
    log_entry('Melting crystal.')
    turbo.off() # To avoid damage

    # Raise saph temperature
    T1.ramp_temperature('heat saph', 25, speed)
    wait_until_quantity(('temperatures', 'saph'), '>', 22, unit='K', source='ctc')

    # Ensure crystal is melted
    #wait_until_quantity(('trans', 'spec'), '>', 95, unit='%')
    countdown_for(2 * MINUTE)

    # Lower temperature slowly
    log_entry('Cooling crystal.')
    T1.ramp_temperature('heat saph', 15, speed)

    # Wait for pressure to drop before enabling turbo
    wait_until_quantity(('pressure',), '<', 1e-1, unit='torr')
    turbo.on()

    # Cool down a bit, then calibrate OceanFX.
    T1.ramp_temperature('heat saph', end_temp, speed)
    wait_until_quantity(('temperatures', 'saph'), '<', 20, unit='K', source='ctc')
#    try:
#        calibrate_oceanfx('baseline', time_limit=1.5 * MINUTE)
#    except:
#        pass
    wait_until_quantity(('temperatures', 'saph'), '<', end_temp + 0.01, unit='K', source='ctc')


# total time: 6 minutes
def melt_and_anneal(neon_flow = 4, end_temp = 9):
    melt_crystal(end_temp = 11)

    # Anneal.
    log_entry('Annealing (starting neon line).')
    mfc.flow_rate_neon_line = 4
    T1.ramp_temperature('heat saph', 9.5, 0.005)
    wait_until_quantity(('temperatures', 'saph'), '<', 9.6, unit='K', source='ctc')

    # Grow a few layers.
    countdown_for(2 * MINUTE)

    # Cool down to temp slowly.
    T1.ramp_temperature('heat saph', end_temp, 0.1)
    wait_until_quantity(('temperatures', 'saph'), '<', end_temp + 0.01, unit='K', source='ctc')

#    mfc.off() # commented out to avoid pause between anneal + growth



def grow_only(
    start_temp = 9, end_temp = None, # start, end temp (K)
    neon_flow = 4, buffer_flow = 0, # flow rates (sccm)

    growth_time = 30 * MINUTE,
    target_roughness = None,
    target_thickness = None,
):
    if end_temp is None: end_temp = start_temp

    log_entry(f'Growing crystal at with {neon_flow:.1f} sccm neon line, {buffer_flow:.1f} sccm buffer flow. Will ramp temperature from {start_temp:.1f} K to {end_temp:.1f} K during growth.')
    T1.ramp_temperature('heat saph', start_temp, 0.5)
    mfc.flow_rate_neon_line = neon_flow
    mfc.flow_rate_cell = buffer_flow

    if end_temp != start_temp:
        ramp_rate = abs(end_temp - start_temp) / growth_time
        T1.ramp_temperature('heat saph', end_temp, ramp_rate)

    if target_roughness is not None:
        wait_for_roughness(target_roughness, lower_bound = True)
    elif target_thickness is not None:
        wait_until_quantity(('model', 'height'), '>', target_thickness)
    else:
        countdown_for(growth_time)

    log_entry('Done growth.')
    mfc.off()


def wait_for_roughness(target_roughness, lower_bound=False):
    wait_until_quantity(
        ('rough', 'surf'),
        '>' if lower_bound else '<',
        target_roughness,
        source='spectrometer',
        buffer_size=16
    )


E_a = 19.94e-3 # eV
k_B = 1.381e-23/1.61e-19 # eV/K
T_0 = 9.6 # K
growth_factor = 0.488 # micron/min/sccm neon line
def stationary_polish(
    flow_rate = 8, # sccm
    target_consistency = 25, # nm
):
    # Compute required temperature from Arrhenius equation
    baseline_growth_rate = flow_rate * growth_factor
    temperature = 1/(1/T_0 - (np.log(baseline_growth_rate) * k_B/E_a))
    log_entry(f'Beginning stationary polish at {flow_rate:.1f} sccm, {temperature:.2f} K.')
    T1.ramp_temperature('heat saph', temperature, 0.5)
    mfc.flow_rate_neon_line = flow_rate
    
#    wait_for_roughness(target_roughness=-5)
    wait_until_quantity(
        ('rough', 'surf'), 'stable to within', target_consistency,
        unit='nm',
        source='spectrometer',
        buffer_size=60,
    )

    log_entry('Cooling...')
    T1.ramp_temperature('heat saph', 5, 0.5)
    mfc.flow_rate_neon_line = 0
    wait_until_quantity(('temperatures', 'saph'), '<', 8, unit='K')
    log_entry('Done polish.')





def melt_and_grow(anneal=True, start_temp = 9, **args):
    if anneal:
        melt_and_anneal(end_temp=start_temp)
    else:
        melt_crystal(end_temp=start_temp)
    grow_only(start_temp=start_temp, **args)


# Initialize devices.
# Port numbers are defined in multiplexer.py.
T1 = CTC100(31415)
T2 = CTC100(31416)
mfc = MFC(31417)
turbo = TurboPump()


# Initial conditions
#mfc.off()
T1.ramp_temperature('heat mirror', 10, 0.5) # Keep nozzle at consistent temperature
T1.enable_output()

T2.ramp_temperature('srb45k out', 5, 0.5) # Keep nozzle at consistent temperature
T2.ramp_temperature('heat cell', 15, 0.5) # Keep nozzle at consistent temperature
T2.enable_output()

try:
#    deep_clean()

#    NORMAL PROCEDURE FOR GOOD CRYSTALS
    melt_and_grow(start_temp = 6.5, neon_flow = 0, buffer_flow = 30, growth_time = 2 * HOUR)
#    melt_and_grow(start_temp = 6.5, neon_flow = 14, buffer_flow = 0, growth_time = 20 * MINUTE)
#    grow_only(start_temp=6.5, neon_flow=0, buffer_flow=30, growth_time=1 * HOUR)

#    stationary_polish()

    # Frosty crystal
#    melt_and_grow(start_temp=8, neon_flow = 14, buffer_flow = 0, growth_time = 30 * MINUTE)

#    melt_crystal(end_temp=5)

#    grow_only(start_temp=6.5,neon_flow=0,buffer_flow=30,growth_time=60 * MINUTE)

finally:
    mfc.off()
    T1.disable_output()
    T2.disable_output()
