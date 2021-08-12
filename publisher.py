import time, pprint, traceback
import itertools
import resource, psutil
import threading

import asyncio
from colorama import Fore, Style

import cv2
import numpy as np

from uncertainties import ufloat
from simple_pyspin import Camera

#Import class objects
from headers.zmq_server_socket import create_server
from headers.zmq_client_socket import connect_to

from headers.FRG730 import FRG730
from headers.CTC100 import CTC100
from headers.labjack_device import Labjack
from headers.mfc import MFC
from headers.turbo import TurboPump
from headers.ximea_camera import Ximea
from headers.verdi import Verdi
from headers.rigol_dp832 import LaserSign
from pulsetube_compressor import PulseTube

from headers.util import display, unweighted_mean, nom, std
from headers.edm_util import deconstruct, Timer, print_tree
from headers.notify import send_email

from models.fringe import FringeModel
from models.fringe_counter import FringeCounter
from models.image_track import fit_image
from models.growth_rate import GrowthModel
from models.cbs import fit_cbs

from threads.spectrometer import spectrometer_thread
from threads.webcam import webcam_thread
from threads.wavemeter import wavemeter_thread



PUBLISH_INTERVAL = 2/1.4 # publish every x seconds.



##### UTILITY FUNCTIONS #####
fringe_model = FringeModel()
fringe_counter = FringeCounter()
growth_model = GrowthModel()

def memory_usage():
    """Get the current memory usage, in KB."""
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss



##### MAIN PUBLISHER #####
async def run_publisher():
    print('Initializing devices...')
    pressure_gauge = FRG730()
    thermometers = [
        (CTC100(31415), ['saph', 'coll', 'bott hs', 'cell'], ['heat saph', 'heat coll']),
        (CTC100(31416), ['srb4k', 'srb45k', '45k plate', '4k plate'], ['srb45k out', 'srb4k out'])
    ]
    labjack = Labjack('470022275')
    mfc = MFC(31417)
    pt = PulseTube()

