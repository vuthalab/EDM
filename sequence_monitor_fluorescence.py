"""
Continuously monitor fluorescence at a specfic pump wavelength.
"""
import time 

import numpy as np 

from headers.ximea_camera import Ximea
from headers.CTC100 import CTC100

from api.pump_laser import PumpLaser

from headers.util import unweighted_mean


configuration = {
    'exposure': 10, # s

    'wavelength': 840,

    'roi': {
        'center_x': 465*2,
        'center_y': 346*2,
        'radius': 110*2,

#        'x_min': 481*2,
#        'x_max': 651*2,
#        'y_min': 338*2,
#        'y_max': 420*2,
    },
}


cam = Ximea(exposure = configuration['exposure'])
pump = PumpLaser()
T1 = CTC100(31415)
T1.ramp_temperature('heat coll', 10, 0.5)

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

pump.ti_saph.verdi.power = 8
pump.wavelength = configuration['wavelength']
pump.source = 'tisaph-low'

start_time = time.time()
with open('signal-log.txt', 'a') as f:
    while True:
        cam.async_capture(fresh_sample=True)
        wls = []
        temps = []
        powers = []
        while cam.image is None:
            print(f'Collecting samples... {len(wls)}', end='\r')
            try:
                wls.append(pump.wavelength)
                temps.append(T1.read('saph'))
                powers.append(pump.pm_power)
                time.sleep(0.25)
            except:
                time.sleep(2)

        wl = unweighted_mean(wls)
        temp = unweighted_mean(temps)
        power = unweighted_mean(powers)

        rate = get_intensity(cam.raw_rate_image)
        ts = time.time()

        net_rate = rate - background_rate

        print(f'[T + {ts-start_time:.3f}] Wavelength: {wl:.3f} nm | Temp: {temp:.3f} K | Power: {power:.3f} mW | Foreground: {rate*1e-3:.3f} kcount/s | Net: {net_rate*1e-3:.3f} kcount/s')
        print(
            ts,
            wl.n, wl.s,
            temp.n, temp.s,
            power.n, power.s,
            rate,
            background_rate.n, background_rate.s,
            file=f,
            flush=True
        )
