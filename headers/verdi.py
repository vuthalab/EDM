try:
    from headers.usbtmc import USBTMCDevice
except:
    from usbtmc import USBTMCDevice


class Verdi(USBTMCDevice):
    def __init__(self, multiplexer_port=31420):
        super().__init__(multiplexer_port, mode='multiplexed', name='Verdi')
#        super().__init__('/dev/verdi', mode='serial', name='Verdi')
        self.query('E = 0')
        self.query('> = 0')

        self._power = None

    @property
    def power(self):
        """Return the current output power in watts."""
        return float(self.query('?P'))

    @power.setter
    def power(self, power: float):
        """Set the current output power in watts."""
        if self._power != power: # Cache to avoid unnecessary messages
            self.query(f'P = {power:.4f}')
        self._power = power


    @property
    def shutter_open(self):
        """Returns whether the shutter is open."""
        return bool(int(self.query('?S')))

    @shutter_open.setter
    def shutter_open(self, open: bool):
        """Sets the shutter status."""
        self.query(f'S = {int(open)}')


    @property
    def is_on(self):
        """Returns whether the laser is on."""
        return int(self.query('?L')) == 1

    @is_on.setter
    def is_on(self, on: bool):
        """Sets the laser power status."""
        self.query(f'L = {int(on)}')

    @property
    def current(self):
        return float(self.query('?C'))

    @property
    def keyswitch(self):
        return bool(int(self.query('?K')))

    # Temperatures
    @property
    def vanadate_temp(self):
        return float(self.query('?VT'))

    @property
    def baseplate_temp(self):
        return float(self.query('?BT'))

    @property
    def diode1_temp(self):
        return float(self.query('?D1T'))

    @property
    def diode2_temp(self):
        return float(self.query('?D2T'))


    ##### Convenience functions #####
    def open_shutter(self): self.shutter_open = True
    def close_shutter(self): self.shutter_open = False

    def on(self):
        if not self.keyswitch:
            raise ValueError('Keyswitch not in on position!')
        self.is_on = True
        self.open_shutter()
        self.power = 1

    def off(self):
        self.close_shutter()
        self.power = 0.01
        self.is_on = False


    def status(self):
        ks_status = 'On' if self.keyswitch else 'Standby'
        print(f'Keyswitch: {ks_status}')

        status = 'Energized' if self.is_on else 'Standby'
        print(f'Status: {status}')

        shutter_status = 'Open' if self.shutter_open else 'Closed'
        print(f'Shutter: {shutter_status}')

        print(f'Power: {self.power:.2f} W')
        print(f'Current: {self.current:.2f} A')



if __name__ == '__main__':
    verdi = Verdi()
