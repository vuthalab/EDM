from pathlib import Path
from datetime import datetime
import time

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


SAVE_DIRECTORY = Path('~/Desktop/edm_data/camera_videos/log').expanduser()

font = ImageFont.truetype('headers/cmunrm.ttf', 24)

while True:
    _, png = monitor_socket.blocking_read()
    png = np.frombuffer(png, dtype=np.uint8)
    frame = cv2.imdecode(png, cv2.IMREAD_GRAYSCALE)
    image = Image.fromarray(frame)


    timestamp = datetime.now().strftime('%Y-%m-%d %H꞉%M꞉%S.%f')
    short_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    draw = ImageDraw.Draw(image)
    draw.text((8, 8), short_timestamp, fill=255, font=font)

    image.save(SAVE_DIRECTORY / f'{timestamp}.png')
    print(timestamp)
