import numpy as np
import matplotlib.pyplot as plt

from colorama import Style

from headers.oceanfx import OceanFX
from headers.zmq_client_socket import zmq_client_socket

from headers.util import nom, std, plot, uarray


N_SAMPLES = 100


# Use this function in an emergency
# if you can't start the publisher.
# Might bias results a bit.
def calibrate_bare(name):
    spec = OceanFX()

    samples = []
    for i in range(N_SAMPLES):
        print('Sample', i+1)
        spec.capture()
        samples.append(spec.intensities)
    spectrum = sum(samples) / len(samples)

    print('Plotting...')
    plot(spec.wavelengths, spectrum, continuous=True)
    plt.xlim(300, 900)
    plt.xlabel('Wavelength (nm)')
    plt.ylabel('Intensity (%)')
    plt.title(name)
    plt.show()

    print('Saving...')
    np.savetxt(f'calibration/{name}.txt', [nom(spectrum), std(spectrum)])





connection_settings = {
    'ip_addr': 'localhost', # ip address
    'port': 5553, # our open port
    'topic': 'spectrometer', # device
}

def calibrate(name, num_samples=N_SAMPLES, plot=False):
    print(f'Calibrating OceanFX {name}...')
    # connect to publisher
    monitor_socket = zmq_client_socket(connection_settings)
    monitor_socket.make_connection()

    samples = []
    for i in range(num_samples):
        _, data = monitor_socket.blocking_read()
        print(f'\rSample {Style.BRIGHT}{i+1}/{num_samples}{Style.RESET_ALL}', end='')
        wavelengths = data['wavelengths']
        spectrum = data['intensities']
        samples.append(uarray(spectrum['nom'], spectrum['std']))
    monitor_socket.socket.close()
    spectrum = sum(samples) / len(samples)
    print()


    if plot:
        print('Plotting...')
        plot(wavelengths, spectrum, continuous=True)
        plt.xlim(300, 900)
        plt.xlabel('Wavelength (nm)')
        plt.ylabel('Intensity (%)')
        plt.title(name)
        plt.show()

    print(f'Saving {name} OceanFX calibration...')
    np.savetxt(f'calibration/{name}.txt', [nom(spectrum), std(spectrum)])



if __name__ == '__main__':
    input('Unblock OceanFX, then press Enter.')
    calibrate('baseline', plot=True)
    input('Block OceanFX, then press Enter.')
    calibrate('background', plot=True)
