"""
Continuously monitor fluorescence at a specfic pump wavelength.
"""
import time 

import numpy as np 

from headers.ximea_camera import Ximea
from headers.elliptec_rotation_stage import ElliptecRotationStage
from headers.util import nom, unweighted_mean

from api.pump_laser import PumpLaser
from api.power_stabilizer import PowerStabilizer



configuration = {
    'exposure': 10, # s
    'wavelength': 815,
    'roi': {
        'center_x': 520*2,
        'center_y': 330*2,
        'radius': 70*2,
    },
}


mount = ElliptecRotationStage(port='/dev/rotation_mount', offset=22434)
#mount_2 = ElliptecRotationStage(port='/dev/rotation_mount_2', offset=12017)
mount_3 = ElliptecRotationStage(port='/dev/rotation_mount_3', offset=-9538)

cam = Ximea(exposure = configuration['exposure'])
pump = PumpLaser()
power_stabilizer = PowerStabilizer(pump)


mount.angle = 22.5
mount_3.angle = 20


def get_intensity(rate_image):
    """Returns the intensity (counts/s) summed over the ROI given a rate image."""
    roi = configuration['roi']

    if 'radius' in roi:
        # Circular ROI
        h, w = rate_image.shape
        x, y = np.meshgrid(np.arange(w), np.arange(h))
        mask = (x - roi['center_x'])**2 + (y - roi['center_y'])**2 < roi['radius']**2
        return rate_image[mask].sum()
    else:
        # Rectangular ROI
        return rate_image[roi['y_min']:roi['y_max'], roi['x_min']:roi['x_max']].sum()

pump.source = None
bg_rates = []
for i in range(3):
    print(f'Capturing background sample {i+1}...', end='\r')
    cam.capture(fresh_sample=True)
    bg_rates.append(get_intensity(cam.raw_rate_image))
print()
background_rate = unweighted_mean(bg_rates)
print(f'Background Rate: {background_rate*1e-3:.3f} kcount/s')


pump.ti_saph.verdi.power = 10
pump.polarization = 0
pump.wavelength = configuration['wavelength']
pump.source = 'tisaph-high'

start_time = time.time()
with open('signal-log.txt', 'a') as f:
    while True:
        cam.async_capture(fresh_sample=True)
        wls = []
        powers = []
        while cam.image is None:
            try:
                wls.append(pump.wavelength)
                power, error, gain = power_stabilizer.update()
                powers.append(power)

                print(f'Collecting samples... {len(wls)} | {power:.3f} mW | {gain:.3f} V', end='\r')
                time.sleep(0.5)
            except Exception as e:
                print(e)
                time.sleep(2)

        wl = unweighted_mean(wls)
        power = unweighted_mean(powers)

        rate = get_intensity(cam.raw_rate_image)
        ts = time.time()

        net_rate = rate - background_rate

        print(f'[T + {ts-start_time:.3f}] Wavelength: {wl:.3f} nm | Power: {power:.3f} mW | Foreground: {rate*1e-3:.3f} kcount/s | Net: {net_rate*1e-3:.3f} kcount/s')
        print(
            ts,
            wl.n, wl.s,
            power.n, power.s,
            rate,
            background_rate.n, background_rate.s,
            file=f,
            flush=True
        )
