import time

import numpy as np

from uncertainties import ufloat

from headers.edm_util import deconstruct
from headers.zmq_server_socket import create_server

from headers.usbtmc import USBTMCDevice


def labjack_thread():
    labjack = USBTMCDevice(31419, mode='multiplexed', name='Upper Labjack')

    with create_server('labjack') as publisher:
        while True:
            dac0 = ufloat(*map(float, labjack.query(f'READ_GENERIC DAC0 3').split()))

            publisher.send({
                'dac0': deconstruct(dac0)
            })

            time.sleep(0.8)
