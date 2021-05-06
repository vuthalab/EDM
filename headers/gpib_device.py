from headers.usbtmc import USBTMCDevice

class GPIBDevice(USBTMCDevice):
    """Controls a GPIB device via the Prologix GPIB-USB converter."""

    def __init__(self,
            serial_port: str,
            gpib_addr: int,
            baud: int = 19200
        ):
        """
        Initialize a serial connection to the GPIB device.

        serial_port:
            Port on which Prologix GPIB-USB converter is located. Usually /dev/ttyUSB*.

        gpib_addr:
            GPIB address of device. Usually configurable on the device.

        baud:
            Baud rate of the serial connection. Usually ignored by the Prologix
            GPIB-USB converter, and can be set arbitrarily.
        """
        super().__init__(serial_port, baud)

        # Set address and timeout
        print('Bridge Version:', self.query('++ver'))
        self.send_command(f'++addr {gpib_addr}')
        self.send_command('++read_tmo_ms 30')

        # Clear existing output
        self.send_command('++read')
        while self._ser.read(): pass
