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


def from_png(buff):
    png = np.frombuffer(buff, dtype=np.uint8)
    return cv2.imdecode(png, cv2.IMREAD_GRAYSCALE)


SAVE_DIRECTORY = Path('~/Desktop/edm_data/camera_videos').expanduser()
font = ImageFont.truetype('headers/cmunrm.ttf', 24)

while True:
    _, data = monitor_socket.blocking_read()
    frame = from_png(data['raw'])
    pattern_frame = from_png(data['fringe'])

    timestamp = datetime.now().strftime('%Y-%m-%d %H꞉%M꞉%S.%f')
    short_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

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
    print(timestamp)
