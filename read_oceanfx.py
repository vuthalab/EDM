import numpy as np
import matplotlib.pyplot as plt

from headers.oceanfx import OceanFX

spec = OceanFX()

#np.savetxt('spectra/baseline.txt', spec.intensities)

plt.plot(spec.wavelengths, spec.transmission)
plt.xlim(400, 800)
plt.ylim(0, 110)
plt.xlabel('Wavelength (nm)')
plt.ylabel('Transmission (%)')
plt.show()

