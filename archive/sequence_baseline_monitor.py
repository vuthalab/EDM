"""
Ablates the crystal, occasionally interrupting ablation to take a fluorescence spectrum.
"""
import time
import json
import itertools

import numpy as np

from colorama import Fore, Style

from headers.edm_util import deconstruct, countdown_for
from headers.mfc import MFC
from headers.CTC100 import CTC100

from api.ablation import AblationSystem
from api.fluorescence import FluorescenceSystem


GROWTH_LENGTH = 10 # Minutes


# Initialize fluorescence system.
fluorescence = FluorescenceSystem(
    ximea_exposure=10,
    samples_per_point=2,
    pump_source = 'tisaph-high',
    use_qe_pro=False
)


T1 = CTC100(31415)
#T2 = CTC100(31416)
mfc = MFC(31417)


T1.ramp_temperature('heat mirror', 10, 0.5)
T1.ramp_temperature('heat saph', 6.5, 0.5)
T1.enable_output()

#T2.ramp_temperature('srb45k out', 5, 0.5)
#T2.ramp_temperature('heat cell', 15, 0.5)
#T2.enable_output()

WAVELENGTHS = np.linspace(780, 880, 21)
POLARIZATIONS = np.linspace(0, 90, 7)

try:
    with open('calibration/baseline-fluorescence-log.txt', 'a') as f:
        for i in itertools.count():
            if i > 0:
                # Growth Phase
                T1.ramp_temperature('heat saph', 6.5, 0.5)
                mfc.flow_rate_neon_line = 14
                fluorescence.pump.source = None
                print('growth', file=f, flush=True)
                countdown_for(GROWTH_LENGTH * 60)


            # Fluorescence scan phase
            mfc.off()
            start_time = time.monotonic()
            np.random.shuffle(WAVELENGTHS)
            for wl in WAVELENGTHS:
                np.random.shuffle(POLARIZATIONS)
                for polarization in POLARIZATIONS:
                    data = fluorescence.take_data(wavelength=wl, polarization=polarization)
                    processed = data['processed']

                    payload = {
                        key: deconstruct(processed[key])
                        for key in [
                            'power', 'angle', 'wavelength', 'linewidth',
                            'crystal-temperature', 'foreground-rate', 'background-rate'
                        ]
                    }
                    payload['timestamp'] = time.time()
                    print('fluorescence', json.dumps(payload), file=f, flush=True)
finally:
    mfc.off()
    fluorescence.off()
