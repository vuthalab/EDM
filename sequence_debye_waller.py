import time

import numpy as np


from api.crystal import CrystalSystem
from api.fluorescence import FluorescenceSystem

temperatures = np.linspace(4.9, 10, 52) 

crystal = CrystalSystem()
optics = FluorescenceSystem(ximea_exposure=15, pump_source='tisaph-low')

optics.take_background(n_samples = 3)

with open('debye-waller.txt', 'a') as f:
    for temp in temperatures:
        crystal.temperature = temp
        data = optics.take_samples(n_samples = 3)

        rate = data['rate']
        power = data['power']

        print(
            time.time(),
            temp,
            rate.n, rate.s,
            power.n, power.s,
            file=f, flush=True
        )

crystal.temperature = 4
