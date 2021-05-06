import serial, time

class USBTMCDevice:
    # Current serial connection
    _ser = None
    _name = None

    def __init__(self,
            serial_port: str,
            baud: int = 19200
        ):
        # Open the serial connection
        print(f'Opening serial connection on {serial_port}...', end=' ', flush=True)
        self._ser = serial.Serial(serial_port, baud, timeout=1)
        time.sleep(0.1)

        # Clear existing output
        self._ser.reset_input_buffer()
        self._ser.reset_output_buffer()
        while self._ser.read(): pass

        time.sleep(0.1)
        self._name = self.query('*idn?')

        print('Done.')

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
        self._ser.write((command + '\n').encode('utf-8'))
        time.sleep(0.1)
        self._ser.flush()
        time.sleep(0.3)

    def query(self, command: str) -> str:
        """Send a command to the device, and return its response."""
        self.send_command(command)
        response = self._ser.readline()
        return response.decode('utf-8').strip()
