import time
import itertools

import numpy as np
import matplotlib.pyplot as plt

from colorama import Style

from headers.oceanfx import OceanFX
from headers.zmq_client_socket import zmq_client_socket

from headers.util import nom, std, plot, uarray



spec = OceanFX()

connection_settings = {
    'ip_addr': 'localhost', # ip address
    'port': 5553, # our open port
    'topic': 'spectrometer', # device
}

def calibrate(
    name,
    time_limit=60,
    show_plot=False,
):
    print(f'Calibrating OceanFX {name} for {time_limit} seconds...')

    # connect to publisher
    monitor_socket = zmq_client_socket(connection_settings)
    monitor_socket.make_connection()

    samples = []
    start_time = time.monotonic()
    for i in itertools.count():
        _, data = monitor_socket.blocking_read()
        print(f'\rSample {Style.BRIGHT}{i+1}{Style.RESET_ALL}', end='')
        wavelengths = data['wavelengths']
        spectrum = data['intensities']
        samples.append(uarray(spectrum['nom'], spectrum['std']))

        if time.monotonic() - start_time > time_limit: break
    monitor_socket.socket.close()

    spectrum = sum(samples) / len(samples)
    print()


    if show_plot:
        print('Plotting...')
        plot(wavelengths, spectrum, continuous=True)
        plt.xlim(300, 900)
        plt.xlabel('Wavelength (nm)')
        plt.ylabel('Intensity (%)')
        plt.title(name)
        plt.show()

    print(f'Saving {name} OceanFX calibration...')
    np.savetxt(f'calibration/{name}.txt', [nom(spectrum), std(spectrum)])
    print('Done.')



if __name__ == '__main__':
    input('Unblock OceanFX, then press Enter.')
    calibrate('baseline', show_plot=True)

#    input('Block OceanFX, then press Enter.')
#    calibrate('background', show_plot=True)
