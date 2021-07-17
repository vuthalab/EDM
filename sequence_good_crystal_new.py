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

from headers.util import display
from headers.zmq_client_socket import connect_to

from calibrate_oceanfx import calibrate as calibrate_oceanfx




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

def _sleep_until(end_time):
    time.sleep(max(end_time - time.monotonic(), 0))

def deep_clean():
    print('Starting deep clean. Melting crystal.')
    T1.ramp_temperature('heat saph', 40, 0.5)
    time.sleep(2 * MINUTE)

    print('Holding for 5 minutes.')
    time.sleep(5 * MINUTE)

    print('Cooling crystal.')
    T1.ramp_temperature('heat saph', 4, 0.15)
    time.sleep(4 * MINUTE)

    print('Done.')


# total time: 1.5 minutes.
# for internal use only
def _melt_internal():
    end_time = time.monotonic() + 1.5 * MINUTE
    print('Melting crystal + holding for 30 seconds.')
    T1.ramp_temperature('heat saph', 35, 0.4)
    _sleep_until(end_time)


# Total time: 5 minutes
def melt_only(end_temp = 8):
    _melt_internal()

    print('Cooling crystal.')
    end_time = time.monotonic() + 3.5 * MINUTE
    T1.ramp_temperature('heat saph', end_temp, 0.15)
    calibrate_oceanfx('baseline', time_limit=3.3 * MINUTE)
    _sleep_until(end_time)


# total time: 6 minutes
def melt_and_anneal(neon_flow = 4, end_temp = 8):
    _melt_internal()

    end_time = time.monotonic() + 3 * MINUTE
    print('Cooling crystal.')
    T1.ramp_temperature('heat saph', 9.4, 0.15)
    calibrate_oceanfx('baseline', time_limit=2.8 * MINUTE)
    _sleep_until(end_time)

    print('Annealing (starting neon line).')
    mfc.flow_rate_neon_line = neon_flow
    time.sleep(1 * MINUTE)

    print('Cooling to temperature.')
    T1.ramp_temperature('heat saph', end_temp, 0.1)
    time.sleep(30)
#    mfc.off() # commented out to avoid pause between anneal + growth



def grow_only(
    start_temp = 8, end_temp = None, # start, end temp (K)
    neon_flow = 4, buffer_flow = 0, # flow rates (sccm)
    growth_time = 30 * MINUTE
):
    if end_temp is None: end_temp = start_temp

    print(f'Growing crystal at with {neon_flow:.1f} sccm neon line, {buffer_flow:.1f} sccm buffer flow. Will ramp temperature from {start_temp:.1f} K to {end_temp:.1f} K during growth.')
    T1.ramp_temperature('heat saph', start_temp, 0.5)
    mfc.flow_rate_neon_line = neon_flow
    mfc.flow_rate_cell = buffer_flow

    if end_temp != start_temp:
        ramp_rate = abs(end_temp - start_temp) / growth_time
        T1.ramp_temperature('heat saph', end_temp, ramp_rate)

    time.sleep(growth_time)

    print('Done.')
    mfc.off()


def wait_for_roughness(target_roughness, time_limit=None):
    ## connect to publisher
    monitor_socket = connect_to('spectrometer')

    # Stay at temperature until roughness drops
    buff = []
    start = time.monotonic()
    while True:
        _, data = monitor_socket.blocking_read()
        roughness = data['rough']['surf']
        if roughness is None:
            print('OceanFX is down!')
            break

        roughness = ufloat(*roughness)
        print(f'\rRoughness: {display(roughness)} nm', end='')

        # Keep rolling buffer
        if roughness.n > 0:
            buff.append(roughness.n)
            buff = buff[-32:]

        if np.mean(buff) < target_roughness:
            print()
            break

        if time_limit is not None and time.monotonic() - start > time_limit:
            print()
            print('Time limit exceeded.')
            break
    monitor_socket.socket.close()


E_a = 19.94e-3 # eV
k_B = 1.381e-23/1.61e-19 # eV/K
T_0 = 9.6 # K
growth_factor = 0.488 # micron/min/sccm neon line
def stationary_polish(
    flow_rate = 4, # sccm
    target_roughness = 300, # nm
    time_limit = None,
):
    # Compute required temperature from Arrhenius equation
    baseline_growth_rate = flow_rate * growth_factor
    temperature = 1/(1/T_0 - (np.log(baseline_growth_rate) * k_B/E_a))
    print(f'Beginning stationary polish at {flow_rate:.1f} sccm, {temperature:.2f} K.')
    T1.ramp_temperature('heat saph', temperature, 0.5)
    mfc.flow_rate_neon_line = flow_rate

    wait_for_roughness(target_roughness, time_limit=time_limit)

    print('Cooling...')
    T1.ramp_temperature('heat saph', 4, 0.5)
    mfc.flow_rate_neon_line = 0
    time.sleep(10)
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
mfc.off()
T1.ramp_temperature('heat coll', 60, 0.5) # Keep nozzle at consistent temperature
T1.enable_output()

try:
    melt_and_grow(neon_flow=0, buffer_flow=10, growth_time=1.5 * HOUR)
    stationary_polish(target_roughness=1500, time_limit=30*MINUTE)

finally:
    mfc.off()
    T1.disable_output()
    T2.disable_output()