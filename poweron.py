import time

#Import class objects
from pulsetube_compressor import PulseTube
from headers.turbo import TurboPump
from headers.CTC100 import CTC100
from headers.mfc import MFC

from headers.zmq_client_socket import zmq_client_socket


MINUTE = 60
HOUR = 60 * MINUTE


# Initialize devices.
# Port numbers are defined in multiplexer.py.
T1 = CTC100(31415)
T2 = CTC100(31416)
mfc = MFC(31417)
turbo = TurboPump()
pt = PulseTube()


# Ensure turbo is running.
if turbo.operation_status != 'normal':
    # If not started, turn on and wait for spinup.
    turbo.on()
    time.sleep(10 * MINUTE)


# Make sure MFC is on. Slowly ramp down the saph temperature to liquid nitrogen temp.
mfc.off()
T1.enable_output()
T1.ramp_temperature('heat saph', 77, 1e-2)
pt.on()


# Wait for 45K sorb to drop below 70 K.
connection_settings = {
    'ip_addr': 'localhost', # ip address
    'port': 5551, # our open port
    'topic': 'edm-monitor', # device
}
monitor_socket = zmq_client_socket(connection_settings)
monitor_socket.make_connection()
while True:
    _, data = monitor_socket.blocking_read()
    temp = data['temperatures']['srb45k']
    print('45K Sorb:', temp, 'K', end='\r')
    if temp < 70: break
print()


# Let system cool naturally.
T1.disable_output()
