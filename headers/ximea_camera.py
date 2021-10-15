import threading

import numpy as np

import cv2
from colorama import Fore, Style

from uncertainties import ufloat

from ximea import xiapi


class Ximea:
    def __init__(self, exposure=1):
        self.cam = xiapi.Camera()
        self.cam.open_device()
        self.cam.set_imgdataformat('XI_RAW16')
        self.cam.start_acquisition()

        self._img = xiapi.Image()
        self.exposure = exposure
        self.image = None


    def set_roi(self, width, height, x, y):
        self.cam.set_width(width)
        self.cam.set_height(height)
        self.cam.set_offsetX(x)
        self.cam.set_offsetY(y)

    def capture(self):
#        print(f'Capturing image with {self._exposure} s exposure...')
        self.cam.get_image(self._img, timeout=max(round(2e3*self.exposure), 500))
        self.image = self._img.get_image_data_numpy().astype(np.uint16)
#        print('Captured.')

    def async_capture(self):
        self.image = None
        capture_thread = threading.Thread(target=self.capture)
        capture_thread.start()

    @property
    def intensity(self):
        return ufloat(self.image.mean(), self.image.std()/np.sqrt(self.image.size))

    @property
    def exposure(self): return self._exposure

    @exposure.setter
    def exposure(self, value):
        self.cam.set_exposure(value * 1e6)
        self._exposure = value

    def close(self):
        self.cam.stop_acquisition()


if __name__ == '__main__':
    import cv2
    import matplotlib.pyplot as plt

    from uncertainties import ufloat
    from util import plot

    if True:
        cam = Ximea(exposure=1e-4)

        while True:
            print('Capturing...')
            cam.capture()

            image = cam.image.astype(float)
            print(image.shape)
            resized = cv2.resize(image, (968, 728))

#            log = np.round(30 * np.log10(resized + 1)).astype(np.uint8)
            clipped = np.minimum(resized/16, 255).astype(np.uint8)
            cv2.imshow('Image', clipped[200:400, 500:700])

            print(np.mean(image), np.std(image), np.max(image))

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
