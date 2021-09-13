
import time
from headers.zmq_server_socket import create_server
from headers.edm_util import deconstruct

from headers.verdi import Verdi
from headers.rigol_dp832 import LaserSign

def verdi_thread():
    verdi = Verdi()
#    laser_sign = LaserSign()

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
#                'sign': laser_sign.enabled,
                'verdi': verdi.is_on or status['power'] > 0,
            }

            # Laser sign interlock
#            if running['sign'] != running['verdi']:
#                if running['sign']:
#                    # Possibly check YAG here too?
#                    laser_sign.off()
#                else:
#                    laser_sign.on()

            publisher.send({
                'running': running,
                'status': status,
            })
            time.sleep(0.5)
