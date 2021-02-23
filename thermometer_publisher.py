# starts server to publish ion gauge pressure

# NOTE
# Use time.sleep to determine your data upload speed. If your
# pub_init time.sleep is < your client_init time.sleep, then your client
# socket will read less data than

import os
import time
os.chdir('/home/vuthalab/gdrive/code/edm_control/headers')
from headers.zmq_server_socket import zmq_server_socket
from headers.CTC100 import CTC100

topic = "CTC100_1"                        # Change this to whatever device you're going to use.
port = 5551                             # If port is in use, enter a different 4 digit port number.

delay_time = 0.5 #s, between measurements

# initialize device
thermometer = CTC100('/dev/ctc100_1')   # what the hell is the device address for the CTC controller?
if thermometer is None:
    print("No device was loaded.")
    exit()

# create a publisher for this topic and port
publisher = zmq_server_socket(port, topic)
counter = 0
channel_names = ['saph','coll','bott hs','east hs']

while True:
    try:
        temperatures = [thermometer.read(channel_names[i]) for i in [0,1,2,3]]
        data_dict = {'temperatures' : temperatures}
        publisher.send(data_dict)
        time.sleep(delay_time)
        # change time.sleep to determine upload speed

        counter +=1
        if counter % 10 == 0:
            print(publisher.current_data)

    except KeyboardInterrupt: break
publisher.close()