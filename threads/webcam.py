import itertools

import numpy as np
import cv2

from headers.oceanfx import OceanFX
from headers.zmq_server_socket import create_server
from headers.zmq_client_socket import connect_to

from headers.edm_util import add_timestamp


def webcam_thread():
    webcam = cv2.VideoCapture(0)

    # Set webcam capture parameters.
    # Use v4l2-ctl to see all available settings.
    webcam.set(cv2.CAP_PROP_FRAME_WIDTH, 1920) # Set 1080p. 4k doesn't work for some reason, so just enable 2x digital zoom later.
    webcam.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

    webcam.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1) # Disable autoexposure
    webcam.set(cv2.CAP_PROP_EXPOSURE, 1500) # Usually keep this at max (0-2047)
    webcam.set(cv2.CAP_PROP_GAIN, 1) # Tweak this instead of exposure for better low-light visibility (1-5)

    webcam.set(cv2.CAP_PROP_AUTOFOCUS, 0) # Disable stupid autofocus
    webcam.set(cv2.CAP_PROP_FOCUS, 60) # Tweak this to get best focus (0-255)

    webcam.set(cv2.CAP_PROP_PAN, 0) # Horizontal shift
    webcam.set(cv2.CAP_PROP_TILT, 0) # Vertical shift

    webcam.set(cv2.CAP_PROP_SHARPNESS, 0) # Disable whatever voodoo sharpness processing they have
    webcam.set(cv2.CAP_PROP_FPS, 10) # Limit FPS

    # Superresolution
    sr = cv2.dnn_superres.DnnSuperResImpl_create()
    sr.readModel('models/ESPCN_x2.pb')
    sr.setModel('espcn', 2)

    publisher_socket = connect_to('edm-monitor')

    with create_server('webcam') as publisher:
        label = ''
        for i in itertools.count():
            ret, saph_image = webcam.read()
#            if i % 2 != 0: continue

#            print(saph_image.shape)

#            resized = sr.upsample(fragment)
#            resized = cv2.resize(saph_image, (960, 540))
            fragment = saph_image[200:800, 800:1300]

            raw_png = cv2.imencode('.png', fragment)[1].tobytes()

            publisher.send({
                'raw': raw_png,
                'index': i,
            })
