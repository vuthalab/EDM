import numpy as np
import matplotlib.pyplot as plt

import cv2

from colorama import Style

from headers.zmq_client_socket import zmq_client_socket

from headers.util import nom, std, plot, uarray


N_SAMPLES = 100 # number of samples to calibrate with.

connection_settings = {
    'ip_addr': 'localhost', # ip address
    'port': 5555, # our open port
    'topic': 'cbs-camera', # device
}


# connect to publisher
monitor_socket = zmq_client_socket(connection_settings)
monitor_socket.make_connection()

samples = []
for i in range(N_SAMPLES):
    _, data = monitor_socket.blocking_read()

    data = np.frombuffer(data['raw'], dtype=np.uint8)
    image = cv2.imdecode(data, cv2.IMREAD_ANYDEPTH).astype(int)
    print(f'\rSample {Style.BRIGHT}{i+1}/{N_SAMPLES}{Style.RESET_ALL} | Min: {image.min()} | Max: {image.max()}', end='')
    samples.append(image)
monitor_socket.socket.close()
print()

result = ((sum(samples) + N_SAMPLES//2) / N_SAMPLES).astype(np.uint16)
cv2.imwrite('calibration/cbs-background.png', result)
print(result.min(), result.max(), result.mean())

plt.imshow(result)
plt.show()
