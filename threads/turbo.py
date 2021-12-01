import time
from headers.zmq_server_socket import create_server

from headers.turbo import TurboPump


def turbo_thread():
    turbo = TurboPump()

    with create_server('turbo') as publisher:
        while True:
            status = turbo.operation_status
            publisher.send({
                'status': status,
                'frequency': turbo.speed,
                'current': turbo.current,
                'running': (status == 'normal'),
            })
            time.sleep(0.5)
