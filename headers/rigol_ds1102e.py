from headers.usbtmc import USBTMCDevice

class RigolDS1102e(USBTMCDevice):
    """USBMTC interface for DS1102e oscilloscope."""

    def __init__(self, ip_address: str):
        super().__init__(ip_address, tcp_port=5555, use_ethernet=True)
