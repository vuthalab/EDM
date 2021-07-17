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
from headers.wavemeter import WM
from headers.turbo import TurboPump
from headers.ximea_camera import Ximea
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



PUBLISH_INTERVAL = 2/1.4 # publish every x seconds.



##### UTILITY FUNCTIONS #####
async def with_uncertainty(getter, N=32, delay=5e-3):
    """Call the given getter function N times and return the mean and standard deviation."""
    values = []
    for i in range(N):
        value = getter()
        if not isinstance(value, float): return None

        values.append(value)
        await asyncio.sleep(delay)

    return (np.mean(values), np.std(values))


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
    wm = WM(publish=False) #wavemeter class used for reading frequencies from high finesse wavemeter
    pt = PulseTube()

    camera = Camera(1)
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


    print('Starting publisher')
    publisher_start = time.monotonic()
    loop = asyncio.get_running_loop()
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
                async_getters.append(loop.run_in_executor(None, pressure_getter))


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



                ##### Read wavemeter frequencies (Async) #####
                frequencies = {}
                async def frequency_getter():
                    """Record the frequencies from the wavemeter."""
                    with Timer('wavemeter', times):
                        frequencies['baf'] = await with_uncertainty(lambda: wm.read_frequency(8))
                        frequencies['calcium'] = await with_uncertainty(lambda: wm.read_frequency(6))
                async_getters.append(frequency_getter())



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

                async_getters.append(loop.run_in_executor(None, camera_getter))


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
                async_getters.append(loop.run_in_executor(None, labjack_getter))


                # Await all async data getters.
                # Tasks will run simultaneously.
                gather_task = asyncio.gather(*async_getters)
                try:
                    await asyncio.wait_for(gather_task, timeout=15)
                except:
                    raise ValueError(gather_task.exception())


                ##### Read CBS camera (Sync) #####
                cbs_png = None
                cbs_raw_png = None
                cbs_info = {'data': None, 'fit': None}

                with Timer('CBS Camera', times):
                    if cbs_cam is not None and cbs_cam.capture():
                        cbs_png = cv2.imencode('.png', cbs_cam.image)[1].tobytes()
                        cbs_raw_png = cv2.imencode('.png', cbs_cam.raw_image)[1].tobytes()

                    try:
#                        r, I, (peak, width, background), chisq = fit_cbs(cbs_cam.image)
                        r, I, (peak, width, background), chisq = fit_cbs(cbs_cam.raw_image)
                        if width.s > 100: raise ValueError

                        cbs_info['data'] = {
                            'radius': list(r),
                            'intensity': {
                                'nom': list(nom(I)),
                                'std': list(std(I)),
                            }
                        }
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



                ### Update models ###
                saph_temp = temperatures['saph']

                growth_model.update(ufloat(*flows['neon']), ufloat(*flows['cell']), saph_temp)
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
                    }
                }
                print_tree(data_dict)









                ###### Software Interlocks #####
                if data_dict['pressure'] is None:
                    raise ValueError('Pressure gauge read failed, restarting.')

                cold_temps = {
                    name: temperatures[name] for name in ['srb4k', 'saph', '4k plate', 'coll']
                    if temperatures[name] is not None
                }
                min_temp = min(cold_temps.values())

                turbo_on = data_dict['running']['turbo']

                # Determine whether pt has been running for 24 hrs
                if not pt_on: pt_last_off = time.monotonic()
                pt_running = (time.monotonic() - pt_last_off) > 24*60*60

                # Determine whether heaters are safe and working (all <20W, or temps >10K).
                # Will send a notification if unsafe for too long.
                heaters_safe = (
                    all(power is None or power < 20 for power in heaters.values())
                    or all(temp > 10 for temp in cold_temps.values())
                )
                if heaters_safe: heaters_last_safe = time.monotonic()


                print(f'{pt_on=} {pt_running=} {heaters_safe=} {min_temp=}')


                if chamber_pressure is not None:
                    # Chamber pressure high during main experiment
                    if chamber_pressure.n > 0.2 and pt_running and turbo_on:
                        for thermometer, _, _ in thermometers:
                            thermometer.disable_output()
                        mfc.off()

                        send_email(
                            'Pressure Interlock Activated',
                            f'Vacuum chamber pressure reached {chamber_pressure:.3f} torr while pulsetube is running! MFC and heaters disabled.'
                        )

                    # Chamber pressurized while turbo on
                    if chamber_pressure.n > 1 and turbo_on:
                        send_email(
                            'Pressure Warning',
                            f'Vacuum chamber pressure is abnormally high ({chamber_pressure:.3f} torr) while turbo is on.'
                        )
                        if not pt_running:
                            turbo.off()

                # Pulsetube running for last 24 hours, yet temperatures abnormally high
                if pt_running and any(temp > 30 for temp in cold_temps.values()):
                    name, temp = max(cold_temps.items(), key=lambda _, temp: temp)
                    send_email(
                        'Temperature Warning',
                        f'Pulsetube has been running for the past 24 hours, yet {name} temperature is abnormally high ({temp:.1f} K).'
                    )


                # Heaters running on full blast, yet surfaces are cold
                if (time.monotonic() - heaters_last_safe) > 20 * 60:
                    strongest_heater = max(heaters.keys(), key=lambda name: heaters[name] or 0)
                    max_power = heaters[strongest_heater]

                    send_email(
                        'Heater Warning',
                        f'{strongest_heater} has been outputting {max_power:.2f} W for 20 minutes, yet coldest temperature is {min_temp:.1f} K. Did the heater fall off?'
                    )



                ### Limit publishing speed ###
                target_end = PUBLISH_INTERVAL * loop_iteration + publisher_start
                time.sleep(max(target_end - time.monotonic(), 0))

                publisher.send(data_dict)
                camera_publisher.send(png)

                if cbs_png is not None:
                    cbs_publisher.send({
                        'raw': cbs_raw_png,
                        'image': cbs_png,
                        **cbs_info,
                    })
                print()
                print()
    finally:
        print(f'{Fore.RED}{Style.BRIGHT}Crashed, cleaning up...{Style.RESET_ALL}')
        camera.stop()
        camera.close()
        camera_publisher.close()

        pressure_gauge.close()
        mfc.close()
        turbo.close()

        cbs_cam.close()
        cbs_publisher.close()







if __name__ == '__main__':
#    threading.Thread(target=spectrometer_thread).start()
    threading.Thread(target=webcam_thread).start()

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
