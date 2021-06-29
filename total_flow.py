"""
Computes total amount of neon used over a specific period.

You must run extract_logs.py first with buffer cell and neon flow enabled
to create the appropriate extract.txt.
"""
from datetime import datetime

import numpy as np

from colorama import Fore, Style
from uncertainties import ufloat

from headers.util import display, uarray, nom, std


# mfc correction factors
CALIBRATION_FACTORS = {
    'buffer': 1.46/1.39, # Ne/Ar
    'neon': 1.46/1.00, # Ne/N2
}


sep = f'{Style.RESET_ALL}{Style.DIM}｜{Style.RESET_ALL}'

def format_line(label, value):
    return f'{Fore.GREEN}{label}{Style.RESET_ALL}{Style.BRIGHT}{value:6.1f}{Style.RESET_ALL} {Style.DIM}L'



total = np.array([0, 0], dtype=float)

with open('extract.txt', 'r') as f:
    next(f)
    last = None
    for i, line in enumerate(f):
        timestamp, buffer_flow, neon_flow, buffer_uncertainty, neon_uncertainty = map(float, line.split())

        # Correct for offsets + calibration
        buffer_flow -= 0.02
        buffer_flow *= CALIBRATION_FACTORS['buffer']
        neon_flow -= 0.005
        neon_flow *= CALIBRATION_FACTORS['neon']

        curr = np.array([timestamp, buffer_flow, neon_flow])

        if last is not None:
            # Trapezoidal method
            delta_t = (timestamp - last[0]) / 60 # minutes
            total += 0.5 * (curr[1:] + last[1:]) * delta_t * 1e-3 # liters

        if (i+1) % 2000 == 0:
            print(
                datetime.fromtimestamp(timestamp).strftime('\r[%Y-%m-%d]'),
                f'{Style.BRIGHT}{round(i/1e3):>3d}k{Style.RESET_ALL} {Fore.YELLOW}lines processed',
                sep,
                format_line('buffer cell', total[0]),
                sep,
                format_line('neon line', total[1]),
                sep,
                format_line('total', sum(total)),
                end=f'{Style.RESET_ALL}'
            )

        last = curr
print()
