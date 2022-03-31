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
        'multiplexed': 8,
    }

    with create_server('wavemeter') as publisher:
        while True:
            frequencies = {}
            powers = {}
            voltages = {}
#            linewidths = {}

            freq_samples = {c: [] for c in channels.keys()}
            power_samples = {c: [] for c in channels.keys()}
            volt_samples = {c: [] for c in channels.keys()}
#            linewidth_samples = {c: [] for c in channels.keys()}
            temp_samples = []
            for i in range(8):
                temp_samples.append(wm.read_temperature())
                time.sleep(5e-3)

                for c, c_num in channels.items():
                    for method, dst in [
                        (wm.read_frequency, freq_samples),
                        (wm.read_laser_power, power_samples),
                        (wm.get_external_output, volt_samples),
#                        (wm.read_linewidth, linewidth_samples),
                    ]:
                        sample = method(c_num)
                        if isinstance(sample, float): dst[c].append(sample)
                        time.sleep(5e-3)

            for src, dst in [
                (freq_samples, frequencies),
                (power_samples, powers),
                (volt_samples, voltages),
#                (linewidth_samples, linewidths),
            ]:
                for key, vals in src.items():
                    if len(vals) > 1:
                        dst[key] = (np.mean(vals), np.std(vals, ddof=1))

            publisher.send({
                'freq': frequencies,
                'power': powers,
                'voltages': voltages,
#                'linewidth': linewidths,
                'temp': (np.mean(temp_samples), np.std(temp_samples, ddof=1))
            })
