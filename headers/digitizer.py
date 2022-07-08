import time
import socket

import numpy as np



class L4532A:
    def __init__(self, address='192.168.0.130', port=5025):
        self._conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self._conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_QUICKACK, 1)
        self._conn.settimeout(1.0)
        self._conn.connect((address, port))

        self.send_command('CONF:TRIG:SOURCE:CHAN:OFF ALL')
        self.send_command('CONF:TRIG:SOURCE EXTERNAL')
        self.send_command('CONF:ARM:SOURCE IMMEDIATE')

        self.send_command('CONF:CHAN:FILT (@1), LP_20_MHZ')
        self.send_command('CONF:CHAN:RANGE (@1), 0.25')
#        self.send_command('CONF:CHAN:RANGE (@1), 8')

        self.send_command('CONF:ACQ:SRATE (@1), 20000000')
        self.send_command('CONF:ACQ:SCOUNT (@1), 2048')
        self.send_command('CONF:ACQ:SPR (@1), 64')
        self.send_command('CONF:ACQ:RECORDS (@1), 1024')
        self.send_command('CONF:ACQ:THOLDOFF (@1), 0')
        self.send_command('CONF:ACQ:TDELAY (@1), 0')

        self.send_command('FORMAT:DATA:INT INT')
        self.init()

    def send_command(self, command):
        self._conn.send(f'{command}\n'.encode('utf-8'))

    def init(self):
        self.send_command('INIT')
        time.sleep(0.5)

    def fetch(self):
        """Get a waveform from the digitizer."""
        self.send_command('READ:WAV:ADC? (@1)')

        # Read data
        header = self._conn.recv(11)
        num_bytes = int(header.decode('ascii')[2:])
        data = bytearray()
        while len(data) < num_bytes:
            packet = self._conn.recv(num_bytes - len(data))
            data.extend(packet)
        self._conn.recv(1)

#        print(num_bytes, len(data))
#        print(num_bytes // 2 / 20, 'us')
        return np.frombuffer(data, dtype=np.int16)

if __name__ == '__main__':
    import matplotlib.pyplot as plt

    digitizer = L4532A()

    data = []
    for i in range(800):
        print(i)
        data.append(digitizer.fetch())
    data = np.array(data)
    plt.plot(np.mean(data, axis=0))
#    plt.imshow(data)
    plt.show()
