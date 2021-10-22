try:
    from headers.usb4000spectrometer import USB4000Spectrometer
except:
    from usb4000spectrometer import USB4000Spectrometer


class QEProSpectrometer(USB4000Spectrometer):
    def __init__(self):
        super().__init__(multiplexer_port=31422, name='QE Pro')

    @property
    def temperature(self):
        """Return the temperature (°C) of the cooled CCD."""
        return float(self.query(f'GET_TEMP'))

    @temperature.setter
    def temperature(self, value):
        """Set the temperature (°C) of the cooled CCD."""
        response = self.query(f'SET_TEMP {value:.8f}')
        if response != 'ok': raise Exception(response)


if __name__ == '__main__':
    spec = QEProSpectrometer()
