from labjack import ljm

import numpy as np

from uncertainties import ufloat

class Labjack:
    def __init__(self, serial_number):
        self.handle = ljm.openS("T7", "Ethernet", serial_number)
        # For test: string "-2" opens fake device. "ANY" opens any T7.

    def read(self, channel):
        # Average out some noise automatically
        N_AVERAGE = 64
        samples = []
        for i in range(N_AVERAGE):
            samples.append(ljm.eReadName(self.handle, channel))
        return ufloat(np.mean(samples), np.std(samples))

    def write(self, channel, value):
        success = ljm.eWriteName(self.handle, channel, value)
        return success

    def close(self):
        ljm.close(self.handle)
