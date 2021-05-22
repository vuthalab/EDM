"""
Utility for allowing multiple users to connect to the same ethernet resource. 

By default, creates multiplexer servers for both CTC100 temperature controllers,
and the Labjack MFC.

Documentation: https://electricatoms.wordpress.com/2021/05/22/multiplexer-server-documentation/

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

        # Set instance variables
        self.conn = connection
        self.name = name

        self.lock = threading.Lock()
        self._handler = client_handler

        # Create a listener server on the given port
        self._local_sock = socket.socket()
        self._local_sock.bind(('localhost', local_port))
        self._local_sock.listen(5)

        print(f'Initialized new multiplexer on port {local_port}')

    def run(self):
        while True:
            # Accept new connections forever.
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
                # Read packet from client.
                msg = self.client_socket.recv(1024)

                # Extract the next line, and keep remaining lines in a buffer.
                # If we receive an empty packet, then crash gracefully.
                # (Sometimes a dropped connection looks like an empty packet.)
                (msg, *buffs) = (buff + msg).split(b'\n')
                buff = b'\n'.join(buffs)
                if msg == b'': break

                # Log command (for debug)
                print(self.addr, '>', self.multiplexer.name, ':', msg)

                # Acquire thread lock for safe atomic read
                if msg == b'lock':
                    self.multiplexer.lock.acquire()
                    self.client_socket.send(b'ok')
                    continue

                # Discard thread lock. Sometimes yells about unlocking
                # if already unlocked, but nobody cares.
                if msg == b'unlock':
                    try:
                        self.multiplexer.lock.release()
                    finally:
                        self.client_socket.send(b'ok')
                        continue

                # Pass on the request to the handler function,
                # where stuff actually happens.
                self.multiplexer._handler(self.multiplexer, self.client_socket, msg)
        except Exception as e:
            print(e)
        finally:
            # Clean up this connection.
            self.client_socket.close()
            if self.multiplexer.lock.locked():
                self.multiplexer.lock.release()
            print(f'{self.addr} closed')


##### Connection Handlers #####
def telnet_handler(multiplexer, client_socket, msg):
    if msg == b'read':
        # Query the response and return.
        response = multiplexer.conn.read_very_eager()
        print(multiplexer.name, '>', response)
        client_socket.send(response or b'\r\n')
    else:
        # Just pass on the packet.
        multiplexer.conn.write(msg + b'\n')

def labjack_handler(multiplexer, client_socket, msg):
    # Implement a USBTMC-like name function
    if msg == b'*IDN?':
        client_socket.send(b'Labjack')

    # Client wants to read a voltage.
    if msg.startswith(b'AIN'):
        # Read the voltage. Returns a float, since
        # `multiplexer.conn` is a Labjack object.
        voltage = multiplexer.conn.read(msg.decode('utf-8'))

        # Send the response, formatted as bytes.
        client_socket.send(f'{voltage:.8f}'.encode('utf-8'))

    # Client wants to set a voltage.
    if msg.startswith(b'DAC'):
        # Read the channel and voltage from the packet.
        channel, voltage = msg.split(b' ')
        voltage = float(voltage.decode('utf-8'))

        # Set the voltage by calling `.write()` on the 
        # Labjack object.
        multiplexer.conn.write(channel.decode('utf-8'), voltage)



if __name__ == '__main__':
    TC1 = telnetlib.Telnet('192.168.0.104', port=23, timeout=2)
    TC2 = telnetlib.Telnet('192.168.0.107', port=23, timeout=2)
    L1 = Labjack('470017292')

    Multiplexer(31415, 'tc1', TC1, telnet_handler).start()
    Multiplexer(31416, 'tc2', TC2, telnet_handler).start()
    Multiplexer(31417, 'labjack', L1, labjack_handler).start()
