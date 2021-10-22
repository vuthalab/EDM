from pathlib import Path
import time

import numpy as np
from PIL import Image

from headers.ti_saph import TiSapphire
from headers.ximea_camera import Ximea
from headers.rigol_ds1102e import RigolDS1102e
from headers.elliptec_rotation_stage  import ElliptecRotationStage

from headers.util import unweighted_mean

NAME = 'NE10AB-FELH0850+SEMROCK842'
#NAME = 'baseline-NE10AB'

#WAVELENGTHS = np.linspace(800, 900, 21)
WAVELENGTHS = np.linspace(800, 840, 9)
ANGLES = np.linspace(0, 35, 8)

ANGLES[3] = -15 # To fix weird reflection

ANGLES = np.array([0])#, 10, 20])


RESISTOR = 100 # ohm, on photodiode

# Initial settings
EXPOSURE = 1e-4
VERDI_POWER = 7
SAMPLES_PER_WAVELENGTH = 32


folder = Path(f'/home/vuthalab/Desktop/edm_data/fluorescence/filters_ximea')
folder.mkdir(parents=True, exist_ok=True)
(folder / 'images').mkdir(parents=True, exist_ok=True)


# Start scan
ti_saph = TiSapphire()
cam = Ximea(exposure=EXPOSURE)
scope = RigolDS1102e('/dev/fluorescence_scope')
mount = ElliptecRotationStage()

scope.active_channel = 1
ti_saph.verdi.power = VERDI_POWER


def process_image(image):
    background = np.percentile(image, 5)
    cropped = image[300:1000, 900:1500] - background
    peak = np.percentile(cropped, 95)
    return cropped, peak, np.mean(cropped)


with open(folder / 'raw_data' / f'{NAME}.txt', 'a') as f:
#    while True:
    for i in range(1):
        np.random.shuffle(ANGLES)
        for angle in ANGLES:
            print(angle)
            mount.angle = angle

#            np.random.shuffle(WAVELENGTHS)
            for wavelength in WAVELENGTHS:
                ti_saph.wavelength = wavelength 

                time.sleep(3)

                wavelength_samples = []
                voltage_samples = []
                intensity_samples = []

                try:
                    # Auto-set exposure
                    while True:
                        print(f'Setting exposure... {cam.exposure} s, {VERDI_POWER} W', end='\r', flush=True)
                        cam.exposure = cam.exposure # Reset existing capture
                        cam.capture()
                        cropped, peak, mean = process_image(cam.image)

                        print(f'Setting exposure... {cam.exposure} s, {VERDI_POWER} W, {peak}, {mean}', end='\r', flush=True)

                        if peak > 3200:
                            if cam.exposure < 1e-3 and VERDI_POWER > 5:
                                VERDI_POWER -= 0.5
                                ti_saph.verdi.power = VERDI_POWER
                                time.sleep(2)
                            else:
                                cam.exposure /= 2
                        elif peak < 64:
                            if cam.exposure > 1 and VERDI_POWER < 7:
                                VERDI_POWER += 0.5
                                ti_saph.verdi.power = VERDI_POWER
                                time.sleep(2)
                            else:
                                cam.exposure *= 2
                        else:
                            break
                    print(f'Final: {cam.exposure} s, {VERDI_POWER} W')
                except:
                    print('Failed to set exposure.')
                    continue

                n_samples = min(SAMPLES_PER_WAVELENGTH, int(30/cam.exposure) + 1)
                for i in range(n_samples):
                    try:
                        print(f'Sample {i}/{n_samples}, {peak}, {mean}', end='\r', flush=True)
                        wavelength_samples.append(ti_saph.wavelength)
                        voltage_samples.append(np.mean(scope.trace) * 1000/RESISTOR)
                        intensity_samples.append(mean)

                        if i < n_samples-1:
                            cam.capture()
                            cropped, peak, mean = process_image(cam.image)
                    except:
                        continue
                print()

                timestamp = time.strftime('%Y-%m-%d-%H-%M-%S')

                wavelength = unweighted_mean(wavelength_samples)
                voltage = unweighted_mean(voltage_samples)
                intensity = unweighted_mean(intensity_samples)
                print(f'{cam.exposure=} {wavelength=} {voltage=} {intensity=}')
                print(f'{timestamp} {n_samples} {cam.exposure} {angle} {wavelength.n} {wavelength.s} {voltage.n} {voltage.s} {intensity.n} {intensity.s}', file=f, flush=True)

                img = Image.fromarray(
                    np.maximum(np.minimum(256 * cropped/(1.2*peak), 255), 0
                ).astype(np.uint8))
                img.save(folder / 'images' / f'{timestamp}.png')
