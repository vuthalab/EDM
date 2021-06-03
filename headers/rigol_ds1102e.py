from typing import Union, Literal, List, Tuple

import time
from collections import defaultdict

import numpy as np
import matplotlib.pyplot as plt

from headers.usbtmc import USBTMCDevice

Channel = Union[Literal[1], Literal[2]]
Array = List[float]


TRIGGER_MODES = ['edge', 'pulse', 'video', 'scope', 'pattern', 'duration', 'alternation']


class RigolDS1102e(USBTMCDevice):
    """USBMTC interface for DS1102e oscilloscope."""

    # Currently active channel (emulated, not on scope)
    active_channel: Channel = 1

    # Number of garbage points at start of trace
    _garbage_points: int = 10

    # Cached properties
    _cache = {channel: defaultdict(lambda: None) for channel in [1, 2]}


    def __init__(self):
        """Initialize a connection to the scope and start acquisition."""
        super().__init__('/dev/usbtmc1', mode='direct')
        self.send_command(':RUN')
        self.send_command(':KEY:LOCK DISABLE')


    def close(self) -> None:
        """Stop acquisition and close the connection."""
        self.send_command(':STOP')
        super().close()


    def __str__(self) -> str:
        trigger_mode = self.trigger_mode
        if trigger_mode == 'edge':
            trigger_mode = f'{self.trigger_direction} edge @ {self.trigger_level:.2f} V'
        trigger_mode = f'{trigger_mode} on {self.trigger_source}'
        return '\n'.join([
            f'Model: {self.name}',
            f'Active Channel: {self.active_channel}',
            f'Voltage Offset: {self.voltage_offset:.2g} V',
            f'Voltage Scale : {self.voltage_scale:.2g} V/div ({self.probe_attenuation}x probe attenuation)',
            f'Time Axis: {self.time_scale:.2g} s/div, {self.time_offset:.2g} s offset',
            f'Trigger: {trigger_mode}'
        ])


    ##### Virtual Properties #####
    @property
    def probe_attenuation(self) -> float:
        """Return the currently configured attenuation factor for the scope probe."""
        return float(self.query(f':CHAN{self.active_channel}:PROB?'))

    @probe_attenuation.setter
    def probe_attenuation(self, attenuation: float) -> None:
        self.send_command(f':CHAN{self.active_channel}:PROB {attenuation}')


    @property
    def voltage_offset(self) -> float:
        """Return the vertical offset of the currently active trace (V)."""
        cached = self._cache[self.active_channel]['voltage_offset']
        if cached is not None: return cached

        # Get value and cache
        value = float(self.query(f':CHAN{self.active_channel}:OFFS?'))
        self._cache[self.active_channel]['voltage_offset'] = value
        return value

    @voltage_offset.setter
    def voltage_offset(self, offset: float) -> None:
        if self.voltage_scale < 0.25:
            assert abs(offset) <= 2
        else:
            assert abs(offset) <= 40
        self.send_command(f':CHAN{self.active_channel}:OFFS {offset:.2g}')
        self._cache[self.active_channel]['voltage_offset'] = offset


    @property
    def voltage_scale(self) -> float:
        """Return the voltage scale (V/div) of the currently active trace."""
        cached = self._cache[self.active_channel]['voltage_scale']
        if cached is not None: return cached

        # Get value and cache
        value = float(self.query(f':CHAN{self.active_channel}:SCAL?'))
        self._cache[self.active_channel]['voltage_scale'] = value
        return value

    @voltage_scale.setter
    def voltage_scale(self, scale: float) -> None:
        """Set the voltage scale (V/div) of the currently active trace."""
        assert 2e-3 <= scale <= 10000

        # Locate smallest safe probe attenuation setting
        attenuations = [1, 5, 10, 50, 100, 500, 1000]
        for attenuation in attenuations:
            if 10 * attenuation >= scale:
                break
        self.probe_attenuation = attenuation
        self.send_command(f':CHAN{self.active_channel}:SCAL {scale:.3g}')
        self._cache[self.active_channel]['voltage_scale'] = scale


    @property
    def time_offset(self) -> float:
        """Return the horizontal time offset (s)."""
        return float(self.query(':TIM:OFFS?'))

    @time_offset.setter
    def time_offset(self, offset: float) -> None:
        assert abs(offset) <= 6 * self.time_scale
        self.send_command(f':TIM:OFFS {offset:.3g}')


    @property
    def time_scale(self) -> float:
        """Return the horizontal time scale (s/div)."""
        return float(self.query(':TIM:SCAL?'))

    @time_scale.setter
    def time_scale(self, scale: float) -> None:
        """Set the time scale (s/div)."""
        assert 2e-9 <= scale <= 50
        self.send_command(f':TIM:SCAL {scale:.3g}')


    @property
    def trigger_source(self) -> str:
        """Return the current edge trigger source."""
        return self.query(':TRIG:EDGE:SOUR?').lower()

    @trigger_source.setter
    def trigger_source(self, source: str) -> None:
        """Set the current edge trigger source."""
        allowed_sources = ['ch1', 'ch2', 'ext', 'acline'] + [f'd{i}' for i in range(16)]
        assert source.lower() in allowed_sources
        self.send_command(f':TRIG:EDGE:SOUR? {source.upper()}')


    @property
    def trigger_mode(self) -> str:
        return self.query(':TRIG:MODE?').lower()

    @trigger_mode.setter
    def trigger_mode(self, mode: str) -> None:
        assert mode.lower() in TRIGGER_MODES
        self.send_command(f':TRIG:MODE {mode.upper()}')


    @property
    def trigger_level(self) -> float:
        """Return the trigger level (V) for rising/falling edges."""
        return float(self.query(':TRIG:EDGE:LEV?'))

    @trigger_level.setter
    def trigger_level(self, level: float) -> None:
        assert abs(level) <= 6 * self.voltage_scale
        self.send_command(f':TRIG:EDGE:LEV {level:.2f}')


    @property
    def trigger_direction(self) -> str:
        """Return the trigger direction (rising/falling) for the edge trigger."""
        return {
            'positive': 'rising',
            'negative': 'falling'
        }[self.query(':TRIG:EDGE:SLOP?').lower()]

    @trigger_direction.setter
    def trigger_direction(self, direction: str) -> None:
        assert direction.lower() in ['rising', 'falling']
        direction = {
            'rising': 'POS',
            'falling': 'NEG'
        }[direction.lower()]
        self.send_command(f':TRIG:EDGE:SLOP {direction}')


    @property
    def times(self) -> Array:
        """Return times along the horizontal axis."""
        offset, scale = self.time_offset, self.time_scale
        N = 610
        return offset + 6 * np.linspace(-scale, scale, N)[self._garbage_points:]

    @property
    def trace(self) -> Array:
        """Return the array of voltage readings for the currently active trace."""
        # Get raw trace bytes
        raw_data = self.query(f':WAV:DATA? CHAN{self.active_channel}', raw=True, delay=0.05)

        # Decode bytes (first 10 are garbage)
        decoded = (~np.frombuffer(raw_data, 'B')[self._garbage_points:]).astype(float)
        return self.voltage_scale * (decoded - 130)/25 - self.voltage_offset

    @property
    def voltage_range(self) -> Tuple[float, float]:
        """Return the voltage range of the active trace."""
        center = -self.voltage_offset
        scale = self.voltage_scale
        return (center - 6*scale, center + 6*scale)

    ##### Convenience Functions #####
    def _create_plot(self):
        fig = plt.figure()
        ax = fig.add_subplot(111)
        ax.set_xlabel('Time (s)')
        ax.set_ylabel('Voltage (V)')
        ax.set_title(f'Channel {self.active_channel}')
        return fig.canvas, ax.plot(self.times, self.trace)[0]

    def quick_plot(self):
        """Show a plot of the current trace."""
        self._create_plot()
        plt.show()

    def live_plot(self):
        """Show a live plot of the current trace."""
        plt.ion()
        canvas, line = self._create_plot()
        try:
            while True:
                line.set_ydata(self.trace)
                canvas.draw()
                canvas.flush_events()
                time.sleep(0.5)
        except KeyboardInterrupt:
            plt.ioff()
