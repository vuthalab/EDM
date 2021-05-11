# starts server to publish ion gauge pressure

# NOTE
# Use time.sleep to determine your data upload speed. If your
# pub_init time.sleep is < your client_init time.sleep, then your client
# socket will read less data than

import os
import time
import itertools

os.chdir('/home/vuthalab/gdrive/code/edm_control')
from headers.zmq_server_socket import zmq_server_socket
from headers.FRG730 import FRG730


topic = "FRG730"                        # Change this to whatever device you're going to use.
port = 5553                             # If port is in use, enter a different 4 digit port number.

delay_time = 0.1 #s, between measurements

# initialize device
topic_device = FRG730('/dev/agilent_pressure_gauge')   # Change this to whatever device you want to connect with the zmq socket.
topic_device.set_torr()
if topic_device is None:
    print("No device was loaded.")
    exit()

# create a publisher for this topic and port
with zmq_server_socket(port, topic) as publisher:
    for iteration in itertools.count():
        pressure = topic_device.read_pressure_torr()
        data_dict = {'pressure' : pressure}

        publisher.send(data_dict)
        time.sleep(delay_time)
        # change time.sleep to determine upload speed

        if iteration % 10 == 0:
            print(publisher.current_data)
