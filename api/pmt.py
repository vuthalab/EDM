import time

import numpy as np

from uncertainties import ufloat

from headers.zmq_client_socket import connect_to
from headers.usbtmc import USBTMCDevice

class PMT:
    def __init__(self):
        super().__init__()

        self.resistor = 10e3 # Ohms. Change this if resistor changes.

        # Labjack gain controller
        self._monitor = connect_to('scope')
#        self._gain_controller = USBTMCDevice(31419, mode='multiplexed', name='PMT Gain Control')

    def _update_cache(self):
        while True:
            _, data = self._monitor.grab_json_data()
            if data is None:
                if self._cache is not None:
                    break
                else:
                    time.sleep(0.5)
            if data is not None and 'ch1' in data:
                self._cache = data

    def off(self):
        self.gain = 0

    @property
    def current(self):
        """Return output current in uA."""
        self._update_cache()
        return -1e6 * ufloat(*self._cache['ch1']) / self.resistor

    @property
    def trace(self):
        """
        Return current (uA) versus time.
        Format: (time, current)
        """
        self._update_cache()
        return (
            np.array(self._cache['times']),
            -1e6*np.array(self._cache['ch1-raw'])/self.resistor
        )


    @property
    def gain(self):
        try:
            n, s = map(float, self._gain_controller.query(f'READ_GENERIC DAC0 3').split())
            self._gain = ufloat(n, s)
        except:
            pass
        return self._gain

    @gain.setter
    def gain(self, gain: float):
        assert 0 <= gain <= 1.1
#        self._gain_controller.send_command(f'DAC0 {gain:.4f}')
        self._gain = ufloat(gain, 1e-3)
