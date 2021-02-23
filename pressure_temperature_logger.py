# log the pressure gauge and thermometer

import os
import zmq
import time
import numpy as np

os.chdir("/home/vuthalab/gdrive/code/edm_control/headers")
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

pause_time = 2 # seconds
# connection_settings = {'ip_addr': 'localhost',  # ip address
#                        'port': 5558,            # our open port
#                        'topic': 'FRG730'}       # device
# pressure_socket = zmq_client_socket(connection_settings)
# pressure_socket.make_connection()

connection_settings = {'ip_addr': 'localhost',  # ip address
                       'port': 5550,            # our open port
                       'topic': 'IGM401'}       # device
pressure1_socket = zmq_client_socket(connection_settings)
pressure1_socket.make_connection()

# connection_settings = {'ip_addr': 'localhost',  # ip address
#                        'port': 5551,            # our open port
#                        'topic': 'CTC100_1'}       # device
# temperature1_socket = zmq_client_socket(connection_settings)
# temperature1_socket.make_connection()

connection_settings = {'ip_addr': 'localhost',  # ip address
                       'port': 5552,            # our open port
                       'topic': 'CTC100_2'}       # device
temperature2_socket = zmq_client_socket(connection_settings)
temperature2_socket.make_connection()


## set up log file
root_dir = "/home/vuthalab/Desktop/edm_data/logs/full_system/"
folder = get_save_folder(root_dir) + '/'

logfile_path = folder + "system_log.txt"

mode = 'a' if os.path.exists(logfile_path) else 'w'
with open(logfile_path, mode) as logfile:
    logfile.write("# unix time [s]  \t pressure [torr] \t temperatures [K] \n")

print('Logging to folder ' + logfile_path)

    # logging loop

try:
    while True:
        current_time = time.time()
        # pressure = pressure_socket.read_on_demand()[1]['pressure']
        # temperatures1 = temperature1_socket.read_on_demand()[1]['temperatures']
        temperatures2 = temperature2_socket.read_on_demand()[1]['temperatures']
        pressure1 = pressure1_socket.read_on_demand()[1]['pressure']
        pdvoltage = pressure1_socket.read_on_demand()[1]['voltage']

        if pressure1 > 1e-12: #correcting against ocassional bugs in reading
            # data = f'{current_time} \t {pdvoltage} \t {pressure1} \t {temperatures1[0]} \t {temperatures1[1]} \t {temperatures1[2]} \t {temperatures1[3]} \t {temperatures2[0]} \t {temperatures2[1]} \t {temperatures2[2]} \t {temperatures2[3]} \n'
            data = f'{current_time} \t {pdvoltage} \t {pressure1} \t {temperatures2[0]} \t {temperatures2[1]} \t {temperatures2[2]} \t {temperatures2[3]} \n'

            with open(logfile_path, 'a') as logfile:
                logfile.write(data)

            print(data)
            time.sleep(pause_time)

except KeyboardInterrupt:
    print("logging ended")