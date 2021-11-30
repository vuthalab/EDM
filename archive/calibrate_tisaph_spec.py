import time

import numpy as np

from headers.ti_saph import TiSapphire
from headers.util import unweighted_mean

ti_saph = TiSapphire()

with open('calibration/ti_saph_spec.txt', 'a') as f:
    while True:
        wl = np.random.uniform(840, 910)
        ti_saph.wavelength = wl

        time.sleep(2)

        spec_wl = []
        wm_wl = []
        for i in range(5):
            spec_wl.append(ti_saph.spectrometer_wavelength)
            try:
                wm_wl.append(ti_saph.wavemeter_wavelength)
            except:
                print('Bad reading')
                time.sleep(0.5)
                continue
            time.sleep(1)

        spec_wl = unweighted_mean(spec_wl)
        wm_wl = unweighted_mean(wm_wl)
        print(spec_wl.n, spec_wl.s, wm_wl.n, wm_wl.s, file=f, flush=True)
