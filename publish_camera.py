import time

from simple_pyspin import Camera

from headers.zmq_server_socket import zmq_server_socket



CAPTURE_INTERVAL = 1/1.4 # seconds. Chosen to match pulsetube frequency

with zmq_server_socket(5552, 'camera') as publisher:
    with Camera() as cam:
        cam.start()

        try:
            while True:
                start = time.monotonic()

                image = cam.get_array()

                print('Captured frame')
                publisher.send(image)

                dt = time.monotonic() - start
                time.sleep(max(0, CAPTURE_INTERVAL - dt))
        finally:
            cam.stop()
