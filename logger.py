# log the pressure gauge and thermometer

import os
import zmq
import time
import numpy as np

os.chdir("/home/vuthalab/gdrive/code/edm_control/")
#from zmq_client_socket import zmq_client_socket
from headers.zmq_client_socket import zmq_client_socket


## create timestamped data folder
def get_save_folder(root_dir):
    # Create a folder inside folder root_dir to save all recorded data, labelled by the date. Returns the full path to the folder

    #Determine the current date for saved data
    day = time.strftime("%d")
    month = time.strftime("%m")
    monthName = time.strftime("%B")
    year = time.strftime("%Y")

    #Create save strings
    yearfolder = year + '/'
    monthfolder = month + '_' + monthName + '_' + year + '/'
    dayfolder = monthName + '_' + day + '/'

    timefolder = time.asctime(time.localtime())
    timefolder = str.replace(timefolder , ':', ".")
    timefolder  = str.replace(timefolder , '  ', ' ')

    #Open folder for saving data
    savefolder = root_dir + yearfolder + monthfolder + dayfolder + timefolder
    savefolder = os.path.expanduser(savefolder)
    if not os.path.exists(savefolder):
        #If folder does not already exist, create it
        os.makedirs(savefolder)
    return savefolder

## connect
connection_settings = {'ip_addr': 'localhost',  # ip address
                       'port': 5550,            # our open port
                       'topic': 'EDM_monitor'}       # device
monitor_socket = zmq_client_socket(connection_settings)
monitor_socket.make_connection()

## set up log file
root_dir = "/home/vuthalab/Desktop/edm_data/logs/full_system/"
folder = get_save_folder(root_dir) + '/'

logfile_path = folder + "system_log.txt"

mode = 'a' if os.path.exists(logfile_path) else 'w'
with open(logfile_path, mode) as logfile:
    logfile.write("# unix time [s]  \t pressure [torr] \t flow [sccm] \t flow [sccm] \t voltage [V] \t voltage [V] \t power [W] \t power [W] \t power [W] \t power [W] \t temperatures [K] \t temperatures [K] \t temperatures [K] \t temperatures [K] \t temperatures [K] \t temperatures [K] \t temperatures [K] \t temperatures [K] \n")

print('Logging to folder ' + logfile_path)

    # logging loop

try:
    while True:
        current_time = time.time()
        pressures = monitor_socket.read_on_demand()[1]['pressures']
        temperatures = monitor_socket.read_on_demand()[1]['temperatures']
        heaters = monitor_socket.read_on_demand()[1]['heaters']
        voltages = monitor_socket.read_on_demand()[1]['voltages']
        flows = monitor_socket.read_on_demand()[1]['flows']

        if pressures > 1e-12: #correcting against ocassional bugs in reading
            data = f'{current_time} \t {pressures} \t {flows[0]} \t {flows[1]} \t {voltages[0]} \t {voltages[1]} \t {heaters[0]} \t {heaters[1]} \t {heaters[2]} \t {heaters[3]} \t {temperatures[0]} \t {temperatures[1]} \t {temperatures[2]} \t {temperatures[3]} \t {temperatures[4]} \t {temperatures[5]} \t {temperatures[6]} \t {temperatures[7]} \n'

            with open(logfile_path, 'a') as logfile:
                logfile.write(data)

            print(data)

except KeyboardInterrupt:
    print("logging ended")