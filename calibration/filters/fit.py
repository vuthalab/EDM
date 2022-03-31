from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

from uncertainties import ufloat
from util import fit, plot


def model(angle, nominal_cutoff, ior, angle_offset):
    return nominal_cutoff * np.sqrt(1 - np.square(np.sin((angle - angle_offset) * np.pi/180)/ior))

for filename in Path('.').glob('*.txt'):
    if filename.stem.endswith('cutoff'): continue

    print(filename)
    with open(filename, 'r') as f:
        name = filename.stem
        next(f)
        wavelengths = np.array([float(x) for x in next(f).split()[1:]])
        mask = (wavelengths > 750)
        wavelengths = wavelengths[mask]

        angles = []
        cutoffs = []
        for line in f:
            angle, *od = map(float, line.split())
            try:
                od = np.array(od)[mask]
            except:
                continue

            if name.startswith('fel') or 'lp' in name:
                idx = np.argmax(od < 10) # Longpass
            elif name.startswith('fes') or 'sp' in name:
                idx = np.argmax(od > 10) # Shortpass
            else:
                # Bandpass
                idx = round(np.median(np.where(od < 3)[0]))

            cutoff = wavelengths[idx]
            angles.append(angle)
            cutoffs.append(ufloat(cutoff, np.mean(np.diff(wavelengths))))

        p0 = {
            'nominal wavelength': (800, 'nm'),
            'index of refaction': (1, ''),
            'angle offset': (0, '°'),
        }
        params, meta, residuals = fit(model, angles, cutoffs, p0)

        plt.figure(figsize=(8, 6))
        plot(
            angles, cutoffs, 
            model=model, meta=meta, params=params, x_min=-42, x_max=42,
            text_pos=(0.02, 'bottom')
        )
        plt.xlabel('Angle (°)')
        plt.ylabel('10 dB Wavelength Cutoff (nm)')
        plt.title(f'Wavelength Cutoff vs Angle for {filename.stem.upper()} Filter')
        plt.tight_layout()
        plt.savefig(f'{filename.stem}-cutoff.pdf')
        plt.close()

        angles = np.linspace(0, 40, 41)
        noms = model(angles, params[0].n, params[1].n, 0)
        np.savetxt(
            f'{filename.stem}-cutoff.txt',
            np.array([angles, noms]).T,
            header='Angle (deg)\tCutoff (nm)',
            delimiter = '\t', fmt='%.4f'
        )