#    camera = Camera(1)
    camera = None
    if camera is not None:
        camera.init()
        try:
            camera.start()
        except:
            pass
        camera.GainAuto = 'Off'
        camera.Gain = 10
        camera.ExposureAuto = 'Off'
        camera_publisher = create_server('camera')

    turbo = TurboPump()

    verdi = Verdi()
    laser_sign = LaserSign()


    pt_last_off = time.monotonic()
    heaters_last_safe = time.monotonic()


    try:
        cbs_cam = Ximea(exposure=1e6)
        cbs_cam.set_roi(500, 500, 700, 700)
    except:
        cbs_cam = None
        print(f'{Fore.RED}ERROR: Ximea camera is unplugged!{Style.RESET_ALL}')
    cbs_publisher = create_server('cbs-camera')

    spectrometer_monitor = connect_to('spectrometer')
    wavemeter_monitor = connect_to('wavemeter')


    print('Starting publisher')
    publisher_start = time.monotonic()
    loop = asyncio.get_running_loop()
    run_async = lambda f: loop.run_in_executor(None, f)
    try:
        with create_server('edm-monitor') as publisher:
            rough = {}
            trans = {}

            for loop_iteration in itertools.count(1):
                loop_start = time.monotonic()
                async_getters = []

                times = {}

                ##### Read pressure gauge (Async) #####
                chamber_pressure = None
                def pressure_getter():
                    nonlocal chamber_pressure, times
                    with Timer('pressure', times):
                        chamber_pressure = pressure_gauge.pressure
                async_getters.append(run_async(pressure_getter))


                ##### Read CTC100 Temperatures + Heaters (Async) #####
                temperatures = {}
                heaters = {}
                async def CTC_getter(thermometer):
                    """Record data from the given thermometer."""
                    obj, temp_channels, heater_channels = thermometer

                    with Timer(f'CTC{obj._address[1]}', times):
                        for channel in temp_channels:
                            temperatures[channel] = await obj.async_read(channel)

                        for channel in heater_channels:
                            heaters[channel] = await obj.async_read(channel)

                async_getters.extend([
                    CTC_getter(thermometer) for thermometer in thermometers
                ])



                ##### Read MFC Flows (Async) #####
                flows = {}
                async def flow_getter():
                    """Record the flow rates from the MFC."""
                    with Timer('MFC', times):
                        flows['cell'] = deconstruct(await mfc.async_get_flow_rate_cell())
                        flows['neon'] = deconstruct(await mfc.async_get_flow_rate_neon_line())
                async_getters.append(flow_getter())



                ##### Read Camera (Async) #####
                center =  {}
                refl = {}
                png = {}
                def camera_getter():
                    camera_samples = []

                    with Timer('camera', times):
                        exposure = camera.ExposureTime

                        image = None
                        while True:
                            capture_start = time.monotonic()
                            sample = camera.get_array()
                            capture_time = time.monotonic() - capture_start

                            camera_samples.append(fit_image(sample))
                            if image is None: image = sample

                            # Clear buffer (force new acquisition)
                            if capture_time > 20e-3: break

                        # Track fringes
                        fringe_model.update(image, exposure)
                        center_x, center_y, cam_refl, saturation = [
                            unweighted_mean(arr) for arr in np.array(camera_samples).T
                        ]
                        cam_refl *= 1500/exposure

                        # Downsample if 16-bit
                        if isinstance(image[0][0], np.uint16):
                            image = (image/256 + 0.5).astype(np.uint8)

                        # Save images
                        png['raw'] = cv2.imencode('.png', image)[1].tobytes()
                        png['fringe']  = cv2.imencode('.png', fringe_model.scaled_pattern)[1].tobytes()
                        png['fringe-annotated']  = cv2.imencode('.png', fringe_model.annotated_pattern)[1].tobytes()

                    # Store data
                    center['x'] = deconstruct(center_x)
                    center['y'] = deconstruct(center_y)
                    center['saturation'] = deconstruct(saturation)
                    center['exposure'] = exposure
                    refl['cam'] = deconstruct(2 * cam_refl)
                    refl['ai'] = deconstruct(fringe_model.reflection)

                    if saturation.n > 99: camera.ExposureTime = exposure // 2
                    if saturation.n < 30: camera.ExposureTime = exposure * 2
                if camera is not None:
                    async_getters.append(run_async(camera_getter))


                ##### Read turbo status (Async) #####
                pt_on = pt.is_on()
                running = {'pt': pt_on}
                async def turbo_getter():
                    """Record the operational status of the turbo pump."""
                    with Timer('turbo', times):
                        status = await turbo.async_operation_status()
                        running['turbo'] = (status == 'normal')
                async_getters.append(turbo_getter())



                ##### Read labjack (Async) #####
                intensities = {}
                def labjack_getter():
                    with Timer('labjack', times):
                        intensities['broadband'] = deconstruct(labjack.read('AIN0'))
