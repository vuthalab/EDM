import numpy as np

try:
    from headers.usbtmc import USBTMCDevice
except:
    from usbtmc import USBTMCDevice



GARBAGE_POINTS = 20 # Discard this many points from start of data

class USB4000Spectrometer(USBTMCDevice):
    def __init__(self, multiplexer_port=31421, name=None):
        super().__init__(multiplexer_port, mode='multiplexed', name=name)
        self._exposure = None
        self._wavelengths = None

    @property
    def exposure(self):
        """Get the exposure, in microseconds."""
        return self._exposure

    @exposure.setter
    def exposure(self, value: int):
        """Set the exposure, in microseconds."""
        response = self.query(f'SET_EXPOSURE {value:.0f}')
        if response != 'ok':
            raise Exception(response)
        self._exposure = value

    @property
    def wavelengths(self):
        if self._wavelengths is None:
            response = self.query(f'WAVELENGTHS')
            self._wavelengths = np.array([float(x) for x in response.split()])[GARBAGE_POINTS:]
        return self._wavelengths

    @property
    def intensities(self):
        response = self.query(f'INTENSITIES')
        return np.array([float(x) for x in response.split()])[GARBAGE_POINTS:]


if __name__ == '__main__':
    import time
    import matplotlib.pyplot as plt

    spec = USB4000Spectrometer()
#    spec.exposure = 10

    plt.ion()
    fig = plt.figure()
    line, = plt.plot(spec.wavelengths, spec.intensities)

    plt.xlabel('Wavelength (nm)')
    plt.ylabel('Intensity (counts)')
    plt.ylim(0, 65536)
    while True:
        time.sleep(0.5)
        line.set_ydata(spec.intensities)
        fig.canvas.draw()
        fig.canvas.flush_events()
