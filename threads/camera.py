import time
import numpy as np
import cv2

from simple_pyspin import Camera

from headers.zmq_server_socket import create_server
from headers.util import unweighted_mean
from headers.edm_util import deconstruct, Timer

from models.image_track import fit_image
from models.fringe import FringeModel

def camera_thread():
    camera = Camera(1)
    camera.init()
    try:
        camera.start()
    except:
        pass
    camera.GainAuto = 'Off'
    camera.Gain = 10
    camera.ExposureAuto = 'Off'

    fringe_model = FringeModel()

    with create_server('fringe-cam') as publisher:
        while True:
            center = {}
            refl = {}
            png = {}

            camera_samples = []
            exposure = camera.ExposureTime

            image = None
            while True:
                capture_start = time.monotonic()
                sample = camera.get_array()
                capture_time = time.monotonic() - capture_start

                camera_samples.append(fit_image(sample))
                if image is None: image = sample

                # Clear buffer (force new acquisition)
                if capture_time > 20e-3: break

            # Track fringes
            fringe_model.update(image, exposure)
            center_x, center_y, cam_refl, saturation = [
                unweighted_mean(arr) for arr in np.array(camera_samples).T
            ]
            cam_refl *= 1500/exposure

            # Downsample if 16-bit
            if isinstance(image[0][0], np.uint16):
                image = (image/256 + 0.5).astype(np.uint8)

            # Save images
            png['raw'] = cv2.imencode('.png', image)[1].tobytes()
            png['fringe']  = cv2.imencode('.png', fringe_model.scaled_pattern)[1].tobytes()
            png['fringe-annotated']  = cv2.imencode('.png', fringe_model.annotated_pattern)[1].tobytes()

            # Store data
            center['x'] = deconstruct(center_x)
            center['y'] = deconstruct(center_y)
            center['saturation'] = deconstruct(saturation)
            center['exposure'] = exposure
            refl['cam'] = deconstruct(2 * cam_refl)
            refl['ai'] = deconstruct(fringe_model.reflection)

            # Auto-adjust exposure
            if saturation.n > 99: camera.ExposureTime = exposure // 2
            if saturation.n < 30: camera.ExposureTime = exposure * 2

            publisher.send({
                'center': center,
                'refl': refl,
                'png': png,
            })
