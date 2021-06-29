import time

import cv2
import numpy as np

from headers.zmq_client_socket import zmq_client_socket


## connect
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


start = time.monotonic()

while True:
    _, data = monitor_socket.blocking_read()
    frame = from_png(data['raw'])
    pattern = from_png(data['fringe-annotated'], color=True)

    frame = cv2.resize(frame, (720, 540))

    cv2.imshow('Camera', frame)
    cv2.imshow('Fringe Pattern', pattern)
    print(time.monotonic() - start)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
