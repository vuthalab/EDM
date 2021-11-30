import time

import numpy as np

from uncertainties import ufloat

from headers.edm_util import deconstruct
from headers.zmq_server_socket import create_server

from headers.rigol_ds1102e import RigolDS1102e



def scope_thread():
    scope = RigolDS1102e('/dev/fluorescence_scope')

    with create_server('scope') as publisher:
        while True:
            times = scope.times

            scope.active_channel = 1
            ch1 = scope.trace

            scope.active_channel = 2
            ch2 = scope.trace

            ch1_mean = ufloat(np.mean(ch1), np.std(ch1))
            ch2_mean = ufloat(np.mean(ch2), np.std(ch2))

            publisher.send({
                'times': list(times),
                'ch1-raw': list(ch1),
                'ch2-raw': list(ch2),
                'ch1': deconstruct(ch1_mean),
                'ch2': deconstruct(ch2_mean),
            })

            time.sleep(0.2)
