#Import modules
import time
import os
import numpy as np

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
        read_success = False
        attempts = 0
        while not read_success:
            try:
                try:
                    pressures = P1.read_pressure_torr()
                    time.sleep(delay_time)
                    temperatures = [T1.read(channel_names) for channel_names in T1.thermometer_names] + [T2.read(channel_names) for channel_names in T2.thermometer_names]
                    time.sleep(delay_time)
                    heater_outputs = [T1.read(channel_names) for channel_names in T1.heater_names] + [T2.read(channel_names) for channel_names in T2.heater_names]
                    time.sleep(delay_time)
                    monitor_voltages = [L1.read(channel_names) for channel_names in L1.active_channels]
                    time.sleep(delay_time)
                    cell_flow = Mfc.get_flow_rate_cell()
                    time.sleep(delay_time)
                    neon_flow = Mfc.get_flow_rate_neon_line()
                    mfc_flows = [cell_flow, neon_flow]
                    time.sleep(delay_time)
                    data_dict = {'pressures' : pressures, 'temperatures' : temperatures, 'heaters' : heater_outputs, 'voltages' : monitor_voltages, 'flows' : mfc_flows}
                    publisher.send(data_dict)
                    if count == 0:
                        print('Publishing started. Time is', time.asctime(time.localtime()), '. Values are:', data_dict, '.\n')
                    #Can include some software interlocks here. Not sure that this is a great implementation.
                    if pressures > 1E-1:
                        T1.disable_output()
                        T2.disable_output()
                        Mfc.off()
                        raise ValueError('Pressure too high! Turning off heaters and mfcs.')
                    count+=1
                except ValueError:
                    print('Pressure too high! Turning off heaters and mfcs and exiting.')
                    raise Exception
                read_success = True
            except:
                time.sleep(delay_time)
                print("Failed to read. Trying again.")
                attempts+=1
                if (attempts >= 100):
                    break
    #print('Publishing complete. Time is', time.asctime(time.localtime()), '. Values are:', data_dict, '.\n')

def Melt(low_temp,high_temp,heat_rate,cool_rate,hold_time,wait_time):
    T1.ramp_temperature('heat saph', high_temp, heat_rate)
    initial_temp = T1.read('saph')
    heat_time = (high_temp - initial_temp) / heat_rate
    print('Beginning melt. Time is', time.asctime(time.localtime()), '. Ramping from', initial_temp, 'K to', high_temp, 'K in', heat_time, 's.\n')
    Publish(heat_time)
    print('Heating complete. Time is', time.asctime(time.localtime()), '. Holding for', hold_time, 's.\n')
    Publish(hold_time)
    T1.ramp_temperature('heat saph', low_temp, cool_rate)
    final_temp = T1.read('saph')
    cool_time = (final_temp - low_temp) / cool_rate
    print('Beginning cooldown. Time is', time.asctime(time.localtime()), '. Ramping from', final_temp, 'K to', low_temp, 'K in', cool_time, 's.\n')
    Publish(cool_time)
    print('Cooling complete. Time is', time.asctime(time.localtime()), '. Holding for', wait_time, 's.\n')
    Publish(wait_time)
    print('Melt complete. Time is', time.asctime(time.localtime()), '.\n')

def Grow(buffer_rate,neon_line_rate,growth_time):
    print('Beginning growth. Time is', time.asctime(time.localtime()), '. Growing at', buffer_rate, 'sccm in buffer cell,', neon_line_rate, 'sccm in neon line, for', growth_time, 's.\n')
    Mfc.set_flow_rate_cell(buffer_rate)
    Mfc.set_flow_rate_neon_line(neon_line_rate)
    Publish(growth_time)
    Mfc.set_flow_rate_cell(0.0)
    Mfc.set_flow_rate_neon_line(0.0)
    print('Growth complete. Time is ', time.asctime(time.localtime()), '.\n')

