from labjack import ljm

class Labjack():
    def __init__(self, serial_number):
        self.handle = ljm.openS("T7", "Ethernet", serial_number) #For test: string "-2" opens fake device. "ANY" opens any T7.
        self.verbose = False
        self.active_channels = []

    def read(self, channel):
        val = ljm.eReadName(self.handle, channel)
        return val

    def write(self, channel, value):
        success = ljm.eWriteName(self.handle, channel, value)
        return success

    def close(self):
        ljm.close(self.handle)
