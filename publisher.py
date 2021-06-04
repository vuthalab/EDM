import time, pprint, traceback

import asyncio

import numpy as np

from uncertainties import ufloat

#Import class objects
from headers.FRG730 import FRG730
from headers.CTC100 import CTC100
from headers.labjack_device import Labjack
from headers.mfc import MFC
from headers.zmq_server_socket import zmq_server_socket
from headers.wavemeter import WM
from headers.oceanfx import OceanFX
from pulsetube_compressor import PulseTube

from notify import send_email

PUBLISH_INTERVAL = 2 # publish every x seconds


FULL_TRANSMISSION_VOLTAGE = 3.196 # Initial voltage on transmission photodiode


def deconstruct(val): 
    """Deconstructs an uncertainty object into a tuple (value, uncertainty)"""
    if val is None: return None
    return (val.n, val.s)

async def with_uncertainty(getter, N=64, delay=2e-3):
    """Call the given getter function N times and return the mean and standard deviation."""
    values = []
    for i in range(N):
        values.append(getter())
        await asyncio.sleep(delay)
    return (np.mean(values), np.std(values))



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
    spectrometer = OceanFX()

    pt_last_off = 0
    heaters_last_safe = 0

    print('Starting publisher')
    printer = pprint.PrettyPrinter(indent=2)
    try:
        with zmq_server_socket(5551, 'edm-monitor') as publisher:
            while True:
                print('[LOOP START]')
                loop_start = time.monotonic()
                async_getters = []

                start = time.monotonic()
                chamber_pressure = pressure_gauge.pressure
                print(f'[SYNC] Read pressure took {time.monotonic() - start:.3f} seconds')

                ##### Read CTC100 Temperatures + Heaters (Async) #####
                temperatures = {}
                heaters = {}
                async def CTC_getter(thermometer):
                    """Record data from the given thermometer."""
                    start = time.monotonic()

                    obj, temp_channels, heater_channels = thermometer
                    for channel in temp_channels:
                        temperatures[channel] = await obj.async_read(channel)

                    for channel in heater_channels:
                        heaters[channel] = await obj.async_read(channel)

                    print(f'[ASYNC] Read CTC{obj._address[1]} took {time.monotonic() - start:.3f} seconds')

                async_getters.extend([
                    CTC_getter(thermometer) for thermometer in thermometers
                ])


                ##### Read MFC Flows (Async) #####
                flows = {}
                async def flow_getter():
                    """Record the flow rates from the MFC."""
                    start = time.monotonic()

                    flows['cell'] = deconstruct(await mfc.async_get_flow_rate_cell())
                    flows['neon'] = deconstruct(await mfc.async_get_flow_rate_neon_line())

                    print(f'[ASYNC] Read MFC took {time.monotonic() - start:.3f} seconds')
                async_getters.append(flow_getter())


                ##### Read wavemeter frequencies (Async) #####
                frequencies = {}
                async def frequency_getter():
                    """Record the frequencies from the wavemeter."""
                    start = time.monotonic()

                    frequencies['baf'] = await with_uncertainty(lambda: wm.read_frequency(8))
                    frequencies['calcium'] = await with_uncertainty(lambda: wm.read_frequency(6))

                    print(f'[ASYNC] Read Wavemeter took {time.monotonic() - start:.3f} seconds')
                async_getters.append(frequency_getter())

                start = time.monotonic()
                pt_on = pt.is_on()
                print(f'[SYNC] Read pulsetube took {time.monotonic() - start:.3f} seconds')

                start = time.monotonic()
                spectrometer.capture()
                I0, roughness = spectrometer.roughness_full
                print(f'[SYNC] Read spectrometer took {time.monotonic() - start:.3f} seconds')


                # Await all async data getters
                await asyncio.wait(async_getters, timeout=2)

                # Construct final data packet
                start = time.monotonic()
                data_dict = {
                    'pressure': deconstruct(chamber_pressure),

                    'temperatures': temperatures,
                    'heaters': heaters,

                    'refl': deconstruct(labjack.read('AIN1')),
                    'flows': flows,

                    'freq': frequencies,
                    'pulsetube': pt_on,
                    'rough': deconstruct(roughness),
                    'trans': {
                        'pd': deconstruct(100 * labjack.read('AIN2')/FULL_TRANSMISSION_VOLTAGE),
                        'spec': deconstruct(spectrometer.transmission_scalar),
                        'unexpl': deconstruct(I0),
                    },
                }
                print(f'[SYNC] Read miscellaneous took {time.monotonic() - start:.3f} seconds')
                printer.pprint(data_dict)


                ###### Software Interlocks #####
                cold_temps = {
                    name: temperatures[name] for name in ['srb4k', 'saph', '4k plate', 'coll']
                    if temperatures[name] is not None
                }
                min_temp = min(cold_temps.values())

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
                    if chamber_pressure.n > 0.2 and pt_running:
                        for thermometer, _, _ in thermometers:
                            thermometer.disable_output()
                        mfc.off()

                        send_email(
                            'Pressure Interlock Activated',
                            f'Vacuum chamber pressure reached {chamber_pressure:.3f} torr while pulsetube is running! MFC and heaters disabled.'
                        )

                    # Chamber pressurized while cold
                    if chamber_pressure.n > 2 and min_temp < 270:
                        pt_status = 'on' if pt_on else 'off'
                        send_email(
                            'Pressure Warning',
                            f'Vacuum chamber pressure is abnormally high ({chamber_pressure:.3f} torr) while cold ({min_temp:.2f} K). Pulse tube is {pt_status}.'
                        )

                # Pulsetube running for last 24 hours, yet temperatures abnormally high
                if pt_running and any(temp > 30 for temp in cold_temps.values()):
                    name, temp = max(cold_temps.items(), lambda _, temp: temp)
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
                dt = time.monotonic() - loop_start
                time.sleep(max(PUBLISH_INTERVAL - dt, 0))
                publisher.send(data_dict)
                print()
    finally:
        spectrometer.close()
        pressure_gauge.close()


if __name__ == '__main__':
    while True:
        try:
            asyncio.run(run_publisher())
        except:
            # Check if this was intentional
            tb = traceback.format_exc()
            print(tb)

            if 'KeyboardInterrupt' in tb: break

            # Log error and send email
            with open('publisher-error-log.txt', 'a') as f:
                print(time.asctime(time.localtime()), tb, file=f)
#            send_email('Publisher Crashed', tb, high_priority=False)

        time.sleep(1)
