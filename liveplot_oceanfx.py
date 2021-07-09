import time


import numpy as np
import matplotlib.pyplot as plt

from colorama import Fore, Style

from uncertainties import ufloat

from headers.oceanfx import OceanFX, roughness_model
from headers.zmq_client_socket import zmq_client_socket

from headers.util import plot, uarray


## connect to publisher (spectrometer data)
connection_settings = {
    'ip_addr': 'localhost', # ip address
    'port': 5553, # our open port
    'topic': 'spectrometer', # device
}
monitor_socket = zmq_client_socket(connection_settings)
monitor_socket.make_connection()

## connect to publisher
connection_settings = {
    'ip_addr': 'localhost', # ip address
    'port': 5551, # our open port
    'topic': 'edm-monitor', # device
}
publisher_socket = zmq_client_socket(connection_settings)
publisher_socket.make_connection()

spec = OceanFX()

# Liveplot
plt.ion()
fig = plt.figure()
while True:
    # Get data
    _, spec_data = monitor_socket.blocking_read()
    _, data = publisher_socket._decode(publisher_socket.grab_data())

    # Unpack + convert data
    wavelengths = np.array(spec_data['wavelengths'])
    intensities = spec_data['intensities']
    raw_intensities = spec_data['raw_intensities']
    integration_time = spec_data['integration_time']

    intensities = uarray(intensities['nom'], intensities['std'])
    intensities -= spec.background

    raw_intensities = uarray(raw_intensities['nom'], raw_intensities['std'])

    I0 = data['trans']['unexpl'][0]
    rough = data['rough']['surf'][0]

    if True:
        # Intensity (counts/us)
        plot(wavelengths, intensities, continuous=True)
        plt.ylabel('Intensity (counts/μs)')

        # Raw intensity (counts)
#        plot(wavelengths, raw_intensities, continuous=True)
#        plt.ylabel('Intensity (counts)')
    else:
        # Transmission
        plot(wavelengths, 100 * intensities/spec.baseline, continuous=True, color='C0')
        plt.plot(wavelengths, roughness_model(wavelengths, I0, rough), alpha=0.5, color='C1')
        plt.ylabel('Transmission (%)')
        plt.ylim(0, 110)


    plt.xlim(350, 1000)
    plt.xlabel('Wavelength (nm)')

    fig.canvas.draw()
    fig.canvas.flush_events()
    print(f'{Fore.YELLOW}Integration Time{Style.RESET_ALL}: {Style.BRIGHT}{integration_time}{Style.RESET_ALL} μs', end='\r')
    time.sleep(0.5)
