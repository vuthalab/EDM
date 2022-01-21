import time
from colorama import Fore, Style

from headers.zmq_client_socket import connect_to
from headers.zmq_server_socket import create_server
from headers.verdi import Verdi

def interlock_thread():
    temp_monitor = connect_to('verdi')
    verdi = Verdi()

    start_time = time.monotonic()
    with create_server('interlock') as publisher:
        while True:
            _, data = temp_monitor.grab_json_data()
            if data is not None:
                verdi_temp = data['status']['temp']['baseplate']
                power = data['status']['power']

                if verdi_temp > 34 and power > 2:
                    verdi.power = 1
                    print(f'{Fore.RED}##### VERDI INTERLOCK TRIPPED! #####{Style.RESET_ALL}')

            # Keepalive Indicator
            publisher.send({'timestamp': time.time(), 'uptime': (time.monotonic() - start_time)/3600})
            time.sleep(0.1)
