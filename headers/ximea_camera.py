import numpy as np

import cv2
from colorama import Fore, Style

from ximea import xiapi


class Ximea:
    def __init__(self, exposure=1e6):
        self.cam = xiapi.Camera()
        self.cam.open_device()
        self.cam.set_exposure(exposure)
        self.cam.set_imgdataformat('XI_RAW16')
        self.cam.start_acquisition()

        self._img = xiapi.Image()
        self._cache = []

    def set_roi(self, width, height, x, y):
        self.cam.set_width(width)
        self.cam.set_height(height)
        self.cam.set_offsetX(x)
        self.cam.set_offsetY(y)


    def capture(self):
        info_prefix = f'  [{Fore.BLUE}INFO{Style.RESET_ALL}]'
        print(info_prefix, 'Capturing CBS image.')
        try:
            self.cam.get_image(self._img, timeout=1200)
        except:
            print(info_prefix, f'CBS capture {Fore.RED}failed{Style.RESET_ALL}.')
            return False
        print(info_prefix, f'CBS capture {Fore.GREEN}succeeded{Style.RESET_ALL}.')

        data = self._img.get_image_data_numpy().astype(int)
        self._cache.append(data)
        self._cache = self._cache[-16:]
        return True

    @property
    def image(self):
        return np.minimum(sum(self._cache), 65535).astype(np.uint16)

    def close(self):
        self.cam.stop_acquisition()
