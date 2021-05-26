import numpy as np
import matplotlib.pyplot as plt

from headers.oceanfx import OceanFX

from headers.util import nom, std, plot

N_SAMPLES = 100
NAME = 'baseline'

spec = OceanFX()

samples = []
for i in range(128):
    print('Sample', i+1)
    samples.append(spec.intensities)
spectrum = sum(samples) / len(samples)

np.savetxt(f'spectra/{NAME}.txt', [nom(spectrum), std(spectrum)])

print('Plotting...')
plot(spec.wavelengths, spectrum, continuous=True)
plt.xlim(300, 900)
#plt.ylim(0, 110)
plt.xlabel('Wavelength (nm)')
plt.ylabel('Intensity (%)')
plt.show()

