from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

from uncertainties import ufloat
from util import uarray, plot, fit, unweighted_mean, nom, std


ximea_qe = 7e-3
collection_efficiency = 0.22e-2
homogeneous_broadening_factor = 1e-3
sigma = 3/(2*np.pi) * (860e-9)**2 * homogeneous_broadening_factor

crystal_area = np.pi/4 * 12.7e-3**2
thickness = 8e-6

extraction_efficiency = 0.01
molecules_per_percent_shot = 1e9

temps = []
sticking = []
for filename in Path('data').glob('*.npz'):
    run = int(filename.stem[-1])
    data = np.load(filename)

    # Compute integrated absorption
    dips = uarray(*data['dips']) - 0.2
    t = data['dip_times'][0]
#    t = np.linspace(0, 60, len(dips))
    absorption = 30 * (0.5 * (dips[1:] + dips[:-1]) * np.diff(t)).sum() # %-shots

    total_yield = extraction_efficiency * absorption * molecules_per_percent_shot # convert to total molecules.

#    plot(t, dips)
#    plt.show()

    power = ufloat(*data['power'])
    photon_flux = 1e-3 * power / (6.626e-34 * 348676.3e9)

    count_rate = ufloat(*data['rate'])
    emission_rate = count_rate / (ximea_qe * collection_efficiency)

#    if run < 6: emission_rate *= 10

    signal = emission_rate / photon_flux # ~ Absorption fraction.

    density = signal / (sigma * thickness)
    fluorescence_estimate = density * crystal_area * thickness

    temps.append(data['temperature'])
    sticking.append(fluorescence_estimate / total_yield)
sticking = np.array(sticking)
temps = np.array(temps)

# Bucket according to temperature.
temps_clean = np.sort(np.unique(temps))
sticking_clean = []
for t in temps_clean:
    mask = np.abs(temps - t) < 0.02
    sticking_clean.append(unweighted_mean(sticking[mask]))

def model(t, height, t_crit):
    return height * np.exp(-t/t_crit)

p0 = {
    'scale': (1e-3, 'arb. units'),
    'temperature scale': (2, 'K'),
}
params, meta, residuals = fit(model, temps_clean, sticking_clean, p0)

np.savetxt(
    'loading-factor.txt',
    np.array([temps_clean, nom(sticking_clean), std(sticking_clean)]).T,
    header='Temperature (K)\tLoading Factor',
    delimiter='\t'
)

#t_interp = np.linspace(4, 7, 512)
plot(
    temps_clean, sticking_clean,
#    params=params, meta=meta, model=model, x_min=4, x_max=7.5,
#    text_pos=(0.02, 'bottom')
)
#plt.plot(t_interp, model(t_interp, 1))
plt.yscale('log')
plt.ylabel('Loading Factor')
plt.xlabel('Temperature (K)')
plt.legend()
plt.show()
