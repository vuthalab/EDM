import time

import numpy as np
import matplotlib.pyplot as plt

from api.pump_laser import PumpLaser
from api.power_stabilizer import PowerStabilizer

from headers.rigol_ds1102e import RigolDS1102e

from headers.util import unweighted_mean, plot


pump = PumpLaser()

pump.ti_saph.verdi.power = 8
pump.eom.frequency = 10e6
pump.eom.start_pulse()
#pump.source = 'tisaph-low'
pump.source = 'tisaph-high'

#stabilizer = PowerStabilizer(pump, setpoint=0.9)
stabilizer = PowerStabilizer(pump, setpoint=20)

scope = RigolDS1102e('/dev/fluorescence_scope')



# Take data
#wavelengths = np.linspace(805, 880, 31)
wavelengths = np.linspace(810, 810, 1)
#polarizations = np.linspace(-90, 90, 37)
polarizations = np.linspace(-180, 180, 181)

with open('calibration/waveplate.txt', 'w') as f:
    np.random.shuffle(wavelengths)
    for wavelength in wavelengths:
        pump.wavelength = wavelength

        # Stabilize power
        print('Stabilizing power...')
        powers = []
        for i in range(30):
            power, error, gain = stabilizer.update()
            powers.append(power)

            if len(powers) > 20:
                stability = np.std(powers[20:]) / np.mean(powers[20:])
            else:
                stability = 0

            print(f'{power:.4f} mW | Gain: {gain:.3f} V | Stability: {stability * 100} %', end='\r')
            time.sleep(0.5)
        print()

        # Take data
        print('Taking data...')
        np.random.shuffle(polarizations)
        for ii, angle in enumerate(polarizations):
#            pump.polarization = angle
            try:
                pump.qwp.angle_unwrapped = angle
            except:
                time.sleep(0.2)
                continue

            power, error, gain = stabilizer.update()
            time.sleep(0.5)

            powers = []
            angles = []
            x_readings = []
            y_readings = []
            wavelengths = []
            for i in range(3):
                try:
                    power, error, gain = stabilizer.update()
                    powers.append(power)
                    angles.append(pump.polarization)
                    wavelengths.append(pump.wavelength)

                    scope.active_channel = 1
                    x_readings.append(np.mean(scope.trace))
                    scope.active_channel = 2
                    y_readings.append(np.mean(scope.trace))
                except:
                    pass

                time.sleep(0.5)

            wl = unweighted_mean(wavelengths)
            power = unweighted_mean(powers)
            angle = unweighted_mean(angles)
            x_reading = unweighted_mean(x_readings)
            y_reading = unweighted_mean(y_readings)
            print(f'{ii+1:2d} | {wl:.3f} nm | {power:.4f} mW | Polarization: {angle.n:6.1f} | X: {x_reading * 1e3:.3f} mV | Y: {y_reading:.3f} V')
            print(
                wl.n, wl.s,
                power.n, power.s,
                angle.n, angle.s,
                x_reading.n, x_reading.s,
                y_reading.n, y_reading.s,
                file=f, flush=True
            )
