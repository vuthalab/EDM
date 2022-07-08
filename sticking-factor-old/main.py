import numpy as np
import matplotlib.pyplot as plt

from uncertainties import ufloat
from util import uarray, plot


temps = [5.20, 6, 6.2, 6.6]
sticking = []
for temperature in temps:
    data = np.load(f'{temperature:.2f}K.npz')

    # Compute integrated absorption
    dips = uarray(*data['dips']) - 0.3
#    t = data['dip_times'][0]
    t = np.linspace(0, 60, len(dips))
    absorption = (0.5 * (dips[1:] + dips[:-1]) * np.diff(t)).sum()

    plot(t, dips)
    plt.show()

    signal = ufloat(*data['rate']) / ufloat(*data['power'])
    print(ufloat(*data['rate']))
    print(ufloat(*data['power']))
    print(temperature, absorption, signal)

    sticking.append(signal / absorption)

plot(temps, sticking)
plt.show()
