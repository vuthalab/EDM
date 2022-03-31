from pathlib import Path
import time
import json

import numpy as np 

from headers.edm_util import deconstruct

from api.fluorescence import FluorescenceSystem

##### ASSUMES WAVELENGTH IS ALREADY INITIALIZED #####


def random_frequency():
    return np.random.uniform(0.3e6, 10e6)

# Initialize fluorescence hardware
system = FluorescenceSystem(
    ximea_exposure = 20,
    samples_per_point = 2,
    pump_source = 'tisaph-high',
    use_qe_pro = False,
)
#system.pump.ti_saph.verdi.close_shutter()
system.pump.ti_saph.verdi.power = 8

# Initialize EOM
system.pump.eom.duty_cycle = 20
system.pump.eom.start_pulse()


start_time = time.monotonic()
try:
    with open('optical-pumping.txt', 'a') as f:
        while True:
            freq = random_frequency()
            print(f'{freq/1e6:.6f} MHz')
            system.pump.eom.frequency = freq
            data = system.take_data(wavelength = None)

            payload = {
                key: deconstruct(data['processed'][key])
                for key in [
                    'power', 'wavelength', 'linewidth',
                    'crystal-temperature', 'foreground-rate', 'background-rate'
                ]
            }
            payload['timestamp'] = time.time()
            payload['chop-frequency'] = freq

            print(payload)
            print(json.dumps(payload), file=f, flush=True)

            ### SHUT DOWN AFTER 9 HOURS ###
            if (time.monotonic() - start_time) / 3600 > 4.5:
                print('Shutting down.')
                pump.source = None
                system.off()
                break


except Exception as e:
    print(repr(e))
    system.off()
