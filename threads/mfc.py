import time
from headers.zmq_server_socket import create_server
from headers.edm_util import deconstruct

from headers.mfc import MFC

def mfc_thread():
    mfc = MFC(31417)

    with create_server('mfc') as publisher:
        while True:
            publisher.send({
                'cell': deconstruct(mfc.flow_rate_cell),
                'neon': deconstruct(mfc.flow_rate_neon_line),
            })
            time.sleep(0.5)
