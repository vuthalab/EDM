import time

import numpy as np
import matplotlib.pyplot as plt

from headers.oceanfx import OceanFX
from headers.zmq_client_socket import zmq_client_socket

from headers.util import plot, uarray


## connect to publisher
connection_settings = {
    'ip_addr': 'localhost', # ip address
    'port': 5553, # our open port
    'topic': 'spectrometer', # device
}
monitor_socket = zmq_client_socket(connection_settings)
monitor_socket.make_connection()

spec = OceanFX()

# Liveplot
plt.ion()
fig = plt.figure()
while True:
    _, data = monitor_socket.blocking_read()

    wavelengths = data['wavelengths']
    intensities = data['intensities']

    intensities = uarray(intensities['nom'], intensities['std'])
    intensities -= spec.background


    if True:
        # Intensity
        plot(wavelengths, intensities, continuous=True)
        plt.ylabel('Intensity (%)')
    else:
        # Transmission
        plot(wavelengths, 100 * intensities/spec.baseline, continuous=True)
        plt.ylabel('Transmission (%)')


    plt.ylim(0, 110)
    plt.xlim(350, 750)
    plt.xlabel('Wavelength (nm)')

    fig.canvas.draw()
    fig.canvas.flush_events()
    time.sleep(0.5)
