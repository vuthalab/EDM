import itertools

import numpy as np
import cv2

from headers.oceanfx import OceanFX
from headers.zmq_server_socket import create_server

from headers.edm_util import add_timestamp


def webcam_thread():
    webcam = cv2.VideoCapture(0)
    webcam.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1)
    webcam.set(cv2.CAP_PROP_EXPOSURE, 64)

    with create_server('webcam') as publisher:
        for i in itertools.count():
            ret, saph_image = webcam.read()
            if i % 5 != 0: continue

            fragment = saph_image[330:180:-1, 450:300:-1, :]

            # Adjust exposure
            saturation = np.max(np.mean(fragment, axis=-1))
            if saturation > 250:
                exposure = webcam.get(cv2.CAP_PROP_EXPOSURE)
                webcam.set(cv2.CAP_PROP_EXPOSURE, exposure//2)

            if saturation < 50:
                exposure = webcam.get(cv2.CAP_PROP_EXPOSURE)
                webcam.set(cv2.CAP_PROP_EXPOSURE, exposure*2)

            resized = cv2.resize(fragment, (450, 450))
            annotated = np.array(add_timestamp(resized))

            raw_png = cv2.imencode('.png', fragment)[1].tobytes()
            annotated_png = cv2.imencode('.png', annotated)[1].tobytes()

            publisher.send({
                'annotated': annotated_png,
                'raw': raw_png,
                'index': i,
            })
