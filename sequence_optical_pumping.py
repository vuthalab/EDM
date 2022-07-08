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


# Settings
polarizations = np.linspace(0, 360, 361)
#polarizations = np.linspace(0, 180, 181)

with open('op-index.txt', 'r') as f:
    start_index = int(f.read())
print('Starting at index', start_index)

# Begin acquisition
ximea = Ximea(exposure = 0.5)
pump = PumpLaser()
#pump.eom.gain = 5
#pump.eom.gain = 0

#pump._diode_stage.angle = 16.3
#pump._diode_stage.angle = 13

#diode_current_controller = USBTMCDevice(31419, mode='multiplexed', name='Diode Current Controller')
#diode_current_controller.send_command('DAC1 4')

mount = ElliptecRotationStage(port='/dev/ttyUSB7', offset=19412)
mount.angle = 0
pump.polarization = 0


for index in itertools.count(start_index):
    print(index)
    with open('op-index.txt', 'w') as f: print(index+1, file=f)

    pump.source = None
#    pump._diode_stage.angle = np.sqrt(
#        np.random.uniform(13**2, 19**2)
#    )
#    current = np.random.uniform(3, 3.5)
#    diode_current_controller.send_command(f'DAC1 {current:.5f}')

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

    # Take foreground
    np.random.shuffle(polarizations)

    save_name = f'/home/vuthalab/Desktop/edm_data/optical-pumping/poincare/data-860-2'#{index:04d}'
    Path(save_name).parent.mkdir(exist_ok=True)
#    Path(save_name).mkdir()
    with open(f'{save_name}.txt', 'a') as f:
#        pump.source = 'diode'
        pump.source = 'tisaph-high'
        time.sleep(3)
        print(pump.wavelength)


        if False:
            # Calibrate power meter
            print('Calibrating power meter...')
            hwp_angles = [*np.linspace(-10, 10, 15), *np.linspace(35, 55, 15)]
            hwp_powers = []
            for angle in hwp_angles:
                print(angle)
                mount.angle_unwrapped = angle
                hwp_powers.append(pump.pm_power)
                time.sleep(0.5)
            mount.angle_unwrapped = hwp_angles[np.argmin(hwp_powers)]
            power_calibration_factor = max(hwp_powers) / min(hwp_powers)
            print(hwp_powers)
            print(power_calibration_factor)
        else:
            power_calibration_factor = 26/1 # Manually determined

#        for i, pol in enumerate(polarizations):
#            print(f'{i}/{len(polarizations)}', pol)
        while True:
            hwp_angle = np.random.uniform(0, 360)
            qwp_angle = np.random.uniform(0, 360)

#            pump.polarization = pol
            pump.polarization = hwp_angle 
            mount.angle_unwrapped = qwp_angle
            print(hwp_angle, qwp_angle)
            time.sleep(0.2)

            power = []
            wavelength = []

            images = []
            rates = []
            print('Ximea foreground.')
            for i in range(5):
                power.append(pump.pm_power)
                wavelength.append(pump.wavelength)

                ximea.capture(fresh_sample=True)

                rates.append(ximea.raw_rate)
                images.append(ximea.image)
            if len(power) == 0: raise ValueError

            power = (unweighted_mean(power) - background_pm) * power_calibration_factor
            wavelength = unweighted_mean(wavelength)
            rate = ufloat(np.median(rates), np.std(rates)) - background
            image = np.median(images, axis=0)

#            print(pol, '|', power, 'mW |', rate * 1e-6, 'Mcounts/s')
            print(power, 'mW |', rate * 1e-6, 'Mcounts/s')
#            print(time.time(), wavelength.n, pol, power.n, power.s, rate.n, rate.s, file=f, flush=True)
            print(time.time(), wavelength.n, hwp_angle, qwp_angle, power.n, power.s, rate.n, rate.s, file=f, flush=True)

            if False:
                np.savez(
                    f'{save_name}/{round(pol):03d}.npz',
                    timestamp=time.time(),
                    image=image,
                    wavelength = wavelength.n,
                    polarization = pol,
                    power = [power.n, power.s],
                )

    pump.source = None
