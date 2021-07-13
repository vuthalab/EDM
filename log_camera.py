from pathlib import Path
from datetime import datetime
import time
import os

import cv2
import numpy as np

from headers.zmq_client_socket import zmq_client_socket

from PIL import Image, ImageFont, ImageDraw


## connect
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
    return cv2.imdecode(png, color)


SAVE_DIRECTORY = Path('~/Desktop/edm_data/camera_videos').expanduser()
font = ImageFont.truetype('headers/cmunrm.ttf', 24)

while True:
    timestamp = datetime.now().strftime('%Y-%m-%d %H꞉%M꞉%S.%f')
    short_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Log fringe camera
    if False:
        _, data = monitor_socket.blocking_read()
        frame = from_png(data['raw'])
        pattern_frame = from_png(data['fringe'])

        # Add timestamp to frame
        image = Image.fromarray(frame)
        draw = ImageDraw.Draw(image)
        draw.text((8, 8), short_timestamp, fill=255, font=font)

        # Add timestamp to fringe frame
        pattern_frame = np.pad(pattern_frame, [(32, 0), (0, 0)])
        fringe_image = Image.fromarray(pattern_frame)
        draw = ImageDraw.Draw(fringe_image)
        draw.text((8, 4), short_timestamp, fill=255, font=font)


        image.save(SAVE_DIRECTORY / 'log' / f'{timestamp}.png', optimize=True)
        fringe_image.save(SAVE_DIRECTORY / 'pattern_log' / f'{timestamp}.png', optimize=True)

    # Log CBS camera
    if True:
        _, data = cbs_socket.blocking_read()
        frame = from_png(data['image'], color=cv2.IMREAD_ANYDEPTH)

        # Amplify signal and convert
        frame = np.minimum(2 * frame, 255).astype(np.uint8)

        # Add timestamp to fringe frame
        frame = np.pad(frame, [(32, 0), (0, 0)])
        image = Image.fromarray(frame)
        draw = ImageDraw.Draw(image)
        draw.text((8, 4), short_timestamp, fill=255, font=font)

        image.save(SAVE_DIRECTORY / 'cbs' / f'{timestamp}.png', optimize=True)

    print(timestamp)
