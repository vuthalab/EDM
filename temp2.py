import time, sys, itertools
import zmq

import numpy as np
import matplotlib.pyplot as plt
import cv2

from headers.ti_saph import TiSapphire
from headers.wavemeter import WM

from headers.zmq_client_socket import connect_to
from headers.util import plot, fit, nom


zmq_context = zmq.Context()
sock = zmq_context.socket(zmq.SUB)
sock.connect('tcp://192.168.0.106:31415')
sock.setsockopt(zmq.SUBSCRIBE, b'')

while True:
    print(sock.recv_json())
