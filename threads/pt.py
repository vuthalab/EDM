import time
from headers.pulse_tube import PulseTube
from headers.zmq_server_socket import create_server

def pt_thread():
    pt = PulseTube()

    with create_server('pt') as publisher:
        while True:
            ##### Read thermometers #####
            pt.status(silent=True)
            variables = {key: val[1] for key, val in pt.variables.items()}
            publisher.send({
                'running': pt.is_on(),
                **variables,
            })
            time.sleep(0.5)
