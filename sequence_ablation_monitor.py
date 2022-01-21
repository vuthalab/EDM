import time
import json

import numpy as np

from colorama import Fore, Style

from headers.edm_util import deconstruct
from headers.mfc import MFC
from headers.CTC100 import CTC100

from api.ablation import AblationSystem
from api.fluorescence import FluorescenceSystem



# Initialize fluorescence system.
fluorescence = FluorescenceSystem(use_qe_pro=False)

# Initialize ablation system
ablation = AblationSystem(start_position=597)
input(f'{Fore.RED}Press Enter to start ablation, or press Ctrl + C to cancel.{Style.RESET_ALL}')


T1 = CTC100(31415)
mfc = MFC(31417)

try:
    with open('ablation-monitor-log.txt', 'a') as f:
        while True:
            # Ablation phase (10 minutes)
            T1.ramp_temperature('heat saph', 6.5, 0.5)
            mfc.flow_rate_cell = 30
            ablation.on()

            start_time = time.monotonic()
            for (n, pos, dip_size) in ablation.ablate_continuously():
                ts = time.monotonic() - start_time
                print(f'{ts:7.3f} s | {n:05d} | ({pos[0]:.3f}, {pos[1]:.3f}) pixels | {dip_size:5.2f} % dip')
                payload = {
                    'timestamp': time.time(),
                    'n': n,
                    'position': [pos[0].n, pos[1].n],
                    'dip': dip_size,
                }
                print('ablation', json.dumps(payload), file=f, flush=True)

                if ts/60 > 10: ablation.off()


            # Fluorescence scan phase (30 minutes)
            mfc.off()
            start_time = time.monotonic()
            while True:
                ts = time.monotonic() - start_time
                wl = np.random.uniform(802, 825)

                data = fluorescence.take_data(wavelength=wl)
                processed = data['processed']

                payload = {
                    key: deconstruct(processed[key])
                    for key in [
                        'power', 'wavelength', 'linewidth',
                        'crystal-temperature', 'foreground-rate', 'background-rate'
                    ]
                }
                payload['timestamp'] = time.time()
                print('fluorescence', json.dumps(payload), file=f, flush=True)
                if ts/60 > 40: break
finally:
    mfc.off()
    ablation.off()
    fluorescence.off()
