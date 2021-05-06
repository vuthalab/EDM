import serial, time, telnetlib, itertools

class USBTMCDevice:
    # Current serial connection
    _ser = None
    _ethernet = False
    _name = None

    def __init__(self,
            serial_port: str,
            baud: int = 19200,
            use_ethernet: bool = False,
            tcp_port: int = 23,
        ):
        self._ethernet = use_ethernet

        # Open the serial connection
        print(f'Opening serial connection on {serial_port}...')
        if use_ethernet:
            self._ser = telnetlib.Telnet(serial_port, port=tcp_port, timeout=2)
        else:
            self._ser = serial.Serial(serial_port, baud, timeout=2)
        time.sleep(0.1)
        assert use_ethernet or self._ser.is_open

        time.sleep(0.1)
        self._name = self.query('*idn?')
        print(f'Connected to {self.name}')

    @property
    def name(self): return self._name

    def stop(self):
        """Closes the serial connection."""
        self._ser.close()

    def __str__(self) -> str:
        return self.name


    ##### Utility Functions #####
    def send_command(self, command: str) -> None:
        """Send a command to the device."""
        while not self._ethernet and self._ser.in_waiting > 0:
            print('Extra Output:', self._ser.readline())

        print('\t>>>', command)
        self._ser.write((command + '\n').encode('utf-8'))

        if not self._ethernet: self._ser.flush()

    def query(self, command: str) -> str:
        """Send a command to the device, and return its response."""
        self.send_command(command)

        if self._ethernet:
            time.sleep(0.3)
            return self._ser.read_all().decode('utf-8').strip()

        for tries in itertools.count(1):
            if self._ser.in_waiting: break

            if tries % 10 == 0:
                print(f'Stuck querying {command}: try {tries}')
            time.sleep(0.2)

        response = self._ser.readline()
        return response.decode('utf-8').strip()
