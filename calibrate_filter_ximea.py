from pathlib import Path
import time

import numpy as np
from PIL import Image

from headers.ti_saph import TiSapphire
from headers.ximea_camera import Ximea
from headers.rigol_ds1102e import RigolDS1102e
from headers.elliptec_rotation_stage  import ElliptecRotationStage

from headers.util import unweighted_mean

NAME = 'NE30AB-FELH0900.txt'

WAVELENGTHS = np.linspace(760, 900, 29)
ANGLES = np.linspace(0, 35, 8)

# Initial settings
EXPOSURE = 1e-4
VERDI_POWER = 5
SAMPLES_PER_WAVELENGTH = 100


folder = Path(f'/home/vuthalab/Desktop/edm_data/fluorescence/filters_ximea')
folder.mkdir(parents=True, exist_ok=True)
(folder / 'images').mkdir(parents=True, exist_ok=True)


# Start scan
ti_saph = TiSapphire()
cam = Ximea(exposure=EXPOSURE)
scope = RigolDS1102e('/dev/fluorescence_scope')
mount = ElliptecRotationStage()

scope.active_channel = 1
ti_saph.verdi.power = 5


def intensity(image):
    clipped = image[400:800, 1000:1400]
    peak = np.percentile(clipped, 95)
    return clipped, peak, np.mean(clipped)


with open(folder / f'{NAME}.txt', 'w') as f:
    while True:
        np.random.shuffle(ANGLES)
        for angle in ANGLES:
            print(angle)
            mount.angle = angle

#            np.random.shuffle(WAVELENGTHS)
            for wavelength in WAVELENGTHS:
                ti_saph.wavelength = wavelength 

                time.sleep(0.5)

                wavelength_samples = []
                voltage_samples = []
                intensity_samples = []

                # Auto-set exposure
                while True:
                    print(f'Setting exposure... {cam.exposure} s, {VERDI_POWER} W', end='\r', flush=True)
                    cam.capture()
                    clipped, peak, mean = intensity(cam.image)

                    if peak > 3200:
                        if cam.exposure < 1e-4 and VERDI_POWER > 5:
                            VERDI_POWER -= 0.5
                            ti_saph.verdi.power = VERDI_POWER
                            time.sleep(3)
                        else:
                            cam.exposure /= 1.5
                    elif peak < 1200:
                        if cam.exposure > 1 and VERDI_POWER < 7:
                            VERDI_POWER += 0.5
                            ti_saph.verdi.power = VERDI_POWER
                            time.sleep(3)
                        else:
                            cam.exposure *= 1.5
                    else:
                        break
                print(f'Final: {cam.exposure} s, {VERDI_POWER} W')

                n_samples = min(SAMPLES_PER_WAVELENGTH, int(100/cam.exposure) +1)
                for i in range(n_samples):
                    try:
                        cam.capture()
                        clipped, peak, mean = intensity(cam.image)

                        print(f'Sample {i}/{n_samples}, {peak}, {mean}', end='\r', flush=True)

                        wavelength_samples.append(ti_saph.wavelength)
                        voltage_samples.append(np.mean(scope.trace))
                        intensity_samples.append(mean)
                    except:
                        continue
                print()

                timestamp = time.strftime('%Y-%m-%d-%H-%M-%S')

                wavelength = unweighted_mean(wavelength_samples)
                voltage = unweighted_mean(voltage_samples)
                intensity = unweighted_mean(intensity_samples)
                print(f'{cam.exposure=} {wavelength=} {voltage=} {intensity=}')
                print(f'{timestamp} {cam.exposure} {angle} {wavelength.n} {wavelength.s} {voltage.n} {voltage.s} {intensity.n} {intensity.s}', file=f, flush=True)

                img = Image.fromarray(np.minimum(clipped/16, 255).astype(np.uint8))
                img.save(folder / 'images' / f'{timestamp}.png')
