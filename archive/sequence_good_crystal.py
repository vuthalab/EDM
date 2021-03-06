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

from uncertainties import ufloat


#Import class objects
import headers.usbtmc as usbtmc
from headers.CTC100 import CTC100
from headers.mfc import MFC

from headers.util import display
from headers.zmq_client_socket import zmq_client_socket



# If uncommented, then don't actually do anything
# usbtmc.DRY_RUN = True


LOG_DIR = Path('~/Desktop/edm_data/logs').expanduser()

connection_settings = {
    'ip_addr': 'localhost', # ip address
    'port': 5551, # our open port
    'topic': 'edm-monitor', # device
}




# Log a copy of this sequence file
root_dir = LOG_DIR / 'sequences'
root_dir.mkdir(parents=True, exist_ok=True)
filename = root_dir / (time.strftime('%Y-%m-%d %H꞉%M꞉%S') + '.py')

print('Cloning sequence file to', filename)
shutil.copy(__file__, filename)



##### Main Sequencer #####
MINUTE = 60
HOUR = 60 * MINUTE

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


# total time: 8 minutes
def melt_and_anneal(neon_flow = 1, end_temp = 8):
    print('Melting crystal.')
    T1.ramp_temperature('heat saph', 35, 0.4)
    time.sleep(1 * MINUTE)

    print('Holding for 30 seconds.')
    time.sleep(30)

    print('Cooling crystal.')
    T1.ramp_temperature('heat saph', 10, 0.15)
    time.sleep(3 * MINUTE)

    print('Annealing + starting neon line.')
    mfc.flow_rate_neon_line = neon_flow
    T1.ramp_temperature('heat saph', 8, 1/90)
    time.sleep(3 * MINUTE)

    print('Cooling to temperature.')
    T1.ramp_temperature('heat saph', end_temp, 0.2)
    time.sleep(30)
#    mfc.off() # commented out to avoid pause between anneal + growth



def grow(
    start_temp = 8, end_temp = None, # start, end temp (K)
    neon_flow = 4, buffer_flow = 0, # flow rates (sccm)
    growth_time = 30 * MINUTE
):
    if end_temp is None: end_temp = start_temp

    print(f'Growing crystal at with {neon_flow:.1f} sccm neon line, {buffer_flow:.1f} sccm buffer flow. Will ramp temperature from {start_temp:.1f} K to {end_temp:.1f} K during growth.')
    T1.ramp_temperature('heat saph', start_temp, 0.5)
    mfc.flow_rate_neon_line = neon_flow
    mfc.flow_rate_cell = buffer_flow

    ramp_rate = abs(end_temp - start_temp) / growth_time
    T1.ramp_temperature('heat saph', end_temp, ramp_rate)
    time.sleep(growth_time)

    print('Done.')
    mfc.off()



def polish(
    polish_temp = 10.3, # K
    target_roughness = 300, # nm

    time_limit = None,

    grow_coat = True,
    coat_sccm = 10, # flow rate for neon coat
    coat_time = 5 * MINUTE, # duration of neon coat
    coat_temp = 9, # saph temperature for neon coat
):
    """Grow a sacrificial coat of neon, then slowly melt until the desired roughness is achieved."""

    if grow_coat:
        print('Setting temperature.')
        T1.ramp_temperature('heat saph', coat_temp, 0.5)
        time.sleep(10)

        print('Growing neon coat.')
        mfc.flow_rate_neon_line = coat_sccm
        time.sleep(coat_time)
        mfc.off()


    print('Annealing surface.')
    T1.ramp_temperature('heat saph', polish_temp, 0.2)


    ## connect to publisher
    monitor_socket = zmq_client_socket(connection_settings)
    monitor_socket.make_connection()

    # Stay at temperature until roughness drops
    start = time.monotonic()
    while True:
        _, data = monitor_socket.blocking_read()
        roughness = data['rough']
        if roughness is None:
            print('OceanFX is down!')
            break

        roughness = ufloat(*roughness)
        print(f'\rRoughness: {display(roughness)} nm', end='')

        if roughness.n + roughness.s < target_roughness and (roughness.n + roughness.s) != 0:
            print()
            break

        if time_limit is not None and time.monotonic() - start > time_limit:
            print()
            print('Time limit exceeded.')
            break
    monitor_socket.close()
    

    print('Cooling...')
    T1.ramp_temperature('heat saph', 4, 0.1)
    time.sleep(1 * MINUTE)
    print('Done.')



def melt_and_grow(start_temp = 8, **args):
    melt_and_anneal(end_temp=start_temp)
    grow(start_temp=start_temp, **args)


# Initialize devices.
# Port numbers are defined in multiplexer.py.
T1 = CTC100(31415)
T2 = CTC100(31416)
mfc = MFC(31417)


# Initial conditions
mfc.off()
T1.enable_output()
T1.ramp_temperature('heat coll', 60, 0.5) # Keep nozzle at consistent temperature

try:
#    deep_clean()

    #melt_and_grow(neon_flow=0, buffer_flow=10, growth_time=1.5 * HOUR)

    # Recreate pause
    #T1.disable_output()
    #time.sleep(10 * MINUTE)
    #T1.enable_output()

    polish(polish_temp=10.3, target_roughness=2250, time_limit=30 * MINUTE)


finally:
    mfc.off()
    T1.disable_output()
    T2.disable_output()
