import threading
import time
import numpy as np

try:
    from headers.usbtmc import USBTMCDevice
except:
    from usbtmc import USBTMCDevice



GARBAGE_POINTS = 20 # Discard this many points from start of data

class USB4000Spectrometer(USBTMCDevice):
    def __init__(self, multiplexer_port=31421, name=None, timeout=120):
        super().__init__(multiplexer_port, mode='multiplexed', name=name, timeout=timeout)
        self._exposure = None
        self._wavelengths = None
        self._intensities = None
        self._capture_time = None

    def reset(self):
        """Interrupt the current capture."""
        cache = self.exposure
        self.exposure = 12345
        self.exposure = cache

    def capture(self, fresh_sample=False):
        if fresh_sample: self.reset()

        while True:
            start_time = time.monotonic()
            response = self.query(f'INTENSITIES')
            if not fresh_sample: break

            # Ensure we get a fresh capture
            if time.monotonic() - start_time > 0.9 * self.exposure / 1e6: break
            print('Skipping cached spectrum')
            time.sleep(0.5)

        self._intensities = np.array([float(x) for x in response.split()])[GARBAGE_POINTS:]
        self._capture_time = time.time()

    def async_capture(self, fresh_sample=False):
        self._intensities = None
        capture_thread = threading.Thread(target=lambda: self.capture(fresh_sample=fresh_sample))
        capture_thread.start()

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
        return self._intensities


if __name__ == '__main__':
    import time
    import matplotlib.pyplot as plt

    spec = USB4000Spectrometer()
    spec.exposure = 10


    plt.ion()
    fig = plt.figure()
    spec.capture()
    line, = plt.plot(spec.wavelengths, spec.intensities)

    plt.xlabel('Wavelength (nm)')
    plt.ylabel('Intensity (counts)')
    plt.ylim(0, 65536)
    while True:
        time.sleep(0.5)
        spec.capture()
        line.set_ydata(spec.intensities)
        fig.canvas.draw()
        fig.canvas.flush_events()
