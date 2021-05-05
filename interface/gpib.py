from interface.usbtmc import USBTMC

class GPIB(USBTMC):
    def __init__(self,
            serial_port: str,
            gpib_addr: int,
            baud: int = 19200
        ):
        super().__init__(serial_port, baud)

        # Set address and timeout
        print('Bridge Version:', self.query('++ver'))
        self.send_command(f'++addr {gpib_addr}')
        self.send_command('++read_tmo_ms 30')

        # Clear existing output
        self.send_command('++read')
        self._ser.read()

        # Display device model
        print('Device Model:', self.get_name())
