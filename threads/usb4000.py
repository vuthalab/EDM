import time

import numpy as np

from headers.usb4000spectrometer import USB4000Spectrometer
from headers.zmq_server_socket import create_server

from headers.edm_util import deconstruct
from headers.util import nom, std, unweighted_mean


window_width = 100
speed_of_light = 299792458

def usb4000_thread():
    spectrometer = USB4000Spectrometer()
    spectrometer.exposure = 32

    wavelengths = spectrometer.wavelengths

    with create_server('usb4000') as publisher:
        while True:
            spectrometer.capture()
            spectrum = spectrometer.intensities
            spectrum -= np.median(spectrum)

            peak_coarse = np.argmax(spectrum[500:]) + 500 #For some reason, the first few points are garbage at higher wavelengths, and this messes up the spectrometer peak fitting
            window = spectrum[peak_coarse - window_width : peak_coarse + window_width]
            wl_window = wavelengths[peak_coarse - window_width : peak_coarse + window_width]

            try:
                peak_fine = np.average(wl_window, weights=window)
                peak_variance = np.average(np.square(wl_window - peak_fine), weights=window)
                assert peak_variance > 0
                peak_stdev = np.sqrt(peak_variance)
            except:
                time.sleep(0.5)
                continue

            data = {
                'wavelength': peak_fine,
                'linewidth': 2 * peak_stdev, 
                'frequency': speed_of_light / peak_fine,
            }
            publisher.send(data)

            time.sleep(0.2)


            if np.max(spectrum) > 50000:
                spectrometer.exposure = max(spectrometer.exposure//2, 10)
                time.sleep(0.5)

            if np.max(spectrum) < 1000:
                spectrometer.exposure = min(spectrometer.exposure*2, 2e5)
                time.sleep(0.5)
