import time
from headers.zmq_server_socket import create_server
from headers.edm_util import deconstruct

from headers.FRG730 import FRG730


def pressure_thread():
    pressure_gauge = FRG730()

    with create_server('pressure') as publisher:
        while True:
            chamber_pressure = pressure_gauge.pressure

            # Reconnect if dead
            if chamber_pressure is None:
                pressure_gauge.close()
                pressure_gauge = FRG730()
                continue

            publisher.send({'pressure': deconstruct(chamber_pressure)})
            time.sleep(0.5)
