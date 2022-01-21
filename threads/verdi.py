import time
from headers.zmq_server_socket import create_server
from headers.edm_util import deconstruct

from headers.verdi import Verdi

def verdi_thread():
    verdi = Verdi()

    with create_server('verdi') as publisher:
        while True:
            status = {
                'current': verdi.current,
                'power': verdi.power,
                'temp': {
                    'baseplate': verdi.baseplate_temp,
                    'vanadate': verdi.vanadate_temp,
                },
            }
            running = {
                'verdi': verdi.is_on or status['power'] > 0,
            }

            publisher.send({
                'running': running,
                'status': status,
            })
            time.sleep(1.2)