#                        intensities['hene'] = deconstruct(labjack.read('AIN1'))
                        intensities['LED'] = deconstruct(labjack.read('AIN2'))
                async_getters.append(run_async(labjack_getter))


                ##### Read Verdi status (Async) #####
                verdi_status = {}
                def verdi_getter():
                    with Timer('verdi', times):
                        running['verdi'] = verdi.is_on
                        verdi_status['current'] = verdi.current
                        verdi_status['power'] = verdi.power
                        verdi_status['temp'] = {
                            'baseplate': verdi.baseplate_temp,
                            'vanadate': verdi.vanadate_temp,
                        }
                async_getters.append(run_async(verdi_getter))

                ##### Read laser sign (Async) #####
                def laser_sign_getter():
                    with Timer('verdi', times):
                        running['sign'] = laser_sign.enabled
                async_getters.append(run_async(laser_sign_getter))



                # Await all async data getters.
                # Tasks will run simultaneously.
                gather_task = asyncio.gather(*async_getters)
                try:
                    await asyncio.wait_for(gather_task, timeout=15)
                except:
                    raise ValueError(gather_task.exception())


                ##### Read CBS camera (Sync) #####
                cbs_png = None
                cbs_info = {'data': None, 'fit': None}

                with Timer('CBS Camera', times):
                    if cbs_cam is not None and cbs_cam.capture():
                        cbs_png = cv2.imencode('.png', cbs_cam.image)[1].tobytes()

                    try:
                        r, I, (peak, width, background), chisq = fit_cbs(cbs_cam.image)

                        cbs_info['data'] = {
                            'radius': list(r),
                            'intensity': {
                                'nom': list(nom(I)),
                                'std': list(std(I)),
                            }
                        }

                        if max(width.s, peak.s) > 100 or min(width.n, peak.n) < 0:
                            raise ValueError

                        cbs_info['fit'] = {
                            'peak': deconstruct(peak),
                            'width': deconstruct(width),
                            'background': deconstruct(background),
                            'chisq': chisq,
                        }
                    except:
                        pass

                
                # Read spectrometer thread.
                _, spec_data = spectrometer_monitor.grab_json_data()
                if spec_data is not None:
                    rough = spec_data['rough']
                    trans = spec_data['trans']
                    rough['hdr-chisq'] = spec_data['fit']['chisq']

                # Read wavemeter thread.
                frequencies = {}
                while True:
                    _, new_data = wavemeter_monitor.grab_json_data()
                    if new_data is None: break
                    frequencies = new_data['freq']
                    intensities = {**intensities, **new_data['power']}
                    temperatures['wavemeter'] = new_data['temp']


                ### Update models ###
                saph_temp = temperatures['saph']

                growth_model.update(ufloat(*flows['neon']), ufloat(*flows['cell']), saph_temp)
                if camera is not None:
                    fringe_counter.update(
                        refl['ai'][0],
                        grow=(growth_model._growth_rate.n > 0)
                    )

                if saph_temp > 13: fringe_counter.reset()


                # Construct final data packet
                times['loop'] = round(1e3 * (time.monotonic() - loop_start))
                uptime = (time.monotonic() - publisher_start)/3600

                data_dict = {
                    'pressure': deconstruct(chamber_pressure),

                    'flows': flows,

                    'temperatures': temperatures,
                    'heaters': heaters,

                    'center': center,
                    'cbs': cbs_info['fit'],

                    'rough': rough,
                    'trans': trans,
                    'refl': refl,
                    'fringe': {
                        'count': fringe_counter.fringe_count,
                        'ampl': fringe_counter.amplitude,
                    },

                    'model': {
                        'height': deconstruct(growth_model.height),
                    },

                    'freq': frequencies,
                    'intensities': intensities,
                    
                    'running': running,
                    'debug': {
                        'times': times,
                        'uptime': uptime if loop_iteration > 1 else None,
                        'memory': memory_usage(),
                        'system-memory': round(psutil.virtual_memory().used / 1024),
                        'cpu': psutil.cpu_percent(),
                        'verdi': verdi_status,
                    }
                }
                print_tree(data_dict)



                ### Limit publishing speed ###
                target_end = PUBLISH_INTERVAL * loop_iteration + publisher_start
                time.sleep(max(target_end - time.monotonic(), 0))

                publisher.send(data_dict)

                if camera is not None:
                    camera_publisher.send(png)

                if cbs_png is not None:
                    cbs_publisher.send({
                        'image': cbs_png,
                        **cbs_info,
                    })
                print()
                print()


                # Restart if pressure gauge cuts out
                if data_dict['pressure'] is None:
                    pressure_gauge.close()
                    pressure_gauge = FRG730()


                # Laser sign interlocks
                verdi_on = running['verdi'] or verdi_status['power'] > 0
                yag_on = False
                proper_sign_status = verdi_on or yag_on
                if proper_sign_status != running['sign']:
                    if proper_sign_status:
                        laser_sign.on()
                    else:
                        laser_sign.off()

    finally:
        print(f'{Fore.RED}{Style.BRIGHT}Crashed, cleaning up...{Style.RESET_ALL}')
        tb = traceback.format_exc()
        print(tb)

        if camera is not None:
            print('Stopping fringe camera...')
            camera.stop()
            camera.close()
            camera_publisher.close()

        print('Stopping CBS camera...')
        cbs_cam.close()
        cbs_publisher.close()

        print('Stopping miscellaneous equipment...')
        pressure_gauge.close()
        mfc.close()
        turbo.close()

        print('Done.')






if __name__ == '__main__':
    thread_functions = [
        spectrometer_thread,
        webcam_thread,
        wavemeter_thread,
    ]

    threads = [threading.Thread(target=function) for function in thread_functions]
    for thread in threads: thread.start()

    while True:
        try:
            asyncio.run(run_publisher())
        except:
            # Occasionally force process restart
            if memory_usage() > 3e6:
                break

            # Check if this was intentional
            tb = traceback.format_exc()
            print(tb)
            if 'KeyboardInterrupt' in tb: break

            # Log error and send email
            print(f'{Fore.RED}===== PUBLISHER CRASHED ====={Style.RESET_ALL}')
            with open('publisher-error-log.txt', 'a') as f:
                print(time.asctime(time.localtime()), tb, file=f)
#            send_email('Publisher Crashed', tb, high_priority=False)

        time.sleep(3)
