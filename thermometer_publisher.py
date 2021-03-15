# starts server to publish ion gauge pressure

# NOTE
# Use time.sleep to determine your data upload speed. If your
# pub_init time.sleep is < your client_init time.sleep, then your client
# socket will read less data than

import os
import time
os.chdir("/home/vuthalab/gdrive/code/edm_control/")
from headers.zmq_server_socket import zmq_server_socket
from headers.CTC100_ethernet import CTC100

topic = "CTC_100"                        # Change this to whatever device you're going to use.
port = 5551                             # If port is in use, enter a different 4 digit port number.

delay_time = 0.1 #s, between measurements

# initialize devices
thermometer_1 = CTC100('192.168.0.104')
thermometer_2 = CTC100('192.168.0.107')

if thermometer_1 is None:
    print("Thermometer 1 was not loaded.")
    if thermometer_2 is None:
        print("Thermometer 2 was not loaded.")
    exit()

# create a publisher for this topic and port
publisher = zmq_server_socket(port, topic)
counter = 0
channel_names_1 = ['saph','coll','bott hs','cell']
channel_names_2 = ['srb4k', 'srb45k', '45k plate', '4k plate']
heater_names_1 = ['heat saph', 'heat coll']
heater_names_2 = ['srb45k out', 'srb4k out']

while True:
    try:
        temperatures_1 = [thermometer_1.read(channel_names_1[i]) for i in [0,1,2,3]]
        temperatures_2 = [thermometer_2.read(channel_names_2[i]) for i in [0,1,2,3]]
        heater_out_1 = [thermometer_1.read(heater_names_1[i]) for i in [0,1]]
        heater_out_2 = [thermometer_2.read(heater_names_2[i]) for i in [0,1]]
        temperatures = temperatures_1 + temperatures_2
        heater_outputs = heater_out_1 + heater_out_2
        data_dict = {'temperatures' : temperatures, 'heaters' : heater_outputs}
        publisher.send(data_dict)
        time.sleep(delay_time)
        # change time.sleep to determine upload speed

        counter +=1
        if counter % 10 == 0:
            print(publisher.current_data)

    except KeyboardInterrupt: break
publisher.close()