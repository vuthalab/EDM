import time, pprint, traceback

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

PUBLISH_INTERVAL = 3 # publish every x seconds


FULL_TRANSMISSION_VOLTAGE = 3.869 # Initial voltage on transmission photodiode

def deconstruct(val): 
    if val is None: return None
    return (val.n, val.s)

def run_publisher():
    print('Initializing devices...')
    pressure_gauge = FRG730('/dev/agilent_pressure_gauge')
    thermometers = [
        (CTC100(31415), ['saph', 'coll', 'bott hs', 'cell'], ['heat saph', 'heat coll']),
        (CTC100(31416), ['srb4k', 'srb45k', '45k plate', '4k plate'], ['srb45k out', 'srb4k out'])
    ]
    labjack = Labjack('470022275')
    mfc = MFC(31417)
    wm = WM(publish=False) #wavemeter class used for reading frequencies from high finesse wavemeter
    spectrometer = OceanFX()
    pt = PulseTube()

    pt_last_off = 0
    heaters_last_safe = 0

    print('Starting publisher')
    printer = pprint.PrettyPrinter(indent=2)
    try:
        with zmq_server_socket(5551, 'edm-monitor') as publisher:
            while True:
                start = time.monotonic()

                chamber_pressure = pressure_gauge.pressure

                temperatures = {
                    channel: thermometer.read(channel)
                    for thermometer, inputs, _ in thermometers
                    for channel in inputs
                }

                heaters = {
                    channel: thermometer.read(channel)
                    for thermometer, _, outputs in thermometers
                    for channel in outputs
                }

                flows = {
                    'cell': deconstruct(mfc.flow_rate_cell),
                    'neon': deconstruct(mfc.flow_rate_neon_line),
                }

                frequencies = {
                    'BaF_Laser': wm.read_frequency(8) #read in GHz
                }

                pt_on = pt.is_on()
                spectrometer.capture()

                I0, roughness = spectrometer.roughness_full

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

                publisher.send(data_dict)
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
                dt = time.monotonic() - start
                time.sleep(max(PUBLISH_INTERVAL - dt, 0))
    finally:
        spectrometer.close()
        pressure_gauge.close()

if __name__ == '__main__':
    while True:
        try:
            run_publisher()
        except:
            # Check if this was intentional
            tb = traceback.format_exc()
            if 'KeyboardInterrupt' in tb:
                print(tb)
                break

            # Log error and send email
            with open('publisher-error-log.txt', 'a') as f:
                print(time.asctime(time.localtime()), tb, file=f)
            send_email('Publisher Crashed', tb, high_priority=False)

        time.sleep(1)

