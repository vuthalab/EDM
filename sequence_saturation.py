from pathlib import Path
import time 
import itertools
from datetime import datetime
import json
import os

import numpy as np 
import matplotlib.pyplot as plt

from uncertainties import ufloat
from headers.util import unweighted_mean, nom

from api.pump_laser import PumpLaser
from headers.usbtmc import USBTMCDevice
from headers.ximea_camera import Ximea
from headers.elliptec_rotation_stage import ElliptecRotationStage


# Settings
#polarizations = np.linspace(0, 360, 91)
polarizations = np.linspace(0, 180, 91)

with open('op-index.txt', 'r') as f:
    start_index = int(f.read())
print('Starting at index', start_index)

# Begin acquisition
diode_current_controller = USBTMCDevice(31419, mode='multiplexed', name='Diode Current Controller')
diode_current_controller.send_command('DAC1 4')

ximea = Ximea(exposure = 1)
pump = PumpLaser()
#pump.eom.gain = 5
#pump.eom.gain = 0

mount = ElliptecRotationStage(port='/dev/ttyUSB7', offset=-22000)


for index in itertools.count(start_index):
    print(index)
    with open('op-index.txt', 'w') as f: print(index+1, file=f)


    pump.source = None
    pump._diode_stage.angle = 16.3

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

    background_pm = []
    for i in range(5):
        print(i)
        background_pm.append(pump.pm_power)
        time.sleep(0.5)
    background_pm = unweighted_mean(background_pm)
    print('PM Background:', background_pm, 'mW')


    # FOREGROUND
    pump.source = 'diode'
    time.sleep(3)
    print(pump.wavelength)

    # Calibrate power meter
    print('Calibrating power meter...')
    hwp_angles = [*np.linspace(-10, 10, 15), *np.linspace(35, 55, 15)]
    hwp_powers = []
    for angle in hwp_angles:
        print(angle)
        mount.angle_unwrapped = angle
        hwp_powers.append(pump.pm_power)
        time.sleep(0.5)
    min_angle = hwp_angles[np.argmin(hwp_powers)]
    target_angles = min_angle + 45 * (np.arcsin(np.linspace(-1, 1, 100)) / np.pi + 0.5)
    np.random.shuffle(target_angles)

    total_power = min(hwp_powers) + max(hwp_powers)

    save_name = f'/home/vuthalab/Desktop/edm_data/optical-pumping/860-op-quartz-ximea/saturation.txt'

    # Take foreground
    with open(save_name, 'a') as f:
        for i, angle in enumerate(target_angles):
            print('Index', i)
            mount.angle_unwrapped = angle

            for pol in [0, 150]:
                pump.polarization = pol
                time.sleep(1)

                power = []
                wavelength = []

                images = []
                rates = []
                print('Ximea foreground.')
                for i in range(3):
                    ximea.async_capture(fresh_sample=True)
                    while True:
                        try:
                            power.append(pump.pm_power)
                            wavelength.append(pump.wavelength)
                        except:
                            time.sleep(0.3)
                        if ximea.image is not None: break
                        time.sleep(0.26)
                    print(ximea.raw_rate)
                    rates.append(ximea.raw_rate)
                    images.append(ximea.image)
                if len(power) == 0: raise ValueError

                power = total_power - unweighted_mean(power) - background_pm
                wavelength = unweighted_mean(wavelength)
                rate = ufloat(np.median(rates), np.std(rates)) - background
                image = np.median(images, axis=0)

                print(pol, '|', power, 'mW |', rate * 1e-6, 'Mcounts/s')
                print(time.time(), wavelength.n, pol, power.n, power.s, rate.n, rate.s, file=f, flush=True)

    pump.source = None
