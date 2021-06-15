# log the pressure gauge and thermometer

from pathlib import Path

import os
import zmq
import time
from datetime import datetime
import json

import numpy as np

from colorama import Fore, Style
from uncertainties import ufloat

from headers.util import display
from headers.zmq_client_socket import zmq_client_socket


ROOT_DIR = Path('~/Desktop/edm_data/logs/system_logs/').expanduser()
if not ROOT_DIR.exists(): ROOT_DIR.mkdir(parents=True, exist_ok=True)

continuous_log_file = ROOT_DIR / 'continuous.txt'


def log_file():
    """Return the current log file. Will change at midnight."""
    return ROOT_DIR / (time.strftime('%Y-%m-%d') + '.txt')


## connect
connection_settings = {
    'ip_addr': 'localhost', # ip address
    'port': 5551, # our open port
    'topic': 'edm-monitor', # device
}
monitor_socket = zmq_client_socket(connection_settings)
monitor_socket.make_connection()


## nice print function
def print_tree(obj, indent=0):
    for key, value in sorted(obj.items()):
        print('   ' * indent + f'{Fore.YELLOW}{key}{Style.RESET_ALL}', end='')

        if isinstance(value, dict):
            print()
            print_tree(value, indent=indent+1)
        else:
            if isinstance(value, tuple):
                value = display(ufloat(*value))
            print(':', value)



## for tracking neon usage
last_neon = None
def update_neon_remaining(data):
    global last_neon

    buffer_flow = data['flows']['cell'][0] - 0.02
    neon_flow = (data['flows']['neon'][0] - 0.005) * 2.0 # empirical calibration factor
    curr = np.array([time.time(), buffer_flow, neon_flow])

    if last_neon is not None:
        dt = (curr[0] - last_neon[0]) / 60 # minutes

        remaining, buffer_used, neon_used = np.loadtxt('calibration/neon.txt').T
        print(
            f'{Style.BRIGHT}{remaining:.2f} L{Style.RESET_ALL} {Fore.GREEN}neon remaining',
            f'{Style.BRIGHT}{buffer_used:.2f} L{Style.RESET_ALL} {Fore.YELLOW}buffer gas used',
            f'{Style.BRIGHT}{neon_used:.2f} L{Style.RESET_ALL} {Fore.YELLOW}neon line used',
            sep = f' {Style.RESET_ALL}{Style.DIM}|{Style.RESET_ALL} '
        )


        # Update usage
        increment = 0.5 * (last_neon[1:] + curr[1:]) * 1e-3

        # Prevent drift
        if increment[0] < 0.2: increment[0] = 0
        if increment[1] < 0.2: increment[1] = 0

        buffer_used += increment[0]
        neon_used += increment[1]
        remaining -= sum(increment)

        np.savetxt(
            'calibration/neon.txt',
            [[remaining, buffer_used, neon_used]],
            header='neon remaining [L], buffer gas used [L], neon line used [L]'
        )

    last_neon = curr



## set up log file
print('Staring logging...')
while True:
    _, data = monitor_socket.blocking_read()
    timestamp = datetime.now().strftime('[%Y-%m-%d %H:%M:%S.%f]')

    with open(log_file(), 'a') as f:
        print(timestamp, json.dumps(data), file=f)

    with open(continuous_log_file, 'a') as f:
        print(timestamp, json.dumps(data), file=f)


    print()
    print()
    print()
    print(f'{Style.BRIGHT}{Fore.GREEN}{timestamp}{Style.RESET_ALL}')
    print_tree(data)
    print()
    update_neon_remaining(data)

    last = timestamp
