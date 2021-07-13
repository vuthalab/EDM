import time


import numpy as np
import matplotlib.pyplot as plt

from colorama import Fore, Style

from uncertainties import ufloat

from headers.oceanfx import OceanFX, roughness_model
from headers.zmq_client_socket import zmq_client_socket

from headers.util import plot, uarray, nom


## SETTINGS ##
PLOT_TRANSMISSION = False
LOG_SCALE = True


## connect to publisher (spectrometer data)
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
    # Get data
    _, data = monitor_socket.grab_json_data()

    if data is not None:
        # Unpack + convert data
        wavelengths = np.array(data['wavelengths'])
        intensities = data['intensities']


        intensities = uarray(intensities['nom'], intensities['std'])
        intensities -= spec.background

        I0 = data['trans']['unexpl'][0]
        rough = data['rough']['surf'][0]
        fourth_order_coefficient = data['rough']['fourth-order'][0]

        if PLOT_TRANSMISSION:
            # Transmission
            plot(wavelengths, 100 * intensities/spec.baseline, continuous=True, color='C0')

            model_pred = roughness_model(wavelengths, I0, rough, fourth_order_coefficient)
            plt.plot(wavelengths, model_pred, alpha=0.5, color='C1', zorder=20)
            plt.ylabel('Transmission (%)')
            plt.ylim(0, 110)
        else:
            # Intensity
            plot(wavelengths, intensities, continuous=True)
            plt.ylabel('Intensity (counts/μs)')

            if LOG_SCALE:
                plt.yscale('log')
                plt.ylim(1e-2, 1e3)
            else:
                hene_mask = (wavelengths < 610) | (wavelengths > 650)
                saturation = max(nom(intensities)[hene_mask])
                plt.ylim(0, 1.1*saturation)

        plt.xlim(350, 1000)
        plt.xlabel('Wavelength (nm)')

        fig.canvas.draw()

    fig.canvas.flush_events()
    time.sleep(0.5)
