from pathlib import Path
import time 

import numpy as np 
import matplotlib.pyplot as plt
from PIL import Image

from uncertainties import ufloat
from headers.util import unweighted_mean, nom, plot

from headers.zmq_client_socket import connect_to

# Devices
from headers.verdi import Verdi
from headers.ti_saph import TiSapphire
from headers.elliptec_rotation_stage  import ElliptecRotationStage
from headers.filter_wheel import FilterWheel

monitor = connect_to('edm-monitor')

ti_saph = TiSapphire()
mount = ElliptecRotationStage()

ti_saph.verdi.power = 8

#angles = np.linspace(-45, 45, 91)
angles = np.linspace(0, 50, 11)
for wavelength in [840, 860, 880, 900]:
    ti_saph.wavelength = wavelength
#    np.random.shuffle(angles)

    samples = []
    for angle in angles:
        mount.angle = angle

        start_time = time.monotonic()
        while True:
            _, data = monitor.grab_json_data()
            if data is None: continue
            if 'pump' not in data or 'power' not in data['pump']: continue

            power = data['pump']['power']
            if time.monotonic() - start_time > 2: break

        print(angle, power)
        samples.append((mount.angle, ufloat(*power)))

    exp_angles, powers = np.array(samples).T

    mask = nom(powers) > nom(powers).max()/2
    center = exp_angles[mask].mean()
    print(wavelength, center)
    plot(exp_angles, powers, clear=False)

plt.xlabel('Angle (deg)')
plt.ylabel('Power (mW)')
plt.show()
