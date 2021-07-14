import time

import cv2
import numpy as np

from simple_pyspin import Camera

from models.image_track import fit_image
from headers.zmq_client_socket import zmq_client_socket


# Select which cameras to show here.
SHOW_CAMERAS = {
    'webcam': True,
    'plume': False,
    'fringe': False,
    'cbs': False,
}


# Size of region around plume to show
plume_size = 200


print('Initializing cameras...')
if SHOW_CAMERAS['webcam']:
    webcam = cv2.VideoCapture(0)
    webcam.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1)
    webcam.set(cv2.CAP_PROP_EXPOSURE, 50)

if SHOW_CAMERAS['plume']:
    plume_camera = Camera(0)
    plume_camera.init()
    plume_camera.start()


## connect
print('Connecting to publisher...')
connection_settings = {
    'ip_addr': 'localhost', # ip address
    'port': 5552, # camera publisher port
    'topic': 'camera', # device
}
monitor_socket = zmq_client_socket(connection_settings)
monitor_socket.make_connection()

connection_settings = {
    'ip_addr': 'localhost', # ip address
    'port': 5555, # camera publisher port
    'topic': 'cbs-camera', # device
}
cbs_socket = zmq_client_socket(connection_settings)
cbs_socket.make_connection()


def from_png(buff, color=False):
    png = np.frombuffer(buff, dtype=np.uint8)
    return cv2.imdecode(png, int(color))


print('Starting.')
start = time.monotonic()
while True:
    timestamp = f'[{time.monotonic() - start:.3f}]'

    if SHOW_CAMERAS['fringe']:
        _, data = monitor_socket.grab_json_data()
        if data is not None:
            frame = from_png(data['raw'])
            pattern = from_png(data['fringe-annotated'], color=True)
            frame = cv2.resize(frame, (720, 540))

            cv2.imshow('Fringe Camera', frame)
            cv2.imshow('Fringe Pattern', pattern)

            print(timestamp, 'fringe')

    if SHOW_CAMERAS['cbs']:
        _, data = cbs_socket.grab_json_data()
        if data is not None:
            image = from_png(data['image'], color=cv2.IMREAD_ANYDEPTH)
            image = np.minimum(2 * image, 255).astype(np.uint8)
            cv2.imshow('Coherent Backscatter', image)

            print(timestamp, 'cbs')

    if SHOW_CAMERAS['webcam']:
        ret, saph_image = webcam.read()
        cv2.imshow('Sapphire Webcam', saph_image[::-1, ::-1, :])

        print(timestamp, 'webcam')


    if SHOW_CAMERAS['plume']:
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
        cv2.imshow('Plume', plume_image)

        print(timestamp, 'plume')


    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

    time.sleep(1e-2)

fringe_camera.release()

if SHOW_CAMERAS['plume']:
    plume_camera.stop()
    plume_camera.close()

cv2.destroyAllWindows()
