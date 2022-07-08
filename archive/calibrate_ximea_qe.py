from pathlib import Path
import time

import numpy as np

from api.pump_laser import PumpLaser
from headers.ti_saph import TiSapphire
from headers.ximea_camera import Ximea
from usb_power_meter.Power_meter_2 import PM16 
from headers.elliptec_rotation_stage  import ElliptecRotationStage

from uncertainties import ufloat
from headers.util import unweighted_mean, nom

folder = Path(f'/home/vuthalab/Desktop/edm_data/ximea-qe-2')
folder.mkdir(exist_ok=True)

# Start scan
pump = PumpLaser()
ximea = Ximea(exposure=0.0001)

# Take background
pump.source = None
time.sleep(3)
background = []
pm_background = []
print('Calibrating Ximea background.')
for i in range(30):
    print(i)
    ximea.capture(fresh_sample=True)
    background.append(ximea.raw_rate)
    pm_background.append(pump.pm_power)
    time.sleep(0.25)
background = unweighted_mean(background)
pm_background = unweighted_mean(pm_background)
print('Ximea Background:', 1e-6*background, 'Mcounts/s')
print('Power Meter Background:', 1e6*pm_background, 'uW')


pump.source = 'tisaph-low'
time.sleep(3)

delta = 1 # Delta wavelength per step
power_calibration_factor = 1/(14.0/0.820) # Manually determined
with open(folder / 'data.txt', 'a') as f:
    while True:
        # Take data
        power = []
        wavelength = []
        rates = []
        print('Ximea foreground.')
        for i in range(10):
            print(f'{i} | {ximea.saturation:6.2} %', end='\r')
            power.append(pump.pm_power)
            wavelength.append(pump.wavelength)
            ximea.capture(fresh_sample=True)
            rates.append(ximea.raw_rate)
            time.sleep(0.25)

        power = (unweighted_mean(power) - pm_background) * power_calibration_factor
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
            pump.wavelength = pump.wavelength + delta
        except ValueError:
            delta *= -1

        # TEMP
        if pump.wavelength > 935: delta = -1
        if pump.wavelength < 743: delta = 1
