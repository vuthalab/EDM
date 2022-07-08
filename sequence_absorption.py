"""Takes a fast emission spectrum with the Ximea."""

from pathlib import Path
import time 
import itertools

import numpy as np 
import matplotlib.pyplot as plt

from uncertainties import ufloat
from headers.util import unweighted_mean, nom

from api.pump_laser import PumpLaser
from headers.rigol_ds1102e import RigolDS1102e
from headers.usbtmc import USBTMCDevice
from headers.elliptec_rotation_stage import ElliptecRotationStage


save_name = Path(f'/home/vuthalab/Desktop/edm_data/fluorescence/transmission/4.8K-2.txt')
save_name.parent.mkdir(exist_ok=True)


# Connect to devices
pump = PumpLaser()
pump.source = 'diode'
diode_current_controller = USBTMCDevice(31419, mode='multiplexed', name='Diode Current Controller')

scope = RigolDS1102e(address='/dev/fluorescence_scope')
scope.active_channel = 2

# Set polarization to circular
qwp = ElliptecRotationStage(port='/dev/ttyUSB7', offset=19412)
pump.polarization = 37.8329
qwp.angle_unwrapped = -133.827

power_calibration_factor = 37.1/2.6# Manually determined
with open(save_name, 'a') as f:
    for i in itertools.count():
        try:
            print('Current set')
            current = np.random.uniform(3.7, 4)
            diode_current_controller.send_command(f'DAC1 {current:.5f}')

            stage_angle = np.sqrt(np.random.uniform(13**2, 17**2))
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
        transmission = []
        for i in range(10):
            power.append(pump.pm_power)
            transmission.append(np.mean(scope.trace))
            wavelength.append(pump.wavelength)
            print(f'{i}', end='\r')
            time.sleep(0.5)

        power = unweighted_mean(power) * power_calibration_factor
        wavelength = unweighted_mean(wavelength)
        transmission = unweighted_mean(transmission)

        # Save data
        print(wavelength, 'nm |', power, 'mW |', transmission * 1e3, 'mV')
        print(
            time.time(),
            wavelength.n, wavelength.s,
            power.n, power.s,
            transmission.n, transmission.s,
            current, stage_angle,
            file=f, flush=True
        )
