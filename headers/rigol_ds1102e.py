import numpy as np
import matplotlib.pyplot as plt

from headers.usbtmc import USBTMCDevice


class RigolDS1102e(USBTMCDevice):
    """USBMTC interface for DS1102e oscilloscope."""

    # Currently active channel (emulated, not on scope)
    active_channel = 1

    # Number of garbage points at start of trace
    _garbage_points = 10

    def __init__(self):
        super().__init__('/dev/usbtmc0', mode='direct')

    def __str__(self):
        return '\n'.join([
            f'Model: {self.name}',
            f'Active Channel: {self.active_channel}',
            f'Voltage Offset: {self.voltage_offset}',
            f'Voltage Scale : {self.voltage_scale} V/div',
        ])

    ##### Virtual Properties #####
    @property
    def voltage_offset(self) -> float:
        return float(self.query(f':CHAN{self.active_channel}:OFFS?'))

    @property
    def voltage_scale(self) -> float:
        return float(self.query(f':CHAN{self.active_channel}:SCAL?'))

    @property
    def time_offset(self) -> float: return float(self.query(':TIM:OFFS?'))

    @property
    def time_scale(self) -> float: return float(self.query(':TIM:SCAL?'))

    @property
    def times(self):
        """Return times along the horizontal axis."""
        offset, scale = self.time_offset, self.time_scale
        N = 610
        return offset + 6 * np.linspace(-scale, scale, N)[self._garbage_points:]

    @property
    def trace(self):
        # Get raw trace bytes
        raw_data = self.query(f':WAV:DATA? CHAN{self.active_channel}', raw=True)

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
