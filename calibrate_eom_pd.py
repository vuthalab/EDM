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
from headers.api import EOM, PumpLaser
from usb_power_meter.Power_meter_2 import PM16 


verdi = Verdi()
pump = PumpLaser()
eom = EOM()
pm = PM16('/dev/power_meter')

monitor = connect_to('scope')

gains = np.linspace(0, 5, 21)

def mean(arr): return ufloat(np.mean(arr), np.std(arr))

def get_samples(f, wl):
    np.random.shuffle(gains)
    for gain in gains:
        eom.gain = gain
        time.sleep(2)

        monitor.flush()

        samples = [], []
        power_samples = []
        for i in range(3):
            print(f'{gain:.3f} V gain | {i} samples', end='\r')
            
            try:
                _, data = monitor.grab_json_data()
                if data is not None:
                    samples[0].append(ufloat(*data['ch1']))
                    samples[1].append(ufloat(*data['ch2']))
                    power_samples.append(pm.power())
            except Exception as e:
                print('Sample error:', e)
                

            time.sleep(1)

        power = mean(power_samples) * 1e3
        a = unweighted_mean(samples[0])
        b = unweighted_mean(samples[1])
        print(gain, wl, power.n, power.s, a.n, a.s, b.n, b.s, file=f, flush=True)
        print(f'{gain:.3f} V gain | {wl:.3f} nm | {display(power)} mW | {display(a)} V vertical | {display(b)} V horizontal')

while True:
    # BaF laser
    print('BaF Laser')
    pump.source = 'baf'
    pm.set_wavelength(860)
    with open('calibration/baf_pd.txt', 'a') as f: get_samples(f, 860)

    # Nothing
    print('Background')
    pump.source = None
    time.sleep(2)
    with open('calibration/background_pd.txt', 'a') as f: get_samples(f, 0)


    # Ti:Saph
    print('Ti:sapphire Laser')
    pump.source = 'tisaph'

    wavelengths = np.linspace(750, 910, 33)
    powers = np.linspace(7, 9, 3)
    np.random.shuffle(wavelengths)
    with open('calibration/tisaph_pd.txt', 'a') as f:
        for wavelength in wavelengths:
            pump.wavelength = wavelength

            np.random.shuffle(powers)
            for pump_power in powers:
                print(f'{pump_power} W')
                try:
                    verdi.power = pump_power
                except:
                    print('Verdi connection dropped!')
                    verdi = Verdi()
                    verdi.power = pump_power

                time.sleep(2)

                wl = pump.wavelength
                pm.set_wavelength(wl)
                get_samples(f, wl)
