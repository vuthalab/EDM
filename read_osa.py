import serial, time, sys
import numpy as np
import matplotlib.pyplot as plt


class OSA:
    # Current serial connection
    _ser = None

    def __init__(self,
            serial_port: str , 
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

        # Query OSA model
        model = self.query('*idn?')
        print('OSA Model:', model)

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

    def read_array(self, command: str):
        """Read a float array from the GPIB device."""
        entries = self.query(command).split(',')
        n = int(entries[0])
        data = np.array([float(x.strip()) for x in entries[1:]])
        assert len(data) == n
        return data


    ##### Data Reading #####
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


if __name__ == '__main__':
    # OSA Port + Address
    SERIAL_PORT = '/dev/ttyUSB1' # Run dmesg | grep "FTDI" to locate port
    GPIB_ADDRESS = 1 # Configurable on the OSA

    osa = OSA(SERIAL_PORT, GPIB_ADDRESS)

    # Get sample spectrum from OSA
    wavelengths, levels = osa.get_spectrum('A')

    # Plot data
    plt.plot(wavelengths, levels)
    plt.xlabel('Wavelength (nm)')
    plt.ylabel('Power (dBm)')
    plt.title(f'Ambient Spectrum')
    plt.show()

    osa.stop()
