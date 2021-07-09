import time

import cv2
import numpy as np

from simple_pyspin import Camera

from models.image_track import fit_image
from headers.zmq_client_socket import zmq_client_socket

plume_size = 200


print('Initializing cameras...')
webcam = cv2.VideoCapture(0)
webcam.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1)
webcam.set(cv2.CAP_PROP_EXPOSURE, 50)

plume_camera = Camera(0)
plume_camera.init()


## connect
print('Connecting to publisher...')
connection_settings = {
    'ip_addr': 'localhost', # ip address
    'port': 5552, # camera publisher port
    'topic': 'camera', # device
}
monitor_socket = zmq_client_socket(connection_settings)
monitor_socket.make_connection()


def from_png(buff, color=False):
    png = np.frombuffer(buff, dtype=np.uint8)
    return cv2.imdecode(png, int(color))


print('Starting.')
plume_camera.start()
start = time.monotonic()
while True:
    try:
        _, data = monitor_socket._decode(monitor_socket.grab_data())
        frame = from_png(data['raw'])
        pattern = from_png(data['fringe-annotated'], color=True)
        frame = cv2.resize(frame, (720, 540))

        cv2.imshow('Fringe Camera', frame)
        cv2.imshow('Fringe Pattern', pattern)
    except:
        pass

    ret, saph_image = webcam.read()
    plume_image = plume_camera.get_array()

    # Extract plume location
    cx, cy, intensity, _ = fit_image(plume_image)
    height, width = plume_image.shape
    cx = round(cx.n * width / 100)
    cy = round(cy.n * height / 100)
    plume_image = plume_image[
        max(cy-plume_size, 0) : cy+plume_size,
        max(cx-plume_size, 0) : cx+plume_size
    ]

    cv2.imshow('Sapphire Webcam', saph_image[::-1, ::-1, :])
    cv2.imshow('Plume', plume_image)
    print(time.monotonic() - start)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

plume_camera.stop()
fringe_camera.release()
plume_camera.close()
cv2.destroyAllWindows()
