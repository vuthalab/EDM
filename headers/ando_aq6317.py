from typing import Tuple, List

import numpy as np
import matplotlib.pyplot as plt

from headers.gpib_device import GPIBDevice


Array = List[float]


SWEEP_MODES = ['stop', 'single', 'repeat', 'auto', 'segment_measure']
SPEED_OF_LIGHT = 299792.458 # in nm Thz


class AndoAQ6317(GPIBDevice):
    """GPIB interface for the Ando AQ6317 optical spectrum analyzer."""


    def _read_array(self, command: str) -> Array:
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
            f'Range: {self.lower_wavelength:.2f}-{self.upper_wavelength:.2f} nm',
            f'Resolution: {self.resolution:.2f} nm',
            f'Scale: {self.scale}',
        ])

    ##### Control Commands #####
    def trigger(self) -> None:
        """Trigger a single sweep."""
        print('Triggering sweep.')
        self.send_command('SGL')


    def center(self) -> None:
        """Center the OSA range around the signal peak."""
        self.send_command('CTR=P')

    def stop(self) -> None:
        self.sweep_mode = 'stop'
        super().stop()


    ##### Virtual Properties #####
    @property
    def active_trace(self) -> str:
        return 'ABC'[int(self.query('ACTV?'))]

    @active_trace.setter
    def active_trace(self, trace: str) -> None:
        """Sets the currently active trace."""
        assert trace.upper() in ['A', 'B', 'C']
        trace_num = 'ABC'.index(trace.upper())
        self.send_command(f'ACTV{trace_num}')


    @property
    def sweep_mode(self) -> str:
        return SWEEP_MODES[int(self.query('SWEEP?'))]

    @sweep_mode.setter
    def sweep_mode(self, mode: str) -> None:
        assert mode.lower() in SWEEP_MODES
        command = {
            'stop': 'STP',
            'single': 'SGL',
            'repeat': 'RPT',
            'auto': 'AUTO',
        }[mode.lower()]
        self.send_command(command)


    @property
    def wavelengths(self) -> Array:
        """Retrieves the wavelength data (nm) from the currently active trace."""
        print('Retrieving wavelengths (nm)...')
        return self._read_array(f'WDAT{self.active_trace}')


    @property
    def levels(self) -> Array:
        """Retrieves the level data from the currently active trace."""
        print('Retrieving levels...')
        return self._read_array(f'LDAT{self.active_trace}')


    @property
    def lower_frequency(self) -> float: return float(self.query('STAF?'))

    @property
    def upper_frequency(self) -> float: return float(self.query('STPF?'))

    @lower_frequency.setter
    def lower_frequency(self, frequency: float) -> None:
        assert 1 <= frequency <= 499.5
        self.send_command(f'STAF{frequency:07.3f}')

    @upper_frequency.setter
    def upper_frequency(self, frequency: float) -> None:
        assert 171.5 <= frequency <= 674.5
        self.send_command(f'STPF{frequency:07.3f}')


    @property
    def lower_wavelength(self) -> float: return SPEED_OF_LIGHT/self.upper_frequency

    @property
    def upper_wavelength(self) -> float: return SPEED_OF_LIGHT/self.lower_frequency

    @lower_wavelength.setter
    def lower_wavelength(self, wavelength: float) -> None:
        self.upper_frequency = SPEED_OF_LIGHT/wavelength

    @upper_wavelength.setter
    def upper_wavelength(self, wavelength: float) -> None:
        self.lower_frequency = SPEED_OF_LIGHT/wavelength


    @property
    def range(self) -> Tuple[float, float]:
        """Return the currently specified horizontal range (nm)."""
        return self.lower_wavelength, self.upper_wavelength

    @range.setter
    def range(self, wavelength_bounds: Tuple[float, float]) -> None:
        self.upper_wavelength = wavelength_bounds[1]
        self.lower_wavelength = wavelength_bounds[0]


    @property
    def scale(self) -> str:
        """Return the currently configured scale type (log/linear)."""
        return ['log', 'linear'][int(self.query('PMUNT?'))]

    @scale.setter
    def scale(self, scale: str) -> None:
        assert scale.lower() in ['log', 'linear']
        unit_num = ['log', 'linear'].index(scale.lower())
        self.send_command(f'PMUNT{unit_num}')


    @property
    def unit(self) -> str:
        """Get the current unit for the vertical axis, according to the scale type."""
        return {'log': 'dBm', 'linear': 'W'}[self.scale]


    @property
    def resolution(self) -> float:
        """Return the current horizontal resolution (nm)."""
        return float(self.query('RESLN?'))

    @resolution.setter
    def resolution(self, resolution: float) -> None:
        """Set the horizontal resolution (nm). Only certain values are allowed."""
        ghz = round(resolution * 200)
        valid_ghz = [2, 4, 10, 20, 40, 100, 200, 400]
        if ghz not in valid_ghz:
            raise ValueError(
                'Valid resolutions are (nm): ' + ', '.join(
                    f'{f/200:.2f}' for f in valid_ghz
                )
            )
        self.send_command(f'RESLNF{ghz:03d}')


    ##### Convenience Functions #####
    def quick_plot(self):
        """Shows a plot of the currently active trace."""
        plt.plot(self.wavelengths, self.levels)
        plt.xlabel('Wavelength (nm)')
        plt.ylabel(f'Power ({self.unit})')
        plt.title(f'Trace {self.active_trace}')
        plt.show()


    @property
    def spectrum(self) -> Tuple[Array, Array]:
        """Retrieves data for the currently active trace from the OSA."""
        return self.wavelengths, self.levels
