# log pressures from the FRG 730 ion gauge & IGM 401 ion gauge

import os
import zmq
import time
import numpy as np

os.chdir("/home/vuthalab/gdrive/code/edm_control/headers")
from headers.zmq_client_socket import zmq_client_socket


## create timestamped data folder
def get_save_folder(root_dir):
    # Create a folder inside folder root_dir to save all recorded data, labelled by the date. Returns the full path to the folder
    #Add a pointless comment.
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

pause_time = 5 # seconds
connection_settings = {'ip_addr': 'localhost',  # ip address
                       'port': 5558,            # our open port
                       'topic': 'FRG730'}       # device
pressure_socket = zmq_client_socket(connection_settings)
pressure_socket.make_connection()

connection_settings = {'ip_addr': 'localhost',  # ip address
                       'port': 5550,            # our open port
                       'topic': 'IGM401'}       # device
pressure2_socket = zmq_client_socket(connection_settings)
pressure2_socket.make_connection()


## set up log file
root_dir = "/home/vuthalab/Desktop/edm_data/logs/pressure/"
folder = get_save_folder(root_dir) + '/'

logfile_path = folder + "pressure_log.txt" #your text_file name

mode = 'a' if os.path.exists(logfile_path) else 'w'
with open(logfile_path, mode) as logfile:
    logfile.write("# unix time [s]  \t pressure [torr]\n")

print('Logging to folder ' + logfile_path)

    # logging loop

try:
    while True:
        current_time = time.time()
        pressure = pressure_socket.read_on_demand()[1]['pressure']
        pressure2 = pressure2_socket.read_on_demand()[1]['pressure']

        if pressure > 1e-12: #correcting against ocassional bugs in reading
            data = f'{current_time} \t {pressure} \t {pressure2} \n'

            if pressure > 1e-5: #warning if pressure gets too high
                duration = 1 #s
                freq = 440 #Hz
                os.system('play -nq -t alsa synth {} sine {}'.format(duration,freq))

            with open(logfile_path, 'a') as logfile:
                logfile.write(data)

            print(data)
            time.sleep(pause_time)

except KeyboardInterrupt:
    print("logging ended")