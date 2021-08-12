try:
    from headers.usbtmc import USBTMCDevice
except:
    from usbtmc import USBTMCDevice


class GPIBDevice(USBTMCDevice):
    """Controls a GPIB device via the Prologix GPIB-USB converter."""


    def __init__(self,
            serial_port: str,
            gpib_addr: int,

            name: str = None,
        ):
        """
        Initialize a serial connection to the GPIB device.
        Note that the baud rate is ignored by the Prologix converter, and can be set arbitrarily.

        serial_port:
            Port on which Prologix GPIB-USB converter is located. Usually /dev/ttyUSB*.

        gpib_addr:
            GPIB address of device. Usually configurable on the device.
        """
        super().__init__(serial_port, name=name)

        # Set address and timeout
        print('Bridge Version:', self.query('++ver'))
        self.send_command(f'++addr {gpib_addr}')
        self.send_command('++read_tmo_ms 30')

        # Clear existing output
        self.send_command('++read')
        self._clear_output()
