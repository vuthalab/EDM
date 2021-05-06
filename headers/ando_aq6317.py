from typing import Tuple

import numpy as np
import matplotlib.pyplot as plt

from headers.gpib_device import GPIBDevice

SWEEP_MODES = ['stop', 'single', 'repeat', 'auto', 'segment_measure']


class AndoAQ6317(GPIBDevice):
    """GPIB interface for the Ando AQ6317 optical spectrum analyzer."""

    _active_trace = None

    def __init__(self, serial_port: str, gpib_addr: int):
        super().__init__(serial_port, gpib_addr)

    def _read_array(self, command: str):
        """Read a float array from the GPIB device."""
        entries = self.query(command).split(',')
        n = int(entries[0])
        data = np.array([float(x.strip()) for x in entries[1:]])
        assert len(data) == n
        return data

    def __str__(self) -> str:
        return '\n'.join([
            f'OSA Model: {self.name}',
            f'Active Trace: {self.active_trace}',
            f'Sweep Mode: {self.sweep_mode}',
            f'Range: {self.lower_wavelength} nm - {self.upper_wavelength} nm'
        ])

    ##### Control Commands #####
    def trigger(self) -> None:
        """Trigger a single sweep."""
        print('Triggering sweep.')
        self.send_command('SGL')

    ##### Virtual Properties #####
    @property
    def active_trace(self) -> str:
        if self._active_trace is None:
            self._active_trace = 'ABC'[int(self.query('ACTV?'))]
        return self._active_trace

    @active_trace.setter
    def active_trace(self, trace: str) -> None:
        """Sets the currently active trace."""
        assert trace.upper() in ['A', 'B', 'C']
        trace_num = 'ABC'.index(trace.upper())
        self.send_command(f'ACTV{trace_num}')
        self._active_trace = trace.upper()

    @property
    def sweep_mode(self) -> str:
        return SWEEP_MODES[int(self.query('SWEEP?'))]

    @property
    def wavelengths(self):
        """Retrieves the wavelength data (nm) from the currently active trace."""
        print('Retrieving wavelengths (nm)...')
        return self._read_array(f'WDAT{self.active_trace}')

    @property
    def levels(self):
        """Retrieves the level data (dBm) from the currently active trace."""
        print('Retrieving levels (dBm)...')
        return self._read_array(f'LDAT{self.active_trace}')

    @property
    def lower_wavelength(self) -> float:
        print('lw')
        return float(self.query('STAWL?'))

    @property
    def upper_wavelength(self) -> float: return float(self.query('STPWL?'))

    @lower_wavelength.setter
    def lower_wavelength(self, wavelength: float) -> None:
        assert 100 <= wavelength <= 1750
        self.send_command(f'STAWL{wavelength:.2f}')

    @upper_wavelength.setter
    def upper_wavelength(self, wavelength: float) -> None:
        assert 600 <= wavelength <= 2350
        self.send_command(f'STPWL{wavelength:.2f}')

    @property
    def range(self) -> Tuple[float, float]:
        return self.lower_wavelength, self.upper_wavelength

    @range.setter
    def range(self, wavelength_bounds: Tuple[float, float]) -> None:
        self.lower_wavelength, self.upper_wavelength = wavelength_bounds


    ##### Convenience Functions #####
    def quick_plot(self):
        """Plots the currently active trace."""
        plt.plot(self.wavelengths, self.levels)
        plt.xlabel('Wavelength (nm)')
        plt.ylabel('Power (dBm)')
        plt.title(f'Trace {self.active_trace}')
        plt.show()


    @property
    def spectrum(self):
        """Retrieves the currently active trace from the OSA."""
        return self.wavelengths, self.levels
