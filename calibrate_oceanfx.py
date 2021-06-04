import numpy as np
import matplotlib.pyplot as plt

from headers.oceanfx import OceanFX

from headers.util import nom, std, plot

def calibrate(name):
    N_SAMPLES = 100

    spec = OceanFX()

    samples = []
    for i in range(128):
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
    np.savetxt(f'spectra/{name}.txt', [nom(spectrum), std(spectrum)])


input('Turn on broadband, then press Enter.')
calibrate('baseline')
input('Turn off broadband, then press Enter.')
calibrate('background')
