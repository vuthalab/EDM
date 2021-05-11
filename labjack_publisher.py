# publisher for Hornet ion gauge

import time
import os
import itertools

from headers.labjack import ljm

os.chdir('/home/vuthalab/gdrive/code/edm_control')
from headers.zmq_server_socket import zmq_server_socket

labjack_serial = 470022275   # device serial number

load_success = False
while not load_success:
    try:
        labjack_handle = ljm.openS("T7","Ethernet",labjack_serial)
        time.sleep(1.0)
        load_success = True
    except:
        print("labjack not loaded, trying again ...")
        time.sleep(1.0)


port= 5550              # If port is in use, enter a different 4 digit port number
topic = "IGM401"        # Change this to whatever device you're going to use. Here it is set to the ion gauage we hope to interface using the labjack
delay_time = 0.1        #s, between measurements


# from Hornet ion gauge manual, section 7
def voltage_to_pressure(V): return 10**(V-10)

# create a publisher for this topic and port
with zmq_server_socket(port, topic) as publisher:
    for iteration in itertools.count():
        try:
            voltage = ljm.eReadAddress(labjack_handle,0,3)
            time.sleep(delay_time)

            voltage2 = ljm.eReadAddress(labjack_handle,2,3)
            time.sleep(delay_time)

            voltage3 = ljm.eReadAddress(labjack_handle,4,3)
        except:
            print("read barfed")
            continue

        pressure = voltage_to_pressure(voltage)
        data_dict = {'pressure' : pressure, 'voltage' : [voltage2, voltage3]}

        publisher.send(data_dict)
        time.sleep(delay_time)
        # change time.sleep to determine upload speed

        if iteration % 10 == 0:
            print(publisher.current_data)
