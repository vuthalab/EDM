import itertools

from pathlib import Path
from datetime import datetime
import time
import os

import cv2
import numpy as np

from headers.zmq_client_socket import connect_to
from headers.edm_util import add_timestamp

from PIL import Image, ImageFont, ImageDraw

# Select which cameras to log.
LOG_CAMERAS = [
    'webcam',
#    'fringe',
#    'cbs',
]


## connect
fringe_socket = connect_to('camera')
cbs_socket = connect_to('cbs-camera')
webcam_socket = connect_to('webcam')


def from_png(buff, color=False):
    png = np.frombuffer(buff, dtype=np.uint8)
    return cv2.imdecode(png, int(color))



SAVE_DIRECTORY = Path('~/Desktop/edm_data/camera_videos').expanduser()

for i in itertools.count():
    timestamp = datetime.now().strftime('%Y-%m-%d %H꞉%M꞉%S.%f')

    # Log fringe camera
    if 'fringe' in LOG_CAMERAS:
        _, data = fringe_socket.grab_json_data()
        if data is not None:
            frame = from_png(data['raw'])
            pattern_frame = from_png(data['fringe'])

            # Add timestamp to frames
            image = add_timestamp(frame)
            fringe_image = add_timestamp(pattern_frame)

            image.save(SAVE_DIRECTORY / 'log' / f'{timestamp}.png', optimize=True)
            fringe_image.save(SAVE_DIRECTORY / 'pattern_log' / f'{timestamp}.png', optimize=True)

            print(timestamp, 'fringe')

    # Log CBS camera
    if 'cbs' in LOG_CAMERAS:
        _, data = cbs_socket.grab_json_data()
        if data is not None:
            frame = from_png(data['image'], color=cv2.IMREAD_ANYDEPTH)

            # Amplify signal and convert
            frame = np.maximum(np.minimum((frame-500)//3, 255), 0).astype(np.uint8)
            image = add_timestamp(frame)
            image.save(SAVE_DIRECTORY / 'cbs' / f'{timestamp}.png', optimize=True)

            print(timestamp, 'cbs')

    # Log webcam
    if 'webcam' in LOG_CAMERAS:
        _, data = webcam_socket.blocking_read()
        if data is not None and data['index'] % 15 == 0:
            image = Image.fromarray(from_png(data['annotated'], color=True))
            image.save(SAVE_DIRECTORY / 'webcam' / f'{timestamp}.png', optimize=True)

            print(timestamp, 'webcam')

    time.sleep(1e-2)
