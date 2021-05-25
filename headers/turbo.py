"""
Header to control the TwisTorr 74 FS AG.
All packets are taken from the user manual.

Author: Samuel Li
May 25, 2021
"""
import time, serial
from functools import reduce

HEADER = b'\x02\x80'
FOOTER = b'\x03'
PACKETS = {
    'start': b'\x02\x8000011\x03\x42\x33',
    'stop': b'\x02\x8000010\x03\x42\x32',

    'status': b'\x02\x802050\x03\x38\x37',
    'current': b'\x02\x802000\x03\x38\x37',

    'ack': b'\x02\x80\x06\x03\x38\x35',
}


class TurboPump:
    def __init__(self, port='/dev/ttyUSB3'):
        self._conn = serial.Serial(port, 9600, timeout=0.5)

    ##### Private Util Functions #####
    def _pad_packet(self, packet):
        packet = HEADER + packet + FOOTER
        crc = self._compute_crc(packet)
        return packet + crc

    def _compute_crc(self, packet):
        crc = reduce(lambda a, b: a ^ b, packet[1:], 0)
        return hex(crc)[2:].upper().encode('utf-8')

    def _query(self, packet):
        self._conn.write(self._pad_packet(packet))
        response = self._conn.read(32)
        response, crc = response[:-2], response[-2:]
        assert self._compute_crc(response) == crc
        return response[2:-1]

    def _read_int(self, window):
        window = str(window).encode('utf-8')
        response = self._query(window + b'0')
        assert response[:3] == window
        return int(response[3:])


    ##### Public Interface #####
    def on(self):
        assert self._query(b'00011') == b'\x06'
        print('Turbo on')

    def off(self):
        assert self._query(b'00010') == b'\x06'
        print('Turbo off')


    def start(self): self.on()
    def stop(self): self.off()

    @property
    def operation_status(self):
        response = self._query(b'2050')
        return [
            'stopped',
            'waiting intlk',
            'starting',
            'auto-tuning',
            'braking',
            'normal',
            'failed',
        ][response[9] - 48]

    @property
    def current(self):
        """Return the pump current [mA]."""
        return self._read_int(200)

    @property
    def voltage(self):
        """Return the pump voltage [Vdc]."""
        return self._read_int(201)

    @property
    def speed(self):
        """Return the pump speed [Hz]."""
        return self._read_int(203)

    @property
    def temperature(self):
        """Return the pump temperature [°C]."""
        return self._read_int(204)


    ##### Convenience Functions ####
    def status(self):
        print('Status:', self.operation_status)
        print('Current:', self.current, 'mA')
        print('Voltage:', self.voltage, 'V')
        print('Speed:', self.speed, 'Hz')
        print('Temperature:', self.temperature, '°C')

    def __enter__(self): return self
    def __exit__(self):
        self._conn.close()
        return self


if __name__ == '__main__':
    turbo = TurboPump()
    turbo.status()
