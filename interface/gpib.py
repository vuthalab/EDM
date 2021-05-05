import serial, time

class GPIB:
    # Current serial connection
    _ser = None

    def __init__(self,
            serial_port: str,
            gpib_addr: int,
            baud: int = 19200
        ):
        # Open the serial connection
        print(f'Opening serial connection on {serial_port}...', end=' ', flush=True)
        self._ser = serial.Serial(serial_port, baud, timeout=2)
        self._ser.reset_input_buffer()
        self._ser.reset_output_buffer()
        print('Done.')

        # Set address and timeout
        print('Bridge Version:', self.query('++ver'))
        self.send_command(f'++addr {gpib_addr}')
        self.send_command('++read_tmo_ms 30')

        # Clear existing output
        self.send_command('++read')
        self._ser.read()

        # Query model
        model = self.query('*idn?')
        print('Device Model:', model)

    def stop(self):
        """Closes the serial connection."""
        self._ser.close()


    ##### Utility Functions #####
    def send_command(self, command: str) -> None:
        """Send a command to the GPIB device."""
        self._ser.write((command + '\n').encode('utf-8'))
        time.sleep(1.0)

    def query(self, command: str) -> str:
        """Send a command to the GPIB device, and return its response."""
        self.send_command(command)
        response = self._ser.readline().strip()
        return response.decode('utf-8')
