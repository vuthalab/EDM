import time

import numpy as np

from headers.qe_pro import QEProSpectrometer
from headers.zmq_server_socket import create_server

from headers.edm_util import deconstruct
from headers.util import nom, std, unweighted_mean


def qe_pro_thread():
    spectrometer = QEProSpectrometer()

    with create_server('qe-pro') as publisher:
        while True:
            data = {
                'temperature': spectrometer.temperature,
            }
            publisher.send(data)

            time.sleep(0.2)
