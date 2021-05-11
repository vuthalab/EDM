# log the pressure gauge and thermometer

from pathlib import Path

import os
import zmq
import time
import numpy as np

os.chdir("/home/vuthalab/gdrive/code/edm_control/")
from headers.zmq_client_socket import zmq_client_socket


## create timestamped data folder
def get_save_folder(root_dir):
    # Create a folder inside folder root_dir to save all recorded data, labelled by the date. Returns the full path to the folder

    #Open folder for saving data
    savefolder = Path(root_dir).expanduser() / time.strftime('%Y/%m_%B_%Y/%d/%H꞉%M꞉%S')

    #If folder does not already exist, create it
    if not savefolder.exists(): savefolder.mkdir(parents=True)

    return savefolder

## connect
connection_settings = {
    'ip_addr': 'localhost', # ip address
    'port': 5550, # our open port
    'topic': 'EDM_monitor' # device
}
monitor_socket = zmq_client_socket(connection_settings)
monitor_socket.make_connection()

## set up log file
root_dir = Path('/home/vuthalab/Desktop/edm_data/logs/full_system/')
logfile_path = get_save_folder(root_dir) / 'system_log.txt'

mode = 'a' if logfile_path.exists() else 'w'
with open(logfile_path, mode) as logfile:
    print("# unix time [s]  \t pressure [torr] \t flow [sccm] \t flow [sccm] \t voltage [V] \t voltage [V] \t power [W] \t power [W] \t power [W] \t power [W] \t temperatures [K] \t temperatures [K] \t temperatures [K] \t temperatures [K] \t temperatures [K] \t temperatures [K] \t temperatures [K] \t temperatures [K]", file=logfile)

print('Logging to folder', logfile_path)

    # logging loop

try:
    while True:
        current_time = time.time()

        print(current_time)

        data = monitor_socket.read_on_demand()[1]
        
        pressures = data['pressures']
        temperatures = data['temperatures']
        heaters = data['heaters']
        voltages = data['voltages']
        flows = data['flows']

        print(current_time)

        if pressures > 1e-12: #correcting against ocassional bugs in reading
            data = f'{current_time} \t {pressures} \t {flows[0]} \t {flows[1]} \t {voltages[0]} \t {voltages[1]} \t {heaters[0]} \t {heaters[1]} \t {heaters[2]} \t {heaters[3]} \t {temperatures[0]} \t {temperatures[1]} \t {temperatures[2]} \t {temperatures[3]} \t {temperatures[4]} \t {temperatures[5]} \t {temperatures[6]} \t {temperatures[7]} \n'

            with open(logfile_path, 'a') as logfile:
                print(data, file=logfile)
            print(data)

except KeyboardInterrupt:
    print("logging ended")
