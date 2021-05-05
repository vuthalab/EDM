import matplotlib.pyplot as plt

from interface.osa import OSA

gpib_address = 1 # Configurable on the OSA
osa = OSA(gpib_address)

# Get sample spectrum from OSA
wavelengths, levels = osa.get_spectrum('A')

# Plot data
plt.plot(wavelengths, levels)
plt.xlabel('Wavelength (nm)')
plt.ylabel('Power (dBm)')
plt.title(f'Ambient Spectrum')
plt.show()

osa.stop()
