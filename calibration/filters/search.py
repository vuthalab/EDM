"""Searches for best filter settings, given desired pass and stop bands."""

from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

from uncertainties import ufloat
from util import fit, plot


pass_wl = float(input('Passband center wavelength (nm)? '))
#pass_width = float(input('Passband center width (nm)? '))
pass_width = 15

stop_wl = float(input('Stopband center wavelength (nm)? '))
#stop_width = float(input('Stopband center width (nm)? '))
stop_width = 15


winner = (None, None, 0)

for filename in Path('.').glob('*.txt'):
    if filename.stem.endswith('cutoff'): continue

    with open(filename, 'r') as f:
        next(f)
        wavelengths = np.array([float(x) for x in next(f).split()[1:]])

        stop_idx = np.abs(wavelengths - stop_wl) < stop_width/2
        pass_idx = np.abs(wavelengths - pass_wl) < pass_width/2

        angles = []
        cutoffs = []
        for line in f:
            angle, *od = map(float, line.split())
            od = np.array(od)

            try:
                relative_od = np.min(od[stop_idx]) - np.max(od[pass_idx])
            except:
                continue

            if relative_od > winner[2]:
                winner = (filename.stem, angle, relative_od)

print(f'Optimal Filter: {winner[0].upper()}')
print(f'Optimal Angle: {winner[1]:.2f} degrees')
print(f'Relative OD: {winner[2]:.2f} dB')
