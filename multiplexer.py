"""
Utility for allowing multiple users to connect to the same ethernet resource. 

By default, creates multiplexer servers for both CTC100 temperature controllers,
and the Labjack MFC.

Documentation: https://electricatoms.wordpress.com/2021/05/22/multiplexer-server-documentation/

Author: Samuel Li
Date: May 11, 2021
"""

import socket, threading, time, serial
import telnetlib

from colorama import Fore, Style

from headers.labjack_device import Labjack

from uncertainties import ufloat


class Multiplexer(threading.Thread):
    """Allows multiple connections to be made to the same port."""

    def __init__(self, local_port: int, connection, client_handler):
        """
        Initializes a new multiplexing server.

        local_port: int
            The port on which the server is hosted.

        connection
            A direct connection to the device.

        client_handler
            A function with signature (multiplexer, client_socket, message)
            that handles messages from clients.
        """
        super().__init__()

        # Set instance variables
        self.conn = connection

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

        host, port = client_socket.getsockname()
        self.name = f'{host}:{port}'

        self.multiplexer = multiplexer

        self.client_name = f'{addr[0]}:{addr[1]}'
        print('New client:', self.client_name)

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
                print(f'[{Fore.GREEN}RECV{Style.RESET_ALL}] {Style.DIM}{self.name:15s} < {self.client_name:15s}{Style.RESET_ALL} | {Fore.GREEN}{msg}{Style.RESET_ALL}')

                # Acquire thread lock for safe atomic read
                if msg == b'lock':
                    self.multiplexer.lock.acquire()
                    self.client_socket.send(b'locked')
                    print(f'[{Fore.RED}SEND{Style.RESET_ALL}] {Style.DIM}{self.name:15s} > {self.client_name:15s}{Style.RESET_ALL} | {Fore.BLUE}locked{Style.RESET_ALL}')
                    continue

                # Discard thread lock. Sometimes yells about unlocking
                # if already unlocked, but nobody cares.
                if msg == b'unlock':
                    try:
                        self.multiplexer.lock.release()
                    finally:
                        self.client_socket.send(b'unlocked')
                        print(f'[{Fore.RED}SEND{Style.RESET_ALL}] {Style.DIM}{self.name:15s} > {self.client_name:15s}{Style.RESET_ALL} | {Fore.BLUE}unlocked{Style.RESET_ALL}')
                        continue

                # Pass on the request to the handler function,
                # where stuff actually happens.
                self.multiplexer._handler(self, msg)
        except Exception as e:
            print(e)
        finally:
            # Clean up this connection.
            self.client_socket.close()
            if self.multiplexer.lock.locked():
                self.multiplexer.lock.release()
            print(f'[{Fore.BLUE}INFO{Style.RESET_ALL}] {self.name} | client {self.client_name} dropped')


##### Connection Handlers #####
def telnet_handler(client_thread, msg):
    conn = client_thread.multiplexer.conn
    client_socket = client_thread.client_socket

    if msg == b'read':
        # Query the response and return.
        response = conn.read_very_eager()
        if response in [b'', b'\r\n']:
            response = b'read failed'

        print(f'[{Fore.RED}SEND{Style.RESET_ALL}] {Style.DIM}{client_thread.name:15s} > {client_thread.client_name:15s}{Style.RESET_ALL} | {Fore.RED}{response}{Style.RESET_ALL}')
        client_socket.send(response)
    else:
        # Just pass on the packet.
        conn.write(msg + b'\n')

def serial_handler(client_thread, msg):
    conn = client_thread.multiplexer.conn
    client_socket = client_thread.client_socket

    if msg == b'read':
        # Query the response and return.
        response = conn.read(1024)
        if response in [b'', b'\r\n']:
            response = b'read failed'

        print(f'[{Fore.RED}SEND{Style.RESET_ALL}] {Style.DIM}{client_thread.name:15s} > {client_thread.client_name:15s}{Style.RESET_ALL} | {Fore.RED}{response}{Style.RESET_ALL}')
        client_socket.send(response)
    else:
        # Just pass on the packet.
        conn.write(msg + b'\n')


def labjack_handler(client_thread, msg):
    conn = client_thread.multiplexer.conn
    client_socket = client_thread.client_socket

    # Implement a USBTMC-like name function
    if msg == b'*IDN?':
        client_socket.send(b'Labjack')

    # Client wants to read a voltage.
    if msg.startswith(b'AIN'):
        # Read the voltage. Returns a ufloat, since
        # `multiplexer.conn` is a Labjack object.
        voltage = conn.read(msg.decode('utf-8'))

        # Send the response, formatted as bytes.
        client_socket.send(f'{voltage.n:.8f} {voltage.s:.8f}'.encode('utf-8'))


    # Client wants to set a voltage.
    if msg.startswith(b'DAC'):
        # Read the channel and voltage from the packet.
        channel, voltage = msg.split(b' ')
        voltage = float(voltage.decode('utf-8'))

        # Set the voltage by calling `.write()` on the 
        # Labjack object.
        conn.write(channel.decode('utf-8'), voltage)




if __name__ == '__main__':
    TC1 = telnetlib.Telnet('192.168.0.104', port=23, timeout=2)
    TC2 = telnetlib.Telnet('192.168.0.107', port=23, timeout=2)
    mfc = Labjack('470017292')
    turbo = serial.Serial('/dev/ttyUSB3', 9600, timeout=0.5)

    Multiplexer(31415, TC1, telnet_handler).start()
    Multiplexer(31416, TC2, telnet_handler).start()
    Multiplexer(31417, mfc, labjack_handler).start()
    Multiplexer(31418, turbo, serial_handler).start()
