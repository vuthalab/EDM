import numpy as np
import matplotlib.pyplot as plt

from headers.oceanfx import OceanFX

from headers.util import nom, std, plot

spec = OceanFX()
print(spec.transmission_scalar)

plot(spec.wavelengths, spec.transmission, continuous=True)
plt.xlim(400, 800)
plt.ylim(-10, 110)
plt.xlabel('Wavelength (nm)')
plt.ylabel('Transmission (%)')
plt.show()

