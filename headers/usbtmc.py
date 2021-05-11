from typing import Optional, Literal, Union
import serial, time, telnetlib, itertools, os


ModeString = Union[Literal['serial'], Literal['ethernet'], Literal['direct']]


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
            mode: ModeString = 'serial'
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
            Must be one of 'serial', 'ethernet', or 'direct'.
            Controls which connection method to use.
            
            'serial' should be used for serial devices (generally /dev/ttyUSB*), such as
            the Prologix GPIB-USB converter.

            'direct' should be used for devices that expose a custom file-like interface,
            such as Rigol USBTMC devices (/dev/usbtmc*).

            'ethernet' should be used for networked LAN devices.
        """
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

        time.sleep(0.1)
        if mode == 'serial': assert self._conn.is_open

        time.sleep(0.1)
        self._name = self.query('*IDN?')
        print(f'Connected to {self.name}')


    @property
    def name(self) -> str: return self._name


    def stop(self) -> None:
        """
        Closes the connection.
        Subclasses may override this to add additional cleanup behavior.
        """
        self._conn.close()


    def __str__(self) -> str:
        """Default implementation. Override in subclasses."""
        return self.name


    ##### Utility Functions #####
    def _clear_output(self) -> None:
        """Clear any extraneous output that may show up in serial mode."""
        if self._mode != 'serial': return
        while self._conn.in_waiting > 0:
            print('Extra Output:', self._conn.readline())


    def send_command(self, command: str) -> None:
        """Send a command to the device."""
        print(' >', command)

        self._clear_output()
        self._conn.write((command + '\n').encode('utf-8'))

        if self._mode in ['serial', 'direct']: self._conn.flush()


    def query(self, command: str, raw: bool = False, delay: float = 0.1) -> Union[str, bytes]:
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
        self.send_command(command)

        time.sleep(delay)
        if self._mode == 'ethernet':
            for tries in itertools.count(1):
                response = self._conn.read_very_eager()
                if response: break
                if tries % 10 == 0:
                    print(f'Stuck querying {command}: try {tries}')
                time.sleep(0.2)

        if self._mode == 'direct':
            # We use os.read to prevent blocking.
            response = os.read(self._conn.fileno(), 2048)

        if self._mode == 'serial':
            # To avoid blocking and improve debugging,
            # we wait explicitly for input.
            for tries in itertools.count(1):
                time.sleep(0.2)
                if self._conn.in_waiting: break
                if tries % 10 == 0:
                    print(f'Stuck querying {command}: try {tries}')

            response = self._conn.readline()

        # Decode the response to a Python string if raw == False.
        return response if raw else response.decode('utf-8').strip()

    ##### Context Manager Magic Methods #####
    def __enter__(self): return self
    def __exit__(self, exception_type, exception_value, traceback): self.stop()
