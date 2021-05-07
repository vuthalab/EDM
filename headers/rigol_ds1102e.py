import numpy as np
import matplotlib.pyplot as plt

from headers.usbtmc import USBTMCDevice


TRIGGER_MODES = ['edge', 'pulse', 'video', 'scope', 'pattern', 'duration', 'alternation']


class RigolDS1102e(USBTMCDevice):
    """USBMTC interface for DS1102e oscilloscope."""

    # Currently active channel (emulated, not on scope)
    active_channel = 1

    # Number of garbage points at start of trace
    _garbage_points = 10

    def __init__(self):
        super().__init__('/dev/usbtmc0', mode='direct')
        self.send_command(':RUN')

    def stop(self):
        self.send_command(':STOP')
        super().stop()

    def __str__(self):
        trigger_mode = self.trigger_mode
        if trigger_mode == 'edge':
            trigger_mode = f'{self.trigger_direction} edge @ {self.trigger_level:.2f} V'
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
        return float(self.query(f':CHAN{self.active_channel}:PROB?'))

    @probe_attenuation.setter
    def probe_attenuation(self, attenuation: float) -> None:
        self.send_command(f':CHAN{self.active_channel}:PROB {attenuation}')

    @property
    def voltage_offset(self) -> float:
        return float(self.query(f':CHAN{self.active_channel}:OFFS?'))

    @voltage_offset.setter
    def voltage_offset(self, offset: float) -> None:
        if self.voltage_scale < 0.25:
            assert abs(offset) <= 2
        else:
            assert abs(offset) <= 40
        self.send_command(f':CHAN{self.active_channel}:OFFS {offset:.2g}')

    @property
    def voltage_scale(self) -> float:
        return float(self.query(f':CHAN{self.active_channel}:SCAL?'))

    @voltage_scale.setter
    def voltage_scale(self, scale: float) -> None:
        """Set the voltage scale (V/div)."""
        assert 2e-3 <= scale <= 10000

        # Locate smallest safe probe attenuation setting
        attenuations = [1, 5, 10, 50, 100, 500, 1000]
        for attenuation in attenuations:
            if 10 * attenuation >= scale:
                break
        self.probe_attenuation = attenuation
        self.send_command(f':CHAN{self.active_channel}:SCAL {scale:.3g}')

    @property
    def time_offset(self) -> float: return float(self.query(':TIM:OFFS?'))

    @time_offset.setter
    def time_offset(self, offset: float) -> None:
        assert abs(offset) <= 6 * self.time_scale
        self.send_command(f':TIM:OFFS {offset:.3g}')

    @property
    def time_scale(self) -> float: return float(self.query(':TIM:SCAL?'))

    @time_scale.setter
    def time_scale(self, scale: float) -> None:
        """Set the time scale (seconds/div)."""
        assert 2e-9 <= scale <= 50
        self.send_command(f':TIM:SCAL {scale:.3g}')

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
    def times(self):
        """Return times along the horizontal axis."""
        offset, scale = self.time_offset, self.time_scale
        N = 610
        return offset + 6 * np.linspace(-scale, scale, N)[self._garbage_points:]

    @property
    def trace(self):
        # Get raw trace bytes
        raw_data = self.query(f':WAV:DATA? CHAN{self.active_channel}', raw=True, delay=0.5)

        # Decode bytes (first 10 are garbage)
        decoded = (~np.frombuffer(raw_data, 'B')[self._garbage_points:]).astype(float)
        return self.voltage_scale * (decoded - 130)/25 - self.voltage_offset

    ##### Convenience Functions #####
    def quick_plot(self):
        plt.plot(self.times, self.trace)
        plt.xlabel('Time (s)')
        plt.ylabel('Voltage (V)')
        plt.title(f'Channel {self.active_channel}')
        plt.show()
