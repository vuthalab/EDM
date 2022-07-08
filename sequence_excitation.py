"""Takes a fast emission spectrum with the Ximea."""

from pathlib import Path
import time 
import itertools
import os

import numpy as np 
import matplotlib.pyplot as plt

from uncertainties import ufloat
from headers.util import unweighted_mean, nom

from api.pump_laser import PumpLaser
from headers.usbtmc import USBTMCDevice
from headers.ximea_camera import Ximea
from headers.elliptec_rotation_stage import ElliptecRotationStage


save_name = Path('/home/vuthalab/Desktop/edm_data/fluorescence/excitation/4.8K.txt')
save_name.parent.mkdir(exist_ok=True)

regions_of_interest = np.array([
    787.8,
    815.5,
    828,
    859.5,
    869.1,
    903.5,
    922
])

ximea = Ximea(exposure = 10)
pump = PumpLaser()

pump.source = None
time.sleep(3)


# Take background
background = []
print('Calibrating Ximea background.')
for i in range(5):
    print(i)
    ximea.capture(fresh_sample=True)
    background.append(ximea.raw_rate)
background = unweighted_mean(background)
print('Ximea Background:', 1e-6*background, 'Mcounts/s')


pump.source = 'tisaph-high'
pump._min_speed = 50
time.sleep(3)

delta = 1 # Delta wavelength per step
power_calibration_factor = 26/1 # Manually determined
with open(save_name, 'a') as f:
    while True:
        # Take data
        power = []
        wavelength = []
        rates = []
        print('Ximea foreground.')
        for i in range(3):
            print(f'{i} | {ximea.saturation:6.2} %', end='\r')
            power.append(pump.pm_power)
            wavelength.append(pump.wavelength)
            ximea.capture(fresh_sample=True)
            rates.append(ximea.raw_rate)

        power = unweighted_mean(power) * power_calibration_factor
        wavelength = unweighted_mean(wavelength)
        rate = ufloat(np.median(rates), np.std(rates)) - background

        # Save data
        print(wavelength, ' nm |', power, 'mW |', rate * 1e-6, 'Mcounts/s')
        print(
            time.time(),
            wavelength.n, wavelength.s,
            power.n, power.s,
            rate.n, rate.s,
            file=f, flush=True
        )

        # Sweep wavelength in one direction until wraparound, then reverse.
        try:
            curr = pump.wavelength
            if np.min(np.abs(curr - regions_of_interest)) < 2:
                pump.wavelength = curr + 0.2 * delta
            else:
                pump.wavelength = pump.wavelength + 2 * delta
        except ValueError:
            delta *= -1

        # TEMP
        if pump.wavelength > 935: delta = -1
        if pump.wavelength < 743: delta = 1
