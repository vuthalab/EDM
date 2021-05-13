import time, pprint

#Import class objects
from headers.FRG730 import FRG730
from headers.CTC100 import CTC100
from headers.labjack_device import Labjack
from headers.mfc import MFC
from headers.zmq_server_socket import zmq_server_socket

MAX_RATE = 2 # Hertz


def run_publisher():
    print('Initializing devices...')
    pressure_gauge = FRG730('/dev/agilent_pressure_gauge')
    thermometers = [
        (CTC100(31415), ['saph', 'coll', 'bott hs', 'cell'], ['heat saph', 'heat coll']),
        (CTC100(31416), ['srb4k', 'srb45k', '45k plate', '4k plate'], ['srb45k out', 'srb4k out'])
    ]
    labjack = Labjack('470022275')
    mfc = MFC(31417)


    print('Starting publisher')
    printer = pprint.PrettyPrinter(indent=2)
    with zmq_server_socket(5551, 'edm-monitor') as publisher:
        last = time.time()

        while True:
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
                channel: labjack.read(channel)
                for channel in ['AIN1', 'AIN2']
            }

            flows = {
                'cell': mfc.flow_rate_cell,
                'neon': mfc.flow_rate_neon_line,
            }

            data_dict = {
                'pressures': pressures,
                'temperatures': temperatures,
                'heaters': heaters,
                'voltages': voltages,
                'flows': flows,
            }

            publisher.send(data_dict)
            printer.pprint(data_dict)

            # Can include some software interlocks here. Not sure that this is a great implementation.
            if pressures['chamber'] is not None and pressures['chamber'] > 0.1:
                for thermometer, _, _ in thermometers:
                    thermometer.disable_output()
                mfc.off()
                
                # TODO send email

            # Limit publishing speed
            dt = time.time() - last
            last = time.time()
            time.sleep(max(1/MAX_RATE - dt, 0))

if __name__ == '__main__':
    # TODO error handling
    run_publisher()
