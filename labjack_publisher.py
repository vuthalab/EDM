# publisher for Hornet ion gauge

from labjack import ljm
import os
os.chdir('/home/vuthalab/gdrive/code/edm_control/headers')
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
delay_time = 0.5        #s, between measurements


# create a publisher for this topic and port
publisher = zmq_server_socket(port, topic)
counter = 0

def voltage_to_pressure(V):
    p = 10**(V-10) # from Hornet ion gauge manual, section 7
    return p

while True:
    try:
        read_success = False
        while not read_success:  # IT SEEMS LIKE BOTH THE TRY AND THE EXCEPT ALWAYS RUN??? WHY V wierd
            try:
            #voltage = ljm.eReadName(labjack_handle,"AIN0")
                voltage = ljm.eReadAddress(labjack_handle,0,3)
                time.sleep(delay_time)
                voltage2 = ljm.eReadAddress(labjack_handle,2,3)
                time.sleep(delay_time)
                read_success = True
            except:
                time.sleep(delay_time)
                print("read barfed")
        pressure = voltage_to_pressure(voltage)
        data_dict = {'pressure' : pressure, 'voltage' : voltage2}
        publisher.send(data_dict)
        time.sleep(delay_time)
        # change time.sleep to determine upload speed

        counter +=1
        if counter % 10 == 0:
            print(publisher.current_data)

    except KeyboardInterrupt: break
publisher.close()