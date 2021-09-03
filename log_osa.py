import time
import itertools

import numpy as np
import matplotlib.pyplot as plt

from headers.ando_aq6317 import AndoAQ6317

from headers.util import nom, std, plot


# Name of file to save spectrum to
SAVE_NAME = 'Baseline_Later'


serial_port = '/dev/ttyUSB5' # TODO remap the serial port to something human-readable
gpib_address = 1 # Configurable on the OSA


# Initialize connection
with AndoAQ6317(serial_port, gpib_address) as osa:
    ###### Configure capture settings #####
#    osa.active_trace = 'c' # choose which trace to read

    osa.resolution = 2.0 # set resolution (nm) (*This is not correct*)
    osa.range = (780,920) # set range (nm)

    #osa.center() # self-center
    #osa.scale = 'log'

    #osa.upper_frequency = 347 # THz
    #osa.lower_frequency = 349 # THz

    osa.sweep_mode = 'repeat' # continuously sweep (for logging)
    #osa.trigger() # trigger once

    # Display configuration
    print('Getting configuration...')
    print()


    # Wait for trigger, then plot trace
    #osa.quick_plot()
    osa.live_plot()


    # Get some averaged spectra
    if False:
        for i in itertools.count():
            if True:
                wavelengths, power = osa.average_spectra(n=1, delay=10)

                data = np.array([wavelengths, nom(power), std(power)])
                np.savetxt(f'spectra/{SAVE_NAME}-{i:04d}.txt', data.T, header='wavelength (nm)\tpower (dB)\tpower uncertainty (dB)')
                print(f'Saved as spectra/{SAVE_NAME}-{i:04d}.txt')

                plot(wavelengths, power, continuous=True)
                plt.xlabel('Wavelength (nm)')
                plt.ylabel('Power (dB)')
                plt.show()
