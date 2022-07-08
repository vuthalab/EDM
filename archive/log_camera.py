import itertools

from pathlib import Path
from datetime import datetime
import time
import os, sys
import subprocess

import cv2
import numpy as np

from headers.zmq_client_socket import connect_to
from headers.edm_util import add_timestamp

from PIL import Image, ImageFont, ImageDraw


if len(sys.argv) > 1:
    DURATION = float(sys.argv[1])
    print(f'Collecting data for {DURATION:.1f} hours.')
else:
    DURATION = None
    print('Collecting data indefinitely.')



# Select which cameras to log.
LOG_CAMERAS = [
    'webcam',
#    'fringe',
#    'cbs',
]


## connect
if 'fringe' in LOG_CAMERAS: fringe_socket = connect_to('camera')
if 'cbs' in LOG_CAMERAS: cbs_socket = connect_to('cbs-camera')
if 'webcam' in LOG_CAMERAS: webcam_socket = connect_to('webcam')


def from_png(buff, color=False):
    png = np.frombuffer(buff, dtype=np.uint8)
    return cv2.imdecode(png, int(color))



SAVE_DIRECTORY = Path('~/Desktop/edm_data/camera_videos').expanduser()

start_time = time.monotonic()
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
        if data is not None: # and data['index'] % 2 == 0:
            image = Image.fromarray(from_png(data['annotated'], color=True)[:,:,::-1])

            save_file = SAVE_DIRECTORY / 'webcam' / f'{timestamp}.png'
            image.save(save_file, optimize=True)

            if data['index'] % 300 == 0:
                subprocess.run(f'scp "{save_file}" celine@143.110.210.120:~/server/webcam.png', shell=True)

            print(timestamp, 'webcam')


    if DURATION is not None and time.monotonic() - start_time > DURATION * 3600:
        break
    time.sleep(0.1)