def Log_Parameters(root_dir, sequence_dict):
    #Create a folder inside folder root_dir to save the required parameters, labelled by the date.
    #Determine the current date for saved data
    day = time.strftime("%d")
    month = time.strftime("%m")
    monthName = time.strftime("%B")
    year = time.strftime("%Y")

    #Create save strings
    yearfolder = year + '/'
    monthfolder = month + '_' + monthName + '_' + year + '/'
    dayfolder = monthName + '_' + day + '/'

    #Open folder for saving data
    savefolder = root_dir + yearfolder + monthfolder + dayfolder
    savefolder = os.path.expanduser(savefolder)
    if not os.path.exists(savefolder):
        #If folder does not already exist, create it
        os.makedirs(savefolder)

    currenttime = time.asctime(time.localtime())
    currenttime = str.replace(currenttime , ':', ".")
    currenttime  = str.replace(currenttime , '  ', ' ')

    params_path = savefolder + currenttime + "_params.txt"

    mode = 'a' if os.path.exists(params_path) else 'w'
    with open(params_path, mode) as params_file:
        print(sequence_dict, file=params_file)

    print('Logging sequence params to', params_path, '.\n')

#Parameters
delay_time = 0.05 #Time between measurements in seconds
port = 5550 #Port for the publisher to broadcast on
topic = 'EDM_monitor' #Topic broadcast via the publisher
root_dir = "/home/vuthalab/Desktop/edm_data/logs/full_system/" #Where the logging happens

#Initialize devices
P1 = FRG730('/dev/agilent_pressure_gauge')
T1 = CTC100('192.168.0.104')
T2 = CTC100('192.168.0.107')
L1 = Labjack('470022275')
Mfc = MFC('470017292')
device_list = [P1,T1,T2,L1,Mfc]

#Configure device-specific settings
P1.set_torr()
T1.thermometer_names = ['saph','coll','bott hs','cell']
T1.heater_names = ['heat saph', 'heat coll']
T2.thermometer_names = ['srb4k', 'srb45k', '45k plate', '4k plate']
T2.heater_names = ['srb45k out', 'srb4k out']
L1.active_channels = ['AIN1','AIN2']

#Create a publisher
publisher = zmq_server_socket(port, topic)

#Create a sequence
try:
    #Start the sequence. Enable heaters.
    print('Running sequence. Time is', time.asctime(time.localtime()), '.\n')
    T1.enable_output()
    Mfc.off()

    #Define static parameters.
    params_dict = {'purpose': 'melt_test',
        'start_time' : time.asctime(time.localtime()),
        'end_time' : time.asctime(time.localtime()),
        'slow_heat_rate' :  0.025,
        'slow_cool_rate' : 0.025,
        'fast_heat_rate' : 1.0,
        'fast_cool_rate' : 1.0,
        'hold_time' : 5.0,
        'wait_time' : 120.0,
        'low_temp' : 8.0,
        'high_temp' : 25.0,
        'buffer_flow' : 0.0,
        'neon_flow' : 2.0,
        'growth_time' : 120.0*60.0}
    fast_rates = np.array([5.0, 2.0, 1.0, 0.7, 0.5, 0.2, 0.1, 0.05])

    Publish(10.0)

    #Perform individual sequences.
    for rate in fast_rates:
        params_dict['start_time'] = time.asctime(time.localtime())
        params_dict['fast_heat_rate'] = rate
        params_dict['fast_cool_rate'] = rate
        Melt(params_dict['low_temp'],params_dict['high_temp'],params_dict['slow_heat_rate'],params_dict['slow_cool_rate'],params_dict['hold_time'],params_dict['wait_time'])
        Melt(params_dict['low_temp'],params_dict['high_temp'],params_dict['fast_heat_rate'],params_dict['fast_cool_rate'],params_dict['hold_time'],params_dict['wait_time'])
        Grow(params_dict['buffer_flow'],params_dict['neon_flow'],params_dict['growth_time'])
        Publish(60.0)
        params_dict['end_time'] = time.asctime(time.localtime())
        Log_Parameters(root_dir, params_dict)

    #End of the sequence.
    print('Sequence complete. Time is', time.asctime(time.localtime()), '.\n')
except:
    print('Sequence error. Time is', time.asctime(time.localtime()), '. Turning off heaters and mfcs. \n')
    T1.disable_output()
    T2.disable_output()
    Mfc.off()
    publisher.close()

#Clean up.
T1.disable_output()
T2.disable_output()
Mfc.off()
publisher.close()
