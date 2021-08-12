import time

import numpy as np

from headers.wa1000_wavemeter import WA1000Wavemeter
from headers.wavemeter import WM
from headers.zmq_server_socket import create_server

from headers.edm_util import deconstruct


def wa1000_wavemeter_thread():
    wavemeter = WA1000Wavemeter()

    with create_server('wa1000-wavemeter') as publisher:
        while True:
            time.sleep(0.5)
            wavemeter.poll()
            publisher.send({'wavelength': deconstruct(wavemeter.wavelength)})


def wavemeter_thread():
    wm = WM()

    channels = {
        'calcium': 6,
        'ti-saph': 7,
        'baf': 8,
    }

    with create_server('wavemeter') as publisher:
        while True:
            frequencies = {}
            powers = {}

            freq_samples = {c: [] for c in channels.keys()}
            power_samples = {c: [] for c in channels.keys()}
            temp_samples = []
            for i in range(8):
                temp_samples.append(wm.read_temperature())
                time.sleep(5e-3)

                for c, c_num in channels.items():

                    sample = wm.read_frequency(c_num)
                    if isinstance(sample, float): freq_samples[c].append(sample)
                    time.sleep(5e-3)

                    sample = wm.read_laser_power(c_num)
                    if isinstance(sample, float): power_samples[c].append(sample)
                    time.sleep(5e-3)

            for key, vals in freq_samples.items():
                if len(vals) > 1:
                    frequencies[key] = (np.mean(vals), np.std(vals, ddof=1))

            for key, vals in power_samples.items():
                if len(vals) > 1:
                    powers[key] = (np.mean(vals), np.std(vals, ddof=1))

            publisher.send({
                'freq': frequencies,
                'power': powers,
                'temp': (np.mean(temp_samples), np.std(temp_samples, ddof=1))
            })
