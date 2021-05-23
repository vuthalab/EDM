# log the pressure gauge and thermometer

from pathlib import Path

import os
import zmq
import time
from datetime import datetime
import json
import numpy as np

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

## set up log file
print('Staring logging...')
while True:
    _, data = monitor_socket.blocking_read()
    timestamp = datetime.now().strftime('[%Y-%m-%d %H:%M:%S.%f]')

    with open(log_file(), 'a') as f:
        print(timestamp, json.dumps(data), file=f)

    with open(continuous_log_file, 'a') as f:
        print(timestamp, json.dumps(data), file=f)

    print(timestamp, json.dumps(data))
