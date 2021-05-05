from interface.usbtmc import USBTMC 

class Oscilloscope(USBTMC):
    """USBMTC interface for DS1102e oscilloscope."""

    def __init__(self):
        super().__init__('/dev/usbtmc0')
