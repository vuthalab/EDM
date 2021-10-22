import time
from headers.zmq_server_socket import create_server
from headers.edm_util import deconstruct

from headers.EI1050 import EI1050, get_absolute_humidity


def ei1050_thread():
    probe = EI1050()

    with create_server('ei1050') as publisher:
        while True:
            T = probe.temperature
            RH = probe.relative_humidity

            humidity = get_absolute_humidity(T, RH)

            publisher.send({
                'temperature': deconstruct(T),
                'relative_humidity': deconstruct(RH),
                'absolute_humidity': deconstruct(humidity),
            })
            time.sleep(0.2)
