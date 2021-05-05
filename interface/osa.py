import numpy as np

from interface.gpib import GPIB


class OSA(GPIB):
    SERIAL_PORT = '/dev/serial/by-id/usb-Prologix_Prologix_GPIB-USB_Controller_PX96QTQY-if00-port0'

    def __init__(self, gpib_addr: int):
        super().__init__(self.SERIAL_PORT, gpib_addr)

    def read_array(self, command: str):
        """Read a float array from the GPIB device."""
        entries = self.query(command).split(',')
        n = int(entries[0])
        data = np.array([float(x.strip()) for x in entries[1:]])
        assert len(data) == n
        return data

    def get_wavelengths(self, trace: str):
        """Retrieves the wavelength data (nm) from the specified trace."""
        print('Retrieving wavelengths (nm)...')
        return self.read_array(f'WDAT{trace}')

    def get_levels(self, trace: str):
        """Retrieves the level data (dBm) from the specified trace."""
        print('Retrieving levels (dBm)...')
        return self.read_array(f'LDAT{trace}')

    def get_spectrum(self, trace: str):
        """Retrieves the specified trace from the OSA."""
        return self.get_wavelengths(trace), self.get_levels(trace)
