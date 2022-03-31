import time
import numpy as np
import cv2

from simple_pyspin import Camera

from headers.zmq_server_socket import create_server
from headers.edm_util import deconstruct

from models.image_track import fit_image_spot


def plume_camera_thread():
    camera = Camera(0)

    camera.AcquisitionFrameRateEnable = True
    camera.AcquisitionFrameRate = 5
    camera.PixelFormat = 'Mono16'

    camera.init()

    camera.GainAuto = 'Off'
    camera.Gain = 1

    camera.ExposureAuto = 'Off'
    camera.ExposureTime = 200 # Microseconds
#    camera.ExposureTime = 1000000 # Microseconds

    camera.start()

    with create_server('plume-cam') as publisher:
        while True:
            image = camera.get_array()
            timestamp = time.time()
            cx, cy, intensity, saturation = fit_image_spot(image)

            # Downsample if 16-bit
            if isinstance(image[0][0], np.uint16):
                image = np.minimum(image/256 + 0.5, 255).astype(np.uint8)

            # Encode PNG
            png = cv2.imencode('.png', image)[1].tobytes()

            publisher.send({
                'timestamp': timestamp,
                'center': {
                    'x': deconstruct(cx),
                    'y': deconstruct(cy),
                },
                'intensity': intensity,
                'saturation': saturation,
                'png': png,
            })

            time.sleep(0.05)
