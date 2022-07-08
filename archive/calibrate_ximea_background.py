import numpy as np

from headers.ximea_camera import Ximea

cam = Ximea()

exposures = np.logspace(-4, 2.8, 32)

with open('/home/vuthalab/Desktop/edm_data/ximea_bg.txt', 'a') as f:
    while True:
        exposure = np.random.choice(exposures)

        print(exposure, end=' ', flush=True)
        cam.exposure = exposure
        cam.capture()

        intensity = cam.intensity
        print(intensity)

        print(exposure, intensity.n, intensity.s, file=f, flush=True)

