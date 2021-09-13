import time
import itertools
import threading
import psutil
import traceback

from colorama import Fore, Style
from uncertainties import ufloat

from headers.zmq_server_socket import create_server
from headers.zmq_client_socket import connect_to

from headers.edm_util import deconstruct, print_tree, memory_usage

from headers.rigol_ds1102e import RigolDS1102e

from models.fringe_counter import FringeCounter
from models.growth_rate import GrowthModel

from threads.spectrometer import spectrometer_thread
from threads.webcam import webcam_thread
from threads.wavemeter import wavemeter_thread
from threads.camera import camera_thread
from threads.pressure import pressure_thread
from threads.turbo import turbo_thread
from threads.ctc import ctc_thread
from threads.pt import pt_thread
from threads.mfc import mfc_thread 
from threads.verdi import verdi_thread 



PUBLISH_INTERVAL = 2/1.4 # publish every x seconds.
LABJACK_SCOPE = '/dev/fluorescence_scope'


##### UTILITY FUNCTIONS #####
fringe_counter = FringeCounter()
growth_model = GrowthModel()


THREADS = {
    'spectrometer': spectrometer_thread,
    'wavemeter': wavemeter_thread,
    'fringe-cam': camera_thread,
    'pressure': pressure_thread,
    'turbo': turbo_thread,
    'ctc': ctc_thread,
    'pt': pt_thread,
    'mfc': mfc_thread,
    'verdi': verdi_thread,
}


##### MAIN PUBLISHER #####
def run_publisher():
    print('Initializing devices...')

    monitors = {
        key: connect_to(key)
        for key in THREADS.keys()
    }


    print('Starting publisher')
    publisher_start = time.monotonic()
    with create_server('edm-monitor') as publisher:
        for loop_iteration in itertools.count(1):
            raw_data = {}
            for key, monitor in monitors.items():
                while True:
                    _, thread_data = monitor.grab_json_data()
                    if thread_data is None: break
                    raw_data[key] = thread_data

            thread_up = {
                key: (key in raw_data)
                for key in THREADS.keys()
            }

            # Extract all relevant data
            data = {}
            data['thread-up'] = thread_up
            data['running'] = {}

            if thread_up['ctc']:
                data['temperatures'] = raw_data['ctc']['temperatures']
                data['heaters'] = raw_data['ctc']['heaters']
            else:
                data['temperatures'] = {}

            if thread_up['spectrometer']:
                data['rough'] = raw_data['spectrometer']['rough']
                data['trans'] = raw_data['spectrometer']['trans']
                data['rough']['hdr-chisq'] = raw_data['spectrometer']['fit']['chisq']

            if thread_up['wavemeter']:
                data['freq'] = raw_data['wavemeter']['freq']
                data['intensities'] = raw_data['wavemeter']['power']
                data['temperatures']['wavemeter'] = raw_data['wavemeter']['temp']

            if thread_up['pressure']:
                data['pressure'] = raw_data['pressure']['pressure']

            if thread_up['mfc']:
                data['flows'] = raw_data['mfc']

            if thread_up['turbo']:
                data['running']['turbo'] = raw_data['turbo']['running']
                data['turbo'] = raw_data['turbo']

            if thread_up['pt']:
                data['pt'] = raw_data['pt']
                data['running']['pt'] = raw_data['pt']['running']

            if thread_up['fringe-cam']:
                data['refl'] = raw_data['fringe-cam']['refl']
                data['center'] = raw_data['fringe-cam']['center']

            if thread_up['verdi']:
                data['verdi'] = raw_data['verdi']['status']
                data['running'] = {**data['running'], **raw_data['verdi']['running']}
                data['temperatures']['verdi'] = data['verdi']['temp']


            # Update models
            if thread_up['ctc'] and thread_up['mfc'] and thread_up['fringe-cam']:
                saph_temp = data['temperatures']['saph']
                growth_model.update(
                    ufloat(*data['flows']['neon']),
                    ufloat(*data['flows']['cell']),
                    saph_temp
                )
                fringe_counter.update(
                    data['refl']['ai'][0],
                    grow=(growth_model._growth_rate.n > 0)
                )
                if saph_temp > 13: fringe_counter.reset()

                data['height'] = deconstruct(growth_model.height),
                data['fringe'] = {
                    'count': fringe_counter.fringe_count,
                    'ampl': fringe_counter.amplitude,
                }


            # Add debug info
            uptime = (time.monotonic() - publisher_start)/3600
            data['debug'] = {
                'uptime': uptime if loop_iteration > 1 else None,
                'memory': memory_usage(),
                'system-memory': round(psutil.virtual_memory().used / 1024),
                'cpu': psutil.cpu_percent(),
            }
#            print_tree(data)
#            print()



            ### Limit publishing speed ###
            target_end = PUBLISH_INTERVAL * loop_iteration + publisher_start
            time.sleep(max(target_end - time.monotonic(), 0))

            publisher.send(data)



def wrap_thread(name, thread_func):
    delay = 5

    # Exponential backoff retry
    while True:
        print(f'Starting {Style.BRIGHT}{key}{Style.RESET_ALL} thread')
        try:
            thread_func()
        except:
            print(f'{Fore.RED}{name} thread crashed!{Style.RESET_ALL} Retrying after {delay} seconds...')
            traceback.print_exc()

            time.sleep(delay)
            delay *= 2



if __name__ == '__main__':
    threads = {}
    for key, thread_func in THREADS.items():
        thread = threading.Thread(target=lambda: wrap_thread(key, thread_func))
        thread.start()
        threads[key] = thread

    run_publisher()

    # Quit all threads gracefully
    for thread in threads.values(): thread.join()
