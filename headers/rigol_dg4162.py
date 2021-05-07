from headers.usbtmc import USBTMCDevice

class RigolDG4162(USBTMCDevice):
    """USBMTC interface for DG4162 function generator."""

    def __init__(self, ip_address: str):
        super().__init__(ip_address, tcp_port=5555, mode='ethernet')

