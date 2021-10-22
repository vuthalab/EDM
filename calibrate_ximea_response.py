from pathlib import Path
import time

import numpy as np
import cv2

from headers.ti_saph import TiSapphire
from headers.ximea_camera import Ximea
from usb_power_meter.Power_meter_2 import PM16 
from headers.elliptec_rotation_stage  import ElliptecRotationStage

from headers.util import unweighted_mean

WAVELENGTHS = np.linspace(800, 830, 13)
np.random.shuffle(WAVELENGTHS)

folder = Path(f'/home/vuthalab/Desktop/edm_data/')


# Start scan
ti_saph = TiSapphire()
cam = Ximea()
pm = PM16('/dev/power_meter')
mount = ElliptecRotationStage()

ti_saph.verdi.power = 7


with open(folder / 'entries.txt', 'a') as f:
    for wavelength in WAVELENGTHS:
        ti_saph.wavelength = wavelength 
        mount.angle = 133
        time.sleep(3)

        print('Determining wavelength...')
        wavelength_samples = []
        for i in range(10):
            print(i, end='\r')
            wavelength_samples.append(ti_saph.wavelength)
            time.sleep(0.3)
        wavelength = unweighted_mean(wavelength_samples)
        print(wavelength)

        pm.set_wavelength(wavelength.n)

        print('Determining exposure time...')
        cam.exposure = 1e-3
        while True:
            cam.capture()
            print(cam.exposure, cam.saturation, end='\r')
            if cam.saturation > 80:
                cam.exposure /= 2
            elif cam.saturation < 5 and cam.exposure < 200:
                cam.exposure *= 2
            else:
                break
        print(f'Exposure set to {cam.exposure} s.')

        intensity_samples = []
        dark_intensity_samples = []
        power_samples = []

        print('Collecting samples...')
        for i in range(10):
            mount.angle = 50
            for i in range(20):
                print(i, end='\r')
                power = pm.power()
                power_samples.append(power)
                time.sleep(0.1)

            mount.angle = 133
            cam.exposure = cam.exposure # Reset capture
            for i in range(5):
                print(i, end='\r')
                cam.capture()
#                intensity_samples.append(cam.rate_image.sum())
                intensity_samples.append(cam.raw_rate)
                time.sleep(0.1)

            # Optional
            print('Collecting dark samples...')
            ti_saph.verdi.shutter_open = False
            time.sleep(0.5)
            cam.exposure = cam.exposure # Reset capture
            for i in range(2):
                print(i, end='\r')
                cam.capture()
                dark_intensity_samples.append(cam.raw_rate)
                time.sleep(0.1)
            ti_saph.verdi.shutter_open = True

            print(unweighted_mean(intensity_samples), unweighted_mean(power_samples), unweighted_mean(dark_intensity_samples))

        intensity = unweighted_mean(intensity_samples) - unweighted_mean(dark_intensity_samples)
        power = unweighted_mean(power_samples)
        print(wavelength.n, wavelength.s, intensity.n, intensity.s, power.n, power.s, file=f, flush=True)
