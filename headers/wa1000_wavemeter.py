import serial

from uncertainties import ufloat

import numpy as np


class WA1000Wavemeter:
    def __init__(self):
        self._conn = serial.Serial('/dev/wavemeter', 19200, timeout=0.1)
        self.wavelength = None

    def poll(self):
        lines = self._conn.read(4096).split(b'\r\n')[:-1]

        wavelengths = []
        for line in lines:
            try:
                wavelength = float(line.split(b',')[0][1:])
            except:
                continue
            if wavelength > 800:
                wavelengths.append(wavelength)

        if wavelengths:
            self.wavelength = ufloat(np.mean(wavelengths), np.std(wavelengths))
        else:
            print('Error:', lines[-1])
            self.wavelength = None



if __name__ == '__main__':
    import time

    wavemeter = WA1000Wavemeter()
    while True:
        wavemeter.poll()
        print(wavemeter.wavelength)
        time.sleep(3)
