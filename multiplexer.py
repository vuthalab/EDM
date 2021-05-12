"""
Utility for allowing multiple users to connect to the same ethernet resource. 

By default, creates multiplexer servers for both CTC100 temperature controllers,
and the Labjack MFC.

Author: Samuel Li
Date: May 11, 2021
"""

import socket, threading, time
import telnetlib

from headers.labjack_device import Labjack

class Multiplexer(threading.Thread):
    """Allows multiple connections to be made to the same port."""

    def __init__(self, local_port: int, name: str, connection, client_handler):
        """
        Initializes a new multiplexing server.

        local_port: int
            The port on which the server is hosted.

        name: str
            Human-readable name for this multiplexer.

        connection
            A direct connection to the device.

        client_handler
            A function with signature (multiplexer, client_socket, message)
            that handles messages from clients.
        """
        super().__init__()

        self.conn = connection
        self.name = name

        self._local_sock = socket.socket()
        self._local_sock.bind(('localhost', local_port))
        self._local_sock.listen(5)

        self.lock = threading.Lock()
        self._handler = client_handler
        print(f'Initialized new multiplexer on port {local_port}')

    def run(self):
        while True:
            conn, addr = self._local_sock.accept()
            ClientThread(conn, addr, self).start()


class ClientThread(threading.Thread):
    def __init__(self, client_socket, addr, multiplexer):
        super().__init__()
        self.client_socket = client_socket
        self.addr = addr
        self.multiplexer = multiplexer
        print('New client:', addr)

    def run(self):
        buff = b''
        try:
            while True:
                msg = self.client_socket.recv(1024)
                (msg, *buffs) = (buff + msg).split(b'\n')
                buff = b'\n'.join(buffs)
                if msg == b'': break
                print(self.addr, '>', self.multiplexer.name, ':', msg)

                if msg == b'lock':
                    self.multiplexer.lock.acquire()
                    self.client_socket.send(b'ok')
                    continue

                if msg == b'unlock':
                    self.multiplexer.lock.release()
                    self.client_socket.send(b'ok')
                    continue

                self.multiplexer._handler(self.multiplexer, self.client_socket, msg)
        finally:
            self.client_socket.close()
            if self.multiplexer.lock.locked():
                self.multiplexer.lock.release()
            print(f'{self.addr} closed')


##### Connection Handlers #####
def telnet_handler(multiplexer, client_socket, msg):
    if msg == b'read':
        response = multiplexer.conn.read_very_eager()
        print(multiplexer.name, '>', response)
        client_socket.send(response or b'\r\n')
    else:
        multiplexer.conn.write(msg + b'\n')

def labjack_handler(multiplexer, client_socket, msg):
    if msg == b'*IDN?':
        client_socket.send(b'Labjack')

    if msg.startswith(b'AIN'):
        response = multiplexer.conn.read(msg.decode('utf-8'))
        client_socket.send(f'{response:.8f}'.encode('utf-8'))

    if msg.startswith(b'DAC'):
        channel, rate = msg.split(b' ')
        rate = float(rate.decode('utf-8'))
        multiplexer.conn.write(channel.decode('utf-8'), rate)

    if msg == b'close':
        multiplexer.conn.close()



if __name__ == '__main__':
    TC1 = telnetlib.Telnet('192.168.0.104', port=23, timeout=2)
    TC2 = telnetlib.Telnet('192.168.0.107', port=23, timeout=2)
    L1 = Labjack('470017292')

    Multiplexer(31415, 'tc1', TC1, telnet_handler).start()
    Multiplexer(31416, 'tc2', TC2, telnet_handler).start()
    Multiplexer(31417, 'labjack', L1, labjack_handler).start()
