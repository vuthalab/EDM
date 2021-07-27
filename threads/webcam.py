import itertools

import numpy as np
import cv2

from headers.oceanfx import OceanFX
from headers.zmq_server_socket import create_server

from headers.edm_util import add_timestamp


def webcam_thread():
    webcam = cv2.VideoCapture(2)

    # Set webcam capture parameters.
    # Use v4l2-ctl to see all available settings.
    webcam.set(cv2.CAP_PROP_FRAME_WIDTH, 1920) # Set 1080p. 4k doesn't work for some reason, so just enable 2x digital zoom later.
    webcam.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

    webcam.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1) # Disable autoexposure
    webcam.set(cv2.CAP_PROP_EXPOSURE, 2047) # Usually keep this at max
    webcam.set(cv2.CAP_PROP_GAIN, 5) # Tweak this instead of exposure for better low-light visibility

    webcam.set(cv2.CAP_PROP_AUTOFOCUS, 0) # Disable stupid autofocus
    webcam.set(cv2.CAP_PROP_FOCUS, 150) # Tweak this to get best focus

    webcam.set(cv2.CAP_PROP_PAN, 0)
    webcam.set(cv2.CAP_PROP_TILT, 0)

    webcam.set(cv2.CAP_PROP_SHARPNESS, 0) # Disable whatever voodoo sharpness processing they have
    webcam.set(cv2.CAP_PROP_FPS, 10) # Limit FPS

    # Superresolution
    sr = cv2.dnn_superres.DnnSuperResImpl_create()
    sr.readModel('models/ESPCN_x2.pb')
    sr.setModel('espcn', 2)

    with create_server('webcam') as publisher:
        for i in itertools.count():
            ret, saph_image = webcam.read()
            if i % 5 != 0: continue

            fragment = saph_image[:, 450:1400]

            # Adjust exposure
#            saturation = np.max(fragment[:, :, 0]) # max of blue channel
#            if saturation > 250:
#                exposure = webcam.get(cv2.CAP_PROP_EXPOSURE)
#                webcam.set(cv2.CAP_PROP_EXPOSURE, exposure//2)

#            if saturation < 50:
#                exposure = webcam.get(cv2.CAP_PROP_EXPOSURE)
#                webcam.set(cv2.CAP_PROP_EXPOSURE, exposure*2)

            resized = fragment
#            resized = sr.upsample(fragment)
            annotated = np.array(add_timestamp(resized))

            raw_png = cv2.imencode('.png', fragment)[1].tobytes()
            annotated_png = cv2.imencode('.png', annotated)[1].tobytes()

            publisher.send({
                'annotated': annotated_png,
                'raw': raw_png,
                'index': i,
            })
