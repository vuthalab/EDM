from typing import Union, Literal, List, Tuple

from collections import defaultdict

import os
import time

import numpy as np
import matplotlib.pyplot as plt

try:
    from headers.usbtmc import USBTMCDevice
except:
    from usbtmc import USBTMCDevice


Array = List[float]

class SDS1204(USBTMCDevice):
    """USBMTC interface for Siglent SDS1204X-E oscilloscope."""

    # Currently active channel (emulated, not on scope)
    active_channel: int = 1

    # Cached properties
    _cache = {channel: defaultdict(lambda: None) for channel in [1, 2]}

    def __init__(self, address = '192.168.0.136'):
        """Initialize a connection to the scope and start acquisition."""
        super().__init__(address , mode='ethernet', tcp_port = 5025)
#        self._clear()
        self.send_command('CHDR OFF')

    @property
    def time_scale(self) -> float: return float(self.query('TDIV?'))

    @property
    def sample_rate(self) -> float: return float(self.query('SARA?'))

    @property
    def times(self) -> Array:
        """Return times along the horizontal axis."""
        scale, sample_rate = self.time_scale, self.sample_rate
        N = 7000
        return -7*scale + np.arange(N)/self.sample_rate


    @property
    def voltage_scale(self) -> float:
        cached = self._cache[self.active_channel]['voltage_scale']
        if cached is not None: return cached

        # Get value and cache
        value = float(self.query(f'C{self.active_channel}:VDIV?'))
        self._cache[self.active_channel]['voltage_scale'] = value
        return value


    @property
    def voltage_offset(self) -> float:
        cached = self._cache[self.active_channel]['voltage_offset']
        if cached is not None: return cached

        # Get value and cache
        value = float(self.query(f'C{self.active_channel}:OFST?'))
        self._cache[self.active_channel]['voltage_offset'] = value
        return value

    @property
    def trace(self) -> Array:
        """Return the array of voltage readings for the currently active trace."""
        scale, offset = self.voltage_scale, self.voltage_offset

        # Get raw trace bytes
        raw_data = self.query(f'C{self.active_channel}:WF? DAT2', raw=True, delay=0.5)
        assert raw_data.endswith(b'\n\n')

        length = int(raw_data[7:16].decode('ascii'))

        # Decode bytes (first 10 are garbage)
        decoded = np.frombuffer(raw_data, 'B')[16:].astype(int)
        decoded[decoded>127] -= 256
        return scale * decoded[:-2]/25 - offset


if __name__ == '__main__':
    scope = SDS1204()
    times = scope.times
    for i in range(2):
        trace = scope.trace
        print(len(trace))
        plt.plot(times[:len(trace)], trace)
    plt.show()
