from pathlib import Path
import itertools
import time
import sys

import numpy as np

from api.pump_laser import PumpLaser
from headers.elliptec_rotation_stage import ElliptecRotationStage
#from headers.rigol_ds1102e import RigolDS1102e
#from headers.digitizer import L4532A
from headers.siglent_sds1204 import SDS1204
from api.pump_laser import PumpLaser


save_folder = sys.argv[1]
assert len(save_folder) > 0
print(save_folder)

save_dir = Path(f'/home/vuthalab/Desktop/edm_data/optical-pumping/delta-decay-3/{save_folder}')
save_dir.mkdir()

pump = PumpLaser()
qwp = ElliptecRotationStage(port='/dev/ttyUSB7', offset=19412)

if True:
    # Set polarization to circular
    print('CIRCULAR')
    pump.polarization = 37.8329
    qwp.angle_unwrapped = -133.827
else:
    # Set polarization to linear
    print('LINEAR')
    pump.polarization = -44
    qwp.angle_unwrapped = 252


def mean(arr):
    return [np.mean(arr, axis=0), np.std(arr, axis=0)/np.sqrt(len(arr))]

#digitizer = L4532A()
#times = np.arange(16400)/20 # us

#with RigolDS1102e(address='/dev/fluorescence_scope') as scope:

with SDS1204() as scope:
    times = scope.times

    for i in itertools.count():
        if i % 50 == 0:
            pump.source = 'diode'
#            pump.source = 'tisaph-high'
#            pump.source = 'tisaph-low'
            time.sleep(5)
#            digitizer.init()

        if i % 50 == 25:
            pump.source = None
            time.sleep(5)
#            digitizer.init()

        traces = []
#    traces_2 = []
#        for j in range(1000):
        for j in range(20):
            scope.active_channel = 1
            try:
                trace = scope.trace
            except Exception as e:
                print('Exception', e)
                time.sleep(0.2)
                scope._conn.close()
                scope = SDS1204()
                time.sleep(0.2)
                continue
            print(i, j, len(trace), end='\r')
            traces.append(trace)
            time.sleep(0.3)
#        scope.active_channel = 2
#        traces_2.append(scope.trace)
#        time.sleep(0.5)
#            traces.append(digitizer.fetch())
        print()

        # Truncate 
        N = min([len(trace) for trace in traces])
        traces = np.array([trace[:N] for trace in traces])

        np.savez(
            str(save_dir / f'{i:04d}.npz'),
            time = times[:N],
#        trace_1 = mean(traces),
#        trace_2 = mean(traces_2),
            trace = mean(traces),
            source=str(pump.source)
        )
