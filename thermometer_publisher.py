# starts server to publish ion gauge pressure

# NOTE
# Use time.sleep to determine your data upload speed. If your
# pub_init time.sleep is < your client_init time.sleep, then your client
# socket will read less data than

import os
import time
import itertools

os.chdir("/home/vuthalab/gdrive/code/edm_control/")
from headers.zmq_server_socket import zmq_server_socket
from headers.CTC100 import CTC100

topic = 'CTC_100' # Change this to whatever device you're going to use.
port = 5551 # If port is in use, enter a different 4 digit port number.

delay_time = 0.1 # s, between measurements

# initialize devices
thermometers = [
    CTC100('192.168.0.104'),
    CTC100('192.168.0.107'),
]

for i, thermometer in enumerate(thermometers):
    if thermometer is None:
        print(f'Thermometer {i+1} was not loaded.')
        exit()

channel_names = [
    ['saph', 'coll', 'bott hs', 'cell'],
    ['srb4k', 'srb45k', '45k plate', '4k plate']
]
heater_names = [
    ['heat saph', 'heat coll'],
    ['srb45k out', 'srb4k out'],
]

# create a publisher for this topic and port
with zmq_server_socket(port, topic) as publisher:
    for iteration in itertools.count():
        temperatures = [
            thermometer.read(channel) for channel in channel_names[i]
            for i, thermometer in enumerate(thermometers)
        ]
        heaters = [
            thermometer.read(heater) for heater in heater_names[i]
            for i, thermometer in enumerate(thermometers)
        ]

        data_dict = {
            'temperatures': temperatures,
            'heaters': heaters
        }
        publisher.send(data_dict)

        time.sleep(delay_time)
        # change time.sleep to determine upload speed

        if iteration % 10 == 0:
            print(publisher.current_data)
