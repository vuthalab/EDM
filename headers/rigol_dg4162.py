from typing import Union, Literal

try:
    from headers.usbtmc import USBTMCDevice
except:
    from usbtmc import USBTMCDevice


Channel = Union[Literal[1], Literal[2]]

# List of waveform shapes.
# Many, many other options omitted.
# If desired, see the programming guide.
WAVEFORM_SHAPES = [
    'sinusoid', 'square', 'ramp', 'pulse',
    'noise', 'harmonic',
]


class RigolDG4162(USBTMCDevice):
    """USBMTC interface for DG4162 function generator."""

    """The currently active channel (emulated, not on device)."""
    active_channel: Channel = 1

    def __init__(self):
        super().__init__('/dev/signal_generator', mode='direct')
        self.active_channel = 1


    def __str__(self) -> str:
        enabled = 'On' if self.enabled else 'Off'
        return '\n'.join([
            f'Model: {self.name}',
            f'Selected Channel: {self.active_channel} ({enabled})',
            f'Waveform: {self.frequency:.3g} Hz {self.waveform}, {self.amplitude} {self.amplitude_unit}',
        ])


    ##### Virtual Properties #####
    @property
    def frequency(self) -> float:
        """Return the frequency (Hz) of the currently active channel."""
        return float(self.query(f':SOURCE{self.active_channel}:FREQ?'))

    @frequency.setter
    def frequency(self, frequency: float) -> None:
        """Set the frequency (Hz) of the currently active channel."""
        assert 1e-6 <= frequency <= 160e6
        self.send_command(f':SOURCE{self.active_channel}:FREQ {frequency:.3g}')


    @property
    def waveform(self) -> str:
        """Return the waveform shape of the currently active channel."""
        return self.query(f':SOURCE{self.active_channel}:FUNC?')

    @waveform.setter
    def waveform(self, shape: str) -> None:
        """Set the waveform shape of the currently active channel."""
        assert shape.lower() in WAVEFORM_SHAPES
        self.send_command(f':SOURCE{self.active_channel}:FUNC {shape.upper()}')


    @property
    def amplitude(self) -> float:
        """
        Return the amplitude of the currently active channel.
        Units should be queried separately.
        """
        return self.query(f':SOURCE{self.active_channel}:VOLT?')

    @amplitude.setter
    def amplitude(self, value: float) -> None:
        """
        Sets the amplitude of the currently active channel.
        Units should be queried separately.
        """
        self.send_command(f':SOURCE{self.active_channel}:VOLT {value:.3g}')


    @property
    def amplitude_unit(self) -> str:
        """Return the amplitude unit (Vpp, Vrms, dBm) of the currently active channel."""
        return {
            'VPP': 'Vpp',
            'VRMS': 'Vrms',
            'DBM': 'dBm',
        }[self.query(f':SOURCE{self.active_channel}:UNIT?')]

    @amplitude_unit.setter
    def amplitude_unit(self, unit: str) -> None:
        """Set the amplitude unit of the currently active channel."""
        assert unit.lower() in ['vpp', 'vrms', 'dbm']
        self.send_command(f':SOURCE{self.active_channel}:UNIT {unit.upper()}')


    @property
    def enabled(self) -> bool:
        """Query whether the currently selected channel is outputting a signal."""
        return self.query(f':OUTPUT{self.active_channel}?') == 'ON'

    @enabled.setter
    def enabled(self, enable: bool) -> None:
        enable_str = 'ON' if enable else 'OFF'
        self.send_command(f':OUTPUT{self.active_channel} {enable_str}')


    ##### Square Wave Utils #####
    @property
    def duty_cycle(self) -> float:
        """
        Return the duty cycle (%) of the currently active channel.
        Must be a square wave.
        """
        return float(self.query(f':SOURCE{self.active_channel}:FUNC:SQUARE:DCYCLE?'))

    @duty_cycle.setter
    def duty_cycle(self, cycle):
        """
        Sets the duty cycle (%) of the currently active channel.
        Must be a square wave.
        """
        self.send_command(f':SOURCE{self.active_channel}:FUNC:SQUARE:DCYCLE {cycle:.3f}')

    @property
    def high(self) -> float:
        """
        Return the high voltage of the currently active channel.
        Must be a square wave.
        """
        return float(self.query(f':SOURCE{self.active_channel}:VOLT:HIGH?'))

    @high.setter
    def high(self, value: float) -> None:
        """
        Sets the high voltage of the currently active channel.
        Must be a square wave.
        """
        self.send_command(f':SOURCE{self.active_channel}:VOLT:HIGH {value:.3g}')

    @property
    def low(self) -> float:
        """
        Return the low voltage of the currently active channel.
        Must be a square wave.
        """
        return float(self.query(f':SOURCE{self.active_channel}:VOLT:LOW?'))

    @low.setter
    def low(self, value: float) -> None:
        """
        Sets the low voltage of the currently active channel.
        Must be a square wave.
        """
        self.send_command(f':SOURCE{self.active_channel}:VOLT:LOW {value:.3g}')




if __name__ == '__main__':
    fg = RigolDG4162()
