try:
    from headers.usbtmc import USBTMCDevice
except:
    from usbtmc import USBTMCDevice

class RigolDP832(USBTMCDevice):
    def __init__(self, device = '/dev/usbtmc2', default_source = 1):
        super().__init__(device, mode='direct')
        self.source = default_source

        # Cache to avoid unnecessary commands
        self._voltage = None
        self._enabled = None

    @property
    def voltage(self):
        """Gets the voltage for the currently selected source."""
        return float(self.query(f':SOURCE{self.source}:VOLTAGE?'))

    @voltage.setter
    def voltage(self, voltage: float):
        """Sets the voltage for the currently selected source."""
        if self._voltage != voltage:
            self.send_command(f':SOURCE{self.source}:VOLTAGE {voltage:.3f}')
        self._voltage = voltage

    @property
    def current(self):
        """Gets the current limit for the currently selected source."""
        return float(self.query(f':SOURCE{self.source}:CURRENT?'))

    @current.setter
    def current(self, current: float):
        """Sets the current limit for the currently selected source."""
        self.send_command(f':SOURCE{self.source}:CURRENT {current:.3f}')

    @property
    def enabled(self):
        """Queries the status of the currently selected source."""
        if self._enabled is None:
            self._enabled = (self.query(f':OUTPUT? CH{self.source}') == 'ON')
        return self._enabled

    @enabled.setter
    def enabled(self, enable: bool):
        """Enables or disables the currently selected source."""
        status = 'ON' if enable else 'OFF'
        self.send_command(f':OUTPUT CH{self.source},{status}')
        self._enabled = enable

    def enable(self):
        if not self.enabled: self.enabled = True

    def disable(self):
        if self.enabled: self.enabled = False




class LaserSign(RigolDP832):
    def on(self):
        self.voltage = 24
        self.current = 0.1
        self.enable()

    def off(self):
        self.disable()

    def is_on(self):
        return self.enabled


class TiSaphMicrometer:
    def __init__(self):
        self._magnitude = RigolDP832('/dev/upper_power_supply', 3)
        self._direction = RigolDP832('/dev/lower_power_supply', 3)

        assert 'DP832' in self._magnitude.name
        assert 'DP831' in self._direction.name

        self._magnitude.voltage = 0
        self._direction.voltage = 0

        self._magnitude.current = 0.1
        self._direction.current = 0.07

        self._magnitude.enable()
        self._direction.enable()

    @property
    def voltage(self):
        direction = self._direction.voltage > -6
        direction = int(direction) * 2 - 1
        return self._magnitude.voltage * direction

    @voltage.setter
    def voltage(self, volt: float):
        assert volt <= 5 and volt >= -5

        if volt != 0:
            self._direction.voltage = 0 if volt > 0 else -12
        self._magnitude.voltage = abs(volt)

    @property
    def speed(self):
        return 100 * self.voltage / 5

    @speed.setter
    def speed(self, speed: float):
        if speed > 100 or speed < -100: raise ValueError('Speed must be between -100 and 100!')
        self.voltage = speed * 5/100

    def off(self):
        self.voltage = 0

if __name__ == '__main__':
    laser_sign = LaserSign()
    micrometer = TiSaphMicrometer()
