from typing import Optional, Literal, Union
import serial, time, telnetlib, itertools, os, socket, select, traceback

import asyncio
from colorama import Fore, Style


ModeString = Union[Literal['serial'], Literal['ethernet'], Literal['direct'], Literal['multiplexed']]

DEBUG = True # Whether to print commands as they are sent
DRY_RUN = False # If true, nothing actually happens (useful for debug)


class USBTMCDevice:
    """The currently open connection."""
    _conn = None

    """The current connection mode."""
    _mode: ModeString = None

    """The name of this device."""
    _name: Optional[str] = None


    def __init__(self,
            resource_path: str,

            tcp_port: int = 23,
            mode: ModeString = 'serial',
            name: Optional[str] = None,
        ):
        """
        Initializes a connection to the USBTMC device.

        resource_path: str
            For serial or direct connections, the path to the serial port.
            Usually /dev/ttyUSB* for serial /dev/usbtmc* for direct.
            For ethernet connections, the IP address of the device.

        tcp_port: int
            Only used for ethernet connections. The port on which to connect to the device.

        mode: str
            Must be one of 'serial', 'ethernet', 'direct', or 'multiplexed'.
            Controls which connection method to use.
            
            'serial' should be used for serial devices (generally /dev/ttyUSB*), such as
            the Prologix GPIB-USB converter.

            'direct' should be used for devices that expose a custom file-like interface,
            such as Rigol USBTMC devices (/dev/usbtmc*).

            'ethernet' should be used for networked LAN devices.
        """
        if DRY_RUN:
            print(f'  [{Fore.YELLOW}WARN{Style.RESET_ALL}] Dry-run mode active. Nothing will actually happen.')

        self._mode = mode 

        # Open the connection
        if mode == 'ethernet':
            print(f'Opening LAN connection on {resource_path}:{tcp_port}...')
            self._conn = telnetlib.Telnet(resource_path, port=tcp_port, timeout=2)

        if mode == 'serial':
            print(f'Opening serial connection on {resource_path}...')
            baud = 19200
            self._conn = serial.Serial(resource_path, baud, timeout=2)

        if mode == 'direct':
            print(f'Opening USBTMC connection on {resource_path}...')
            self._conn = open(resource_path, 'r+b')

        if mode == 'multiplexed':
            # For async: defer connection until later.
            self._async_conn = None
            self._address = ('127.0.0.1', resource_path)

            try:
                print(f'  [{Fore.BLUE}INFO{Style.RESET_ALL}] {Style.DIM}Connecting to multiplexer server on port {Style.RESET_ALL}{Style.BRIGHT}{resource_path}{Style.RESET_ALL}')
                self._conn = socket.socket()
                self._conn.connect(self._address)
                self._conn.settimeout(2)
            except:
                print(f'{Fore.RED}Please start the multiplexer server!{Style.RESET_ALL}')
                self._conn = None

        time.sleep(0.1)
        self._name = name or self.query('*IDN?')
        print(f'  [{Fore.BLUE}INFO{Style.RESET_ALL}] {Style.DIM}Connected to {Style.RESET_ALL}{Style.BRIGHT}{self.name}{Style.RESET_ALL}')


    @property
    def name(self) -> str: return self._name


    def close(self) -> None:
        """
        Closes the connection.
        Subclasses may override this to add additional cleanup behavior.
        """
        if self._mode == 'multiplexed':
            self._conn.send(b'unlock')

            if self._async_conn is not None:
                reader, writer = self._async_conn
                writer.close()

        self._conn.close()


    def __str__(self) -> str:
        """Default implementation. Override in subclasses."""
        return self.name

    @property
    def short_name(self) -> str:
        return self.name[:20] if self.name is not None else 'unknown'


    ##### Utility Functions #####
    def _clear_output(self) -> None:
        """Clear any extraneous output that may show up in serial mode."""
        if self._mode != 'serial': return
        while self._conn.in_waiting > 0:
            print('Extra Output:', self._conn.readline())


    def send_command(self, command: str, raw: bool = False, delay: float = 0.2) -> None:
        """Send a command to the device."""
        if DEBUG: print(f'  [{Fore.RED}SEND{Style.RESET_ALL}] {Style.DIM}{self.short_name:20s} <{Style.RESET_ALL} {Fore.RED}{command}{Style.RESET_ALL}')
        if DRY_RUN: return

        if not raw:
            command = (command + '\n').encode('utf-8')

        if self._mode == 'multiplexed':
            self._conn.send(command)

            # unless you read after, a 0.2 s
            # delay is necessary because of
            # TCP packet scheduling voodoo magic
            time.sleep(delay)
            return

        self._clear_output()
        self._conn.write(command)

        if self._mode in ['serial', 'direct']:
            self._conn.flush()
            time.sleep(delay)


    def query(
        self,
        command: str,
        raw: bool = False,
        raw_command: bool = False,
        delay: float = 2e-2
    ) -> Union[str, bytes]:
        """
        Send a command to the device, and return its response.

        command: str
            The command to send.

        raw: bool
            Whether to return the response as raw bytes or a Python string.

        delay: float
            Delay between writing the command and reading the response.
            Increase the delay for commands that return large amounts of data.
        """
        if DRY_RUN:
            self.send_command(command, raw=raw_command, delay=0)
            return None

        if self._mode != 'multiplexed':
            self.send_command(command, raw=raw_command, delay=delay)

        if self._mode == 'ethernet':
            for tries in itertools.count(1):
                response = self._conn.read_very_eager()
                if response: break
                time.sleep(0.2)
                if tries > 30: return None

        if self._mode == 'direct':
            # We use os.read to prevent blocking.
            response = os.read(self._conn.fileno(), 2048)

        if self._mode == 'serial':
            # To avoid blocking and improve debugging,
            # we wait explicitly for input.
            for tries in itertools.count(1):
                time.sleep(0.2)
                if self._conn.in_waiting: break
                if tries > 30: return None

            response = self._conn.readline()

        if self._mode == 'multiplexed':
            # Acquire lock
            self._conn.send(b'lock\n')
            assert self._conn.recv(32) == b'locked'

            # Send command and wait for device response
            self.send_command(command, raw=raw_command, delay=delay)

            # Read response
            for i in range(20):
                self._conn.send(b'read\n')
                response = self._conn.recv(1024)
                if response != b'read failed': break
                time.sleep(5e-2)
                print(f'  [{Fore.BLUE}INFO{Style.RESET_ALL}] {Style.DIM}{self.short_name:20s} :{Style.RESET_ALL} {Fore.BLUE}Read failed, trying again.{Style.RESET_ALL}')
            else:
                raise ValueError('Read failed too many times.')

            # Release lock
            time.sleep(1e-3)
            self._conn.send(b'unlock\n')
            time.sleep(2e-3)
            assert self._conn.recv(32) == b'unlocked'


        if DEBUG: print(f'  [{Fore.GREEN}RECV{Style.RESET_ALL}] {Style.DIM}{self.short_name:20s} >{Style.RESET_ALL} {Fore.GREEN}{response[:50]}{Style.RESET_ALL}')

        # Decode the response to a Python string if raw == False.
        return response if raw else response.decode('utf-8').strip()


    ##### Async Code #####
    async def open_async_connection(self):
        """Open a new async TCP connection, if not already opened."""
        assert self._mode == 'multiplexed'
        if self._async_conn is not None: return
        self._async_conn = await asyncio.open_connection(*self._address)


    async def async_query(
            self,
            command: str,
            raw: bool = False,
            raw_command: bool = False,
            delay: float = 2e-2
        ) -> Union[str, bytes]:

        await self.open_async_connection()
        reader, writer = self._async_conn

        # Acquire lock
        writer.write(b'lock\n')
        await writer.drain()
        assert await reader.read(32) == b'locked'

        # Send command and wait for device response
        if DEBUG: print(f'  [{Fore.RED}SEND{Style.RESET_ALL}] {Style.DIM}{self.short_name:20s} <{Style.RESET_ALL} {Fore.RED}{command}{Style.RESET_ALL}')
        if not raw_command:
            command = (command + '\n').encode('utf-8')
        writer.write(command)
        await writer.drain()
        await asyncio.sleep(delay)

        # Read response
        for i in range(20):
            writer.write(b'read\n')
            await writer.drain()


            response = await reader.read(1024)
            if response != b'read failed': break
            await asyncio.sleep(5e-2)
            print(f'  [{Fore.BLUE}INFO{Style.RESET_ALL}] {Style.DIM}{self.short_name:20s} :{Style.RESET_ALL} {Fore.BLUE}Read failed, trying again.{Style.RESET_ALL}')
        else:
            raise ValueError('Read failed too many times.')

        if DEBUG: print(f'  [{Fore.GREEN}RECV{Style.RESET_ALL}] {Style.DIM}{self.short_name:20s} >{Style.RESET_ALL} {Fore.GREEN}{response[:50]}{Style.RESET_ALL}')

        # Release lock
        await asyncio.sleep(1e-3)
        writer.write(b'unlock\n')
        await writer.drain()
        await asyncio.sleep(2e-3)
        ack = await asyncio.wait_for(
            reader.read(32),
            timeout=5
        )
        assert ack == b'unlocked'

        # Decode the response to a Python string if raw == False.
        return response if raw else response.decode('utf-8').strip()


    ##### Context Manager Magic Methods #####
    def __enter__(self): return self
    def __exit__(self, exception_type, exception_value, traceback): self.close()
