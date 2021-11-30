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

    import time
    import matplotlib.pyplot as plt

    spec = QEProSpectrometer()
    spec.exposure = 1E6 # us
    spec.temperature = -30

    plt.ion()
    fig = plt.figure()
    spec.capture()
    line, = plt.plot(spec.wavelengths, spec.intensities)

    plt.xlabel('Wavelength (nm)')
    plt.ylabel('Intensity (counts)')
    plt.ylim(0, 65536)
    while True:
        time.sleep(2)
        spec.capture()
        line.set_ydata(spec.intensities)
        fig.canvas.draw()
        fig.canvas.flush_events()
