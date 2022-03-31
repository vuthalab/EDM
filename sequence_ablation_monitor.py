"""
Ablates the crystal, occasionally interrupting ablation to take a fluorescence spectrum.
"""
import time
import json
import itertools

import numpy as np

from colorama import Fore, Style

from headers.edm_util import deconstruct
from headers.mfc import MFC
from headers.CTC100 import CTC100

from api.ablation import AblationSystem
from api.fluorescence import FluorescenceSystem


ABLATION_LENGTH = 45 # Minutes
SCAN_LENGTH = 30 # Minutes



# Initialize fluorescence system.
fluorescence = FluorescenceSystem(
    ximea_exposure=20,
    samples_per_point=2,
    use_qe_pro=False
)

# Initialize ablation system
ablation = AblationSystem(start_position=1)
print(f'{Fore.RED}Make sure you have annealed the crystal first!{Style.RESET_ALL}')
input(f'{Fore.RED}Press Enter to start ablation, or press Ctrl + C to cancel.{Style.RESET_ALL}')


T1 = CTC100(31415)
T2 = CTC100(31416)
mfc = MFC(31417)


T2.ramp_temperature('srb45k out', 5, 0.5) # Keep nozzle at consistent temperature
T2.ramp_temperature('heat cell', 15, 0.5) # Keep nozzle at consistent temperature
T2.enable_output()

try:
    with open('ablation-monitor-log.txt', 'a') as f:
        for i in itertools.count():
            if i > 0:
                # Ablation phase
                T1.ramp_temperature('heat saph', 6.5, 0.5)
                mfc.flow_rate_cell = 15
                fluorescence.pump.source = None
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

                    if ts/60 > ABLATION_LENGTH: ablation.off()

                ABLATION_LENGTH += 15


            # Fluorescence scan phase
            mfc.off()
            start_time = time.monotonic()
            while True:
                ts = time.monotonic() - start_time
                wl = np.random.uniform(802, 825)

                data = fluorescence.take_data(wavelength=wl, temperature=6.2)
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
                if ts/60 > SCAN_LENGTH: break
finally:
    ablation.off()
    mfc.off()
    fluorescence.off()
