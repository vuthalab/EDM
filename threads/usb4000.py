import time

import numpy as np

from headers.usb4000spectrometer import USB4000Spectrometer
from headers.zmq_server_socket import create_server

from headers.edm_util import deconstruct
from headers.util import nom, std, unweighted_mean


window_width = 40
speed_of_light = 299792458

def usb4000_thread():
    spectrometer = USB4000Spectrometer()
    spectrometer.exposure = 30

    wavelengths = spectrometer.wavelengths

    with create_server('usb4000') as publisher:
        while True:
            spectrum = spectrometer.intensities
            spectrum -= np.median(spectrum)

            peak_coarse = np.argmax(spectrum)
            window = spectrum[peak_coarse - window_width : peak_coarse + window_width]

            try:
                peak_fine = np.average(wavelengths[peak_coarse - window_width : peak_coarse + window_width], weights=window)
            except:
                time.sleep(0.5)
                continue

            data = {
                'wavelength': peak_fine,
                'frequency': speed_of_light / peak_fine,
            }
            publisher.send(data)

            time.sleep(0.2)
