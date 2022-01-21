from pathlib import Path
import time 

import numpy as np 
import matplotlib.pyplot as plt
from PIL import Image

from uncertainties import ufloat
from headers.util import unweighted_mean, nom, display
from headers.zmq_client_socket import connect_to

# Devices
from headers.verdi import Verdi
from api.pump_laser import EOM, PumpLaser
from usb_power_meter.Power_meter_2 import PM16 


pump = PumpLaser()
pm = PM16('/dev/power_meter')

pump.source = 'tisaph'
pump.ti_saph.verdi.power = 8



wavelengths = np.linspace(770, 890, 25)
polarizations = np.linspace(0, 50, 11)

while True:
    np.random.shuffle(wavelengths)
    with open('calibration/eom_drift.txt', 'a') as f:
        for wavelength in wavelengths:
            try:
                pump.wavelength = wavelength
            except ValueError:
                print('Wavelength out of range!')
                continue

            time.sleep(0.5)

            wls = []
            for i in range(3):
                wls.append(pump.wavelength)
                time.sleep(0.5)
            wl = np.median(wls)

            pm.set_wavelength(wl)

            np.random.shuffle(polarizations)
            for polarization in polarizations:
                print(f'{polarization:.1f} degrees')

                print(f'change {wl:.5f} {polarization:.3f}', file=f, flush=True)

                start_time = time.monotonic()
                pump.polarization = polarization

                for i in range(60):
                    try:
                        t = time.monotonic() - start_time
                        pol, power = pump.polarization, pump.power
                        pm_power = pm.power() * 1e3
                        print(f'{t:.8f} {pol.n:.8f} {pol.s:.8f} {power.n:.8f} {power.s:.8f} {pm_power:.8f}', file=f, flush=True)
                        print(f'{t:.3f} | {display(pol)} | {display(power)} mW | {pm_power:.3f} mW')
                    except Exception as e:
                        print('Sample failed:', e)
                    time.sleep(2)
