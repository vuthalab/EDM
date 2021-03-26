#Import modules
import time

#Import class objects
from headers.FRG730 import FRG730
from headers.CTC100 import CTC100
from headers.Labjack import Labjack
from headers.mfc import MFC
from headers.zmq_server_socket import zmq_server_socket

#Parameters
delay_time = 0.05 #Time between measurements in seconds
publish_time = 60.0 #Time to publish the data in seconds
port = 5550 #Port for the publisher to broadcast on
topic = 'EDM_monitor' #Topic broadcast via the publisher

#Initialize devices
P1 = FRG730('/dev/agilent_pressure_gauge')
T1 = CTC100('192.168.0.104')
T2 = CTC100('192.168.0.107')
L1 = Labjack('470022275')
Mfc = MFC('470017292')
device_list = [P1,T1,T2,L1,Mfc]

#Create a publisher
publisher = zmq_server_socket(port, topic)

#Configure device-specific settings
P1.set_torr()
T1.thermometer_names = ['saph','coll','bott hs','cell']
T1.heater_names = ['heat saph', 'heat coll']
T2.thermometer_names = ['srb4k', 'srb45k', '45k plate', '4k plate']
T2.heater_names = ['srb45k out', 'srb4k out']
L1.active_channels = ['AIN1','AIN2']

#Start publishing the data for a specified amount of time
start_time = time.time()
while (time.time - start_time) < publish_time:
    pressures = P1.read_pressure_torr()
    time.sleep(delay_time)
    temperatures = [T1.read(channel_names) for channel_names in T1.thermometer_names] + [T2.read(channel_name) for channel_names in T2.thermometer_names]
    time.sleep(delay_time)
    heater_outputs = [T1.read(channel_names) for channel_names in T1.heater_names] + [T2.read(channel_name) for channel_names in T2.heater_names]
    time.sleep(delay_time)
    monitor_voltages = [L1.read(channel_names) for channel_names in L1.active_channels]
    time.sleep(delay_time)
    mfc_flows = [Mfc.get_flow_rate_cell(), Mfc.get_flow_rate_neon_line()]
    time.sleep(delay_time)
    data_dict = {'pressures' : pressures, 'temperatures' : temperatures, 'heaters' : heater_outputs, 'voltages' : monitor_voltages, 'flows' : mfc_flows}
    publisher.send(data_dict)
    print(data_dict)



