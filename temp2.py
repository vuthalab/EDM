import time

import cv2
import numpy as np

from headers.zmq_client_socket import zmq_client_socket


region_size = 500


## connect
connection_settings = {
    'ip_addr': 'localhost', # ip address
    'port': 5552, # camera publisher port
    'topic': 'camera', # device
}
monitor_socket = zmq_client_socket(connection_settings)
monitor_socket.make_connection()


start = time.monotonic()

while True:
    _, png = monitor_socket.blocking_read()
    png = np.frombuffer(png, dtype=np.uint8)
    frame = cv2.imdecode(png, cv2.IMREAD_GRAYSCALE)

    height, width = frame.shape
    total = np.sum(frame)
    center_x = np.sum(frame @ np.arange(width)) / total
    center_y = np.sum(frame.T @ np.arange(height)) / total

    region = frame[
        round(center_y-region_size/2) : round(center_y+region_size/2),
        round(center_x-region_size/2) : round(center_x+region_size/2)
    ]


    cv2.imshow('Camera', region)
    print(center_x, center_y, time.monotonic() - start)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
