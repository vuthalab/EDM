import serial, time, telnetlib, itertools, os

class USBTMCDevice:
    # Current connection
    _conn = None
    _mode = None
    _name = None

    def __init__(self,
            resource_path: str,
            baud: int = 19200,

            tcp_port: int = 23, # For ethernet connections
            mode: str = 'serial' # One of serial, ethernet, or direct (file)
        ):
        self._mode = mode 

        # Open the connection
        if mode == 'ethernet':
            print(f'Opening LAN connection on {resource_path}:{tcp_port}...')
            self._conn = telnetlib.Telnet(resource_path, port=tcp_port, timeout=2)

        if mode == 'serial':
            print(f'Opening serial connection on {resource_path}...')
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
    def name(self): return self._name

    def stop(self):
        """Closes the connection."""
        self._conn.close()

    def __str__(self) -> str:
        return self.name


    ##### Utility Functions #####
    def _clear_output(self):
        if self._mode != 'serial': return
        while self._conn.in_waiting > 0:
            print('Extra Output:', self._conn.readline())

    def send_command(self, command: str) -> None:
        """Send a command to the device."""
        print(' >', command)

        self._clear_output()
        self._conn.write((command + '\n').encode('utf-8'))

        if self._mode in ['serial', 'direct']: self._conn.flush()

    def query(self, command: str, raw: bool = False, delay: float = 0.1) -> str:
        """Send a command to the device, and return its response."""
        self.send_command(command)

        time.sleep(delay)
        if self._mode == 'ethernet':
            response = self._conn.read_all()

        if self._mode == 'direct':
            response = os.read(self._conn.fileno(), 2048)

        if self._mode == 'serial':
            for tries in itertools.count(1):
                if self._conn.in_waiting: break

                if tries % 10 == 0:
                    print(f'Stuck querying {command}: try {tries}')
                time.sleep(0.2)

            response = self._conn.readline()

        return response if raw else response.decode('utf-8').strip()
