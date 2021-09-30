import time


import numpy as np
import matplotlib.pyplot as plt

from colorama import Fore, Style

from uncertainties import ufloat

from headers.oceanfx import OceanFX, roughness_model
from headers.zmq_client_socket import connect_to

from headers.util import plot, uarray, nom


## SETTINGS ##
PLOT_TRANSMISSION = False
LOG_SCALE = False


## connect to publisher (spectrometer data)
monitor_socket = connect_to('spectrometer')

spec = OceanFX()

# Liveplot
plt.ion()
fig = plt.figure()
while True:
    # Get data
    ts, data = monitor_socket.grab_json_data()
    if data is not None:
        print(ts)

        # Unpack + convert data
        wavelengths = np.array(data['wavelengths'])
        intensities = data['intensities']


        intensities = uarray(intensities['nom'], intensities['std'])
        intensities -= spec.background

#        intensities = data['fit']['chisq-array'] # Plot chisq instead
#        intensities = data['fit']['num-points'] # Plot number of fitted points instead
#        intensities = uarray(data['intercepts']['nom'], data['intercepts']['std']) # Plot intercepts instead

        beta_0 = data['rough']['zero-order'][0]
        beta_2 = data['rough']['second-order'][0]
        beta_4 = data['rough']['fourth-order'][0]

        if PLOT_TRANSMISSION:
            # Transmission
            plot(wavelengths, 100 * intensities/spec.baseline, continuous=True, color='C0')

            model_pred = np.exp(roughness_model(wavelengths, beta_0, beta_2, beta_4))
            plt.plot(wavelengths, model_pred, alpha=0.5, color='C1', zorder=20)
            plt.ylabel('Transmission (%)')

            if LOG_SCALE:
                plt.ylim(1e-2, 110)
                plt.yscale('log')
            else:
                plt.ylim(0, 110)
        else:
            # Intensity
            plot(wavelengths, intensities, continuous=True)
            plt.ylabel('Intensity (counts/μs)')

            if LOG_SCALE:
                plt.yscale('log')
                plt.ylim(1e-6, 1e2)
            else:
                hene_mask = (wavelengths < 610) | (wavelengths > 650)
                saturation = max(nom(intensities)[hene_mask])
                plt.ylim(0, 1.1*saturation)

        plt.xlim(350, 1000)
        plt.xlabel('Wavelength (nm)')

        fig.canvas.draw()

    fig.canvas.flush_events()
    time.sleep(0.5)
