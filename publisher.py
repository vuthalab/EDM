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

MAX_RATE = 0.5 # Hertz

def deconstruct(val): return (val.n, val.s)


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
    with zmq_server_socket(5551, 'edm-monitor') as publisher:
        while True:
            start = time.monotonic()

            pressures = {
                'chamber': pressure_gauge.pressure
            }

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

            voltages = {
                channel: deconstruct(labjack.read(channel))
                for channel in ['AIN1', 'AIN2']
            }

            flows = {
                'cell': deconstruct(mfc.flow_rate_cell),
                'neon': deconstruct(mfc.flow_rate_neon_line),
            }

            frequencies = {
                'BaF_Laser': wm.read_frequency(8) #read in GHz
            }

            spectral = {
                'transmission': deconstruct(spectrometer.transmission_scalar)
            }

            pt_on = pt.is_on()

            data_dict = {
                'pressures': pressures,
                'temperatures': temperatures,
                'heaters': heaters,
                'voltages': voltages,
                'flows': flows,
                'frequencies': frequencies,
                'pulsetube': {
                    'running': pt_on,
                },
                'spectral': spectral,
            }

            publisher.send(data_dict)
            printer.pprint(data_dict)


            ###### Software Interlocks #####
            cold_temps = [
                temperatures[name] for name in ['srb4k', 'saph', '4k plate', 'coll']
                if temperatures[name] is not None
            ]
            min_temp = min(cold_temps)

            # Determine whether pt has been running for 24 hrs
            if not pt_on: pt_last_off = time.monotonic()
            pt_running = (time.monotonic() - pt_last_off) > 24*60*60

            # Determine whether heaters are safe and working (all <20W, or temps >10K).
            # Will send a notification if unsafe for too long.
            heaters_safe = (
                all(power is None or power < 20 for power in heaters.values())
                or all(temp > 10 for temp in cold_temps)
            )
            if heaters_safe: heaters_last_safe = time.monotonic()

            print(f'{pt_on=} {pt_running=} {heaters_safe=} {min_temp=}')

            chamber_pressure = pressures['chamber']
            if chamber_pressure is not None:
                # Chamber pressure high during main experiment
                if chamber_pressure > 0.2 and pt_running:
                    for thermometer, _, _ in thermometers:
                        thermometer.disable_output()
                    mfc.off()

                    send_email(
                        'Pressure Interlock Activated',
                        f'Vacuum chamber pressure reached {chamber_pressure:.3f} torr while pulsetube is running! MFC and heaters disabled.'
                    )

                # Chamber pressurized while cold
                if chamber_pressure > 2 and min_temp < 270:
                    pt_status = 'on' if pt_on else 'off'
                    send_email(
                        'Pressure Warning',
                        f'Vacuum chamber pressure is abnormally high ({chamber_pressure:.3f} torr) while cold ({min_temp:.2f} K). Pulse tube is {pt_status}.'
                    )

            # Pulsetube running for last 24 hours, yet temperatures abnormally high
            if pt_running and any(temp > 30 for temp in cold_temps):
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
            time.sleep(max(1/MAX_RATE - dt, 0))

if __name__ == '__main__':
    while True:
        try:
            run_publisher()
        except:
            # Check if this was intentional
            tb = traceback.format_exc()
            if 'KeyboardInterrupt' in tb: break

            # Log error and send email
            with open('publisher-error-log.txt', 'a') as f:
                print(time.asctime(time.localtime()), tb, file=f)
            send_email('Publisher Crashed', tb, high_priority=False)

        time.sleep(1)

