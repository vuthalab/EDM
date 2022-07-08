"""Takes a fast emission spectrum with the Ximea."""

from pathlib import Path
import time 
import itertools
import os
import sys

import numpy as np 
import matplotlib.pyplot as plt

from uncertainties import ufloat
from headers.util import unweighted_mean, nom

from api.pump_laser import PumpLaser
from headers.CTC100 import CTC100
from headers.rigol_ds1102e import RigolDS1102e
from headers.usbtmc import USBTMCDevice
from headers.ximea_camera import Ximea
from headers.elliptec_rotation_stage import ElliptecRotationStage


temperature = float(sys.argv[1])

save_name = Path(f'/home/vuthalab/Desktop/edm_data/fluorescence/fine-excitation/869-{temperature:.2f}K.txt')
save_name.parent.mkdir(exist_ok=True)


# Set temperature
T1 = CTC100(31415)
T1.ramp_temperature('heat saph', temperature, 0.1)
T1.enable_output()

# Connect to devices
ximea = Ximea(exposure = 1.5)
pump = PumpLaser()
diode_current_controller = USBTMCDevice(31419, mode='multiplexed', name='Diode Current Controller')
scope = RigolDS1102e(address='/dev/fluorescence_scope')
scope.active_channel = 2

# Set polarization to circular
qwp = ElliptecRotationStage(port='/dev/ttyUSB7', offset=19412)
pump.polarization = 37.8329
qwp.angle_unwrapped = -133.827


# Take background
pump.source = None
time.sleep(3)

background = []
print('Calibrating Ximea background.')
for i in range(9):
    print(i)
    ximea.capture(fresh_sample=True)
    background.append(ximea.raw_rate)
background = unweighted_mean(background)
print('Ximea Background:', 1e-6*background, 'Mcounts/s')


pump.source = 'diode'
time.sleep(3)

power_calibration_factor = 31.3/2.25# Manually determined
with open(save_name, 'a') as f:
    for i in range(2000):
        try:
            print('Current set')
            current = np.random.uniform(3.7, 4)
            diode_current_controller.send_command(f'DAC1 {current:.5f}')

#            if np.random.random() < 0.6:
#                stage_angle = np.sqrt(np.random.uniform(12**2, 20**2))
#            else:
#                stage_angle = np.sqrt(np.random.uniform(14**2, 17**2))
#            if np.random.random() < 0.5: stage_angle *= -1

            stage_angle = np.sqrt(np.random.uniform(3**2, 13**2))
            print('Wavelength set', stage_angle)
            pump._diode_stage.angle_unwrapped = stage_angle
            print('Optic update')
            pump._update_optics()
            print('Done')
        except ValueError as e:
            print('Error, retry.', e)
            time.sleep(2)
            continue

        # Take data
        power = []
        wavelength = []
        rates = []
        transmission = []
        print('Ximea foreground.')
        for i in range(3):
            ximea.capture(fresh_sample=True)
            power.append(pump.pm_power)
            rates.append(ximea.raw_rate)
            transmission.append(np.mean(scope.trace))
            wavelength.append(pump.wavelength)
            print(f'{i} | {ximea.saturation:6.2} %', end='\r')

        power = unweighted_mean(power) * power_calibration_factor
        wavelength = unweighted_mean(wavelength)
        rate = ufloat(np.median(rates), np.std(rates)) - background
        transmission = unweighted_mean(transmission)

        # Save data
        print(wavelength, 'nm |', power, 'mW |', rate * 1e-6, 'Mcounts/s |', transmission * 1e3, 'mV |', ximea.saturation)
        print(
            time.time(),
            wavelength.n, wavelength.s,
            power.n, power.s,
            rate.n, rate.s,
            transmission.n, transmission.s,
            current, stage_angle,
            file=f, flush=True
        )
