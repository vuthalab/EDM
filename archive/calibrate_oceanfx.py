import time
import itertools

import numpy as np
import matplotlib.pyplot as plt

from colorama import Style

from headers.oceanfx import OceanFX
from headers.zmq_client_socket import connect_to

from headers.edm_util import show_interrupt_menu
from headers.util import nom, std, plot, uarray



spec = OceanFX()

def calibrate(
    name,
    time_limit=60,
    show_plot=False,
):
    print(f'Calibrating OceanFX {name} for {time_limit} seconds...')

    # connect to publisher
    samples = []
    start_time = time.monotonic()

    try:
        for i in itertools.count():
            spec.capture()
            print(f'\rSample {Style.BRIGHT}{i+1}{Style.RESET_ALL}', end='')
            wavelengths = spec.wavelengths
            spectrum = spec.intensities
            samples.append(spectrum)

            if time.monotonic() - start_time > time_limit: break

        samples = samples[1:] # Discard first sample (to avoid 'partial' spectrum).
        spectrum = sum(samples) / len(samples)
        print()


        if show_plot:
            print('Plotting...')
            plot(wavelengths, spectrum, continuous=True)
            plt.xlim(300, 900)
            plt.xlabel('Wavelength (nm)')
            plt.ylabel('Intensity (counts/us)')
            plt.title(name)
            plt.show()

        print(f'Saving {name} OceanFX calibration...')
        np.savetxt(f'calibration/{name}.txt', [nom(spectrum), std(spectrum)])
        print('Done.')

    except KeyboardInterrupt:
        show_interrupt_menu()



if __name__ == '__main__':
    choice = input('1 for baseline, 2 for background. ')
    if choice == '1':
        input('Unblock OceanFX, then press Enter.')
        calibrate('baseline', show_plot=True)
    elif choice == '2':
        input('Block OceanFX, then press Enter.')
        calibrate('background', time_limit=120, show_plot=True)
