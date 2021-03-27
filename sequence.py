#Import modules
import time

#Import class objects
from headers.FRG730 import FRG730
from headers.CTC100 import CTC100
from headers.Labjack import Labjack
from headers.mfc import MFC
from headers.zmq_server_socket import zmq_server_socket

#Convenient functions
#Start publishing the data for a specified amount of time
def Publish(publish_time):
    start_time = time.time()
    count = 0
    while ((time.time() - start_time) < publish_time):
        pressures = P1.read_pressure_torr()
        time.sleep(delay_time)
        temperatures = [T1.read(channel_names) for channel_names in T1.thermometer_names] + [T2.read(channel_names) for channel_names in T2.thermometer_names]
        time.sleep(delay_time)
        heater_outputs = [T1.read(channel_names) for channel_names in T1.heater_names] + [T2.read(channel_names) for channel_names in T2.heater_names]
        time.sleep(delay_time)
        monitor_voltages = [L1.read(channel_names) for channel_names in L1.active_channels]
        time.sleep(delay_time)
        mfc_flows = [Mfc.get_flow_rate_cell(), Mfc.get_flow_rate_neon_line()]
        time.sleep(delay_time)
        data_dict = {'pressures' : pressures, 'temperatures' : temperatures, 'heaters' : heater_outputs, 'voltages' : monitor_voltages, 'flows' : mfc_flows}
        publisher.send(data_dict)
        if count == 0:
            print('Publishing started. Time is ', time.asctime(time.localtime()), '. Values are: ', data_dict)
        #Can include some software interlocks here.
        if pressures > 1E-2:
            print('Pressure too high!')
            T1.disable_output()
            T2.disable_output()
            Mfc.set_flow_rate_cell(0.0)
            Mfc.set_flow_rate_neon_line(0.0)
        count+=1
    print('Publishing complete. Time is ', time.asctime(time.localtime()), '. Values are: ', data_dict)

def Melt(low_temp,high_temp,heat_rate,cool_rate,hold_time,wait_time):
    print('Beginning melt. Time is ', time.asctime(time.localtime()), '. Requested values are: ', low_temp,high_temp,heat_rate,cool_rate,hold_time,wait_time)
    T1.ramp_temperature('heat saph', high_temp, heat_rate)
    initial_temp = T1.read('saph')
    heat_time = (high_temp - initial_temp) / heat_rate
    Publish(heat_time)
    Publish(hold_time)
    T1.ramp_temperature('heat saph', low_temp, cool_rate)
    final_temp = T1.read('saph')
    cool_time = (final_temp - initial_temp) / cool_rate
    Publish(cool_time)
    Publish(wait_time)
    print('Melt complete. Time is ', time.asctime(time.localtime()))

def Grow(buffer_rate,neon_line_rate,grow_time):
    print('Beginning growth. Time is ', time.asctime(time.localtime()), '. Requested values are: ', buffer_rate,neon_line_rate,grow_time)
    Mfc.set_flow_rate_cell(buffer_rate)
    Mfc.set_flow_rate_neon_line(neon_line_rate)
    Publish(grow_time)
    Mfc.set_flow_rate_cell(0.0)
    Mfc.set_flow_rate_neon_line(0.0)
    print('Growth complete. Time is ', time.asctime(time.localtime()))


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

#Create a sequence
#Melt(5.0,25.0,0.25,0.25,60.0,60.0)
Grow(0.0,5.0,60.0)
Publish(60.0)

#Clean up.
publisher.close()
