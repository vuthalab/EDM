"""
Header to control the TwisTorr 74 FS AG.
All packets are taken from the user manual.

Author: Samuel Li
May 25, 2021
"""
import time

from functools import reduce

try:
    from headers.usbtmc import USBTMCDevice
except:
    from usbtmc import USBTMCDevice


HEADER = b'\x02\x80'
FOOTER = b'\x03'
PACKETS = {
    'start': b'\x02\x8000011\x03\x42\x33',
    'stop': b'\x02\x8000010\x03\x42\x32',

    'status': b'\x02\x802050\x03\x38\x37',
    'current': b'\x02\x802000\x03\x38\x37',

    'ack': b'\x02\x80\x06\x03\x38\x35',
}


class TurboPump(USBTMCDevice):
    def __init__(self, multiplexer_port=31418):
        super().__init__(multiplexer_port, mode='multiplexed', name='Turbo')

    ##### Private Util Functions #####
    def _pad_packet(self, packet):
        packet = HEADER + packet + FOOTER
        crc = self._compute_crc(packet)
        return packet + crc

    def _compute_crc(self, packet):
        crc = reduce(lambda a, b: a ^ b, packet[1:], 0)
        return hex(crc)[2:].upper().encode('utf-8')

    def _decode_packet(self, packet):
        response, crc = packet[:-2], packet[-2:]
        assert self._compute_crc(response) == crc
        return response[2:-1]

    def _query(self, packet):
        response = self.query(self._pad_packet(packet), raw=True, raw_command=True)
        return self._decode_packet(response)

    async def _async_query(self, packet):
        response = await self.async_query(self._pad_packet(packet), raw=True, raw_command=True)
        return self._decode_packet(response)

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

    def _decode_operation_status(self, packet):
        return [
            'stopped',
            'waiting intlk',
            'starting',
            'auto-tuning',
            'braking',
            'normal',
            'failed',
        ][packet[9] - 48]

    @property
    def operation_status(self):
        response = self._query(b'2050')
        return self._decode_operation_status(response)

    async def async_operation_status(self):
        response = await self._async_query(b'2050')
        return self._decode_operation_status(response)

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
        self.close()
        return self


if __name__ == '__main__':
    turbo = TurboPump()
    turbo.status()
