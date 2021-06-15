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


start = time.monotonic()

while True:
    _, png = monitor_socket.blocking_read()
    png = np.frombuffer(png, dtype=np.uint8)
    frame = cv2.imdecode(png, cv2.IMREAD_GRAYSCALE)

    frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)

    cv2.imshow('Camera', frame)
    print(time.monotonic() - start)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
