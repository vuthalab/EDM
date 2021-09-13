from headers.zmq_server_socket import create_server

from headers.CTC100 import CTC100

def ctc_thread():
    thermometers = [
        (CTC100(31415), ['saph', 'coll', 'bott hs', 'cell'], ['heat saph', 'heat coll']),
        (CTC100(31416), ['srb4k', 'srb45k', '45k plate', '4k plate'], ['srb45k out', 'srb4k out'])
    ]

    with create_server('ctc') as publisher:
        while True:
            ##### Read thermometers #####
            temperatures = {}
            heaters = {}

            for thermometer in thermometers:
                obj, temp_channels, heater_channels = thermometer

                for channel in temp_channels:
                    temperatures[channel] = obj.read(channel)

                for channel in heater_channels:
                    heaters[channel] = obj.read(channel)

            publisher.send({
                'temperatures': temperatures,
                'heaters': heaters,
            })
