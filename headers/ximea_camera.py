import threading
import time

import numpy as np

import cv2
from colorama import Fore, Style

from uncertainties import ufloat

from ximea import xiapi


class Ximea:
    def __init__(self, exposure=1e-3):
        self.cam = xiapi.Camera()
        self.cam.open_device()
        self.cam.set_imgdataformat('XI_RAW16')
        self.cam.start_acquisition()

        self._img = xiapi.Image()
        self.exposure = exposure
        self.image = None
        self._capture_time = None # time of last capture


    def set_roi(self, width, height, x, y):
        self.cam.set_width(width)
        self.cam.set_height(height)
        self.cam.set_offsetX(x)
        self.cam.set_offsetY(y)

    def interrupt(self):
        """Interrupt the existing capture, if any."""
        return # TEMP
        cache = self.exposure
        self.exposure = 1.2345
        self.exposure = cache

    def capture(self, fresh_sample=False):
        if fresh_sample: self.interrupt()

        while True:
            start_time = time.monotonic()
            self.cam.get_image(self._img, timeout=max(round(2e3*self.exposure), 500))
            if not fresh_sample: break

            # Ensure we get a fresh capture
            if time.monotonic() - start_time > 0.8 * self.exposure: break
            print('Skipping cached image')
            if self.exposure > 0.1: time.sleep(0.05)

        self.image = self._img.get_image_data_numpy().astype(np.uint16)
        self._capture_time = time.time()


    def async_capture(self, fresh_sample=False):
        self.image = None
        capture_thread = threading.Thread(target=lambda: self.capture(fresh_sample=fresh_sample))
        capture_thread.start()

    @property
    def raw_rate(self):
        """Return raw total count rate."""
        return self.raw_rate_image.sum()

    @property
    def saturation(self):
        """Return maximum saturation in %."""
        # Percentile to ignore salt-and-pepper noise
#        return 100 * np.percentile(self.background_subtracted_image, 99) / 4095
        return 100 * np.percentile(self.image, 99) / 4095

    @property
    def background_subtracted_image(self):
        background = np.percentile(self.image, 5) # Compute background level
        return self.image - background

    @property
    def rate_image(self):
        """Return an image showing hit rate (counts/s) in each pixel."""
        return self.background_subtracted_image / self.exposure

    @property
    def raw_rate_image(self):
        """Return an image showing hit rate (counts/s) in each pixel."""
        return self.image / self.exposure

    @property
    def exposure(self): return self._exposure

    @exposure.setter
    def exposure(self, value):
        self.cam.set_exposure(value * 1e6)
        self._exposure = value
        time.sleep(0.1)

    def close(self):
        self.cam.stop_acquisition()


if __name__ == '__main__':
    import cv2
    import matplotlib.pyplot as plt

    from uncertainties import ufloat
    from util import plot

    import sys

    if True:
        if len(sys.argv) > 1:
            exposure = float(sys.argv[1])
        else:
            exposure = float(input('Exposure time (s)? '))
        cam = Ximea(exposure=exposure)

        while True:
            print('Capturing...')
            cam.capture()

            rate_image = cam.rate_image
            resized = cv2.resize(rate_image, (968, 728))
            peak = np.percentile(resized, 99.9)
#            peak = 4096 # Disable autoscale
            processed = np.maximum(np.minimum(256 * resized/(1.2*peak), 255), 0).astype(np.uint8)
#            processed = np.maximum(np.minimum(30 * np.log(resized), 255), 0).astype(np.uint8)
            cv2.imshow('Image', processed)
            raw_rate = (cam.image/cam.exposure).sum()
            print(f'{raw_rate/1e6:.3f} Mcounts/s raw | {rate_image.sum()/1e6:.3f} Mcounts/s | Saturation: {cam.saturation:.2f} %')

            time.sleep(0.2)

            if cv2.waitKey(1) == ord('q'): break
        cv2.destroyAllWindows()

    if False:
        cam = Ximea(exposure=2)

#        cam.capture()
#        dead_pixels = np.where(cam.image > 5 * cam.image.mean())

#        with open('../calibration/ximea-dead-pixels.txt', 'w') as f:
#            for entry in zip(*dead_pixels):
#                print(*entry, file=f)

#        plt.imshow(cam.image, aspect='auto', interpolation='none')
#        plt.show()


#        exposures = np.logspace(-3, 1, 10)
#        values = []
#
#        np.random.shuffle(exposures)
#
#        for exposure in exposures:
#            print(exposure)
#            cam.exposure = exposure * 1e6
#            cam.capture()
#            values.append(cam.intensity)
#
#        values = np.array(values)
#
#        sort_idx = np.argsort(exposures)
#        plot(exposures[sort_idx], values[sort_idx], continuous=True)
#        plt.xlabel('Exposure (s)')
#        plt.ylabel('Mean Brightness (counts/pixel)')
#        plt.xscale('log')
#        plt.yscale('log')
#        plt.show()
