import time
import itertools
import random
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

from headers.usbtmc import USBTMCDevice
from headers.qe_pro import QEProSpectrometer
from headers.elliptec_rotation_stage import ElliptecRotationStage
from api.pump_laser import PumpLaser

from headers.util import unweighted_mean

save_dir = Path('/home/vuthalab/Desktop/edm_data/fluorescence/2d/new-crystal-6.5K-short')
save_dir.mkdir(exist_ok=True)

regions_of_interest = np.array([
    787.8,
    815.5,
    828,
    859.5,
    869.1,
    903.5,
    922
])


spec = QEProSpectrometer()
#spec.exposure = 3e6 # microseconds
spec.exposure = 10e6 # microseconds
spec.temperature = -29 # C

pump = PumpLaser()
pump.eom.gain = 5
#diode_current_controller = USBTMCDevice(31419, mode='multiplexed', name='Diode Current Controller')

# Set polarization to circular
qwp = ElliptecRotationStage(port='/dev/ttyUSB7', offset=19412)
pump.polarization = 37.8329
qwp.angle_unwrapped = -133.827

with open('temp.txt', 'r') as f:
    start_idx = int(f.read())
print('Starting at index', start_idx)


def capture(N=3):
    # Capture sample
    print('Capturing...')
    powers = []
    spectra = []
    while True:
        start = time.monotonic()
        spec.async_capture()
        while spec.intensities is None:
            try:
                powers.append(pump.pm_power)
            except:
                time.sleep(2.0)
                continue

            time.sleep(1.0)
        end = time.monotonic()

        if end - start > 0.9 * spec.exposure / 1e6:
            spectra.append(spec.intensities)
            print('Saved spectrum.')
            if len(spectra) == N: break
        else:
            print('Skipping cached spectrum.')

    intensities = np.median(spectra, axis=0) # Filter out cosmic rays
    return spec.wavelengths, intensities * 1e3/spec.exposure, unweighted_mean(powers)



print('Capturing background.')
pump.source = None
time.sleep(3)
_, bg, bg_power = capture(9)


#pump.source = 'tisaph-low'
pump.source = 'tisaph-high'
time.sleep(3)

delta = 1 # Delta wavelength per step
power_calibration_factor = 95.0/5.72 # manually determined
try:
    for i in itertools.count(start_idx):
        if False:
            try:
                current = np.random.uniform(3, 4)
                diode_current_controller.send_command(f'DAC1 {current:.5f}')
                pump._diode_stage.angle_unwrapped = np.sqrt(
                    np.random.uniform(12.5**2, 20**2)
                )
                pump._update_optics()
            except ValueError:
                time.sleep(5)
                continue

        with open('temp.txt', 'w') as f:
            print(i+1, file=f)

        try:
            wl, fg, fg_power = capture()
            pump_wl = pump.wavelength

            # Save data
            power = (fg_power - bg_power) * power_calibration_factor
            print(power, 'mW')
            print(pump_wl, 'nm')
            np.savez(
                save_dir / f'{i:04d}.npz',
                timestamp = time.time(),
                pump_wavelength = pump_wl,
                angle = pump.polarization,
                power = [power.n, power.s],

                probe_wavelengths = wl,
                fg_rate = fg,
                bg_rate = bg,
            )
        except:
            print('Crashed!')
            time.sleep(10)


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
#        if pump.wavelength > 935: delta = -1
        if pump.wavelength > 890: delta = -1
        if pump.wavelength < 743: delta = 1
finally:
    pump.source = None
