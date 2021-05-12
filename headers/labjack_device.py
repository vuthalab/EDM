from labjack import ljm

class Labjack:
    def __init__(self, serial_number):
        self.handle = ljm.openS("T7", "Ethernet", serial_number)
        # For test: string "-2" opens fake device. "ANY" opens any T7.

    def read(self, channel):
        return ljm.eReadName(self.handle, channel)

    def write(self, channel, value):
        success = ljm.eWriteName(self.handle, channel, value)
        return success

    def close(self):
        ljm.close(self.handle)
