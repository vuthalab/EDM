import serial, time, sys
import numpy as np
import matplotlib.pyplot as plt


# OSA Port + Address
SERIAL_PORT = '/dev/ttyUSB2' # Run dmesg | grep "FTDI" to locate port
GPIB_ADDRESS = 1 # Configurable on the OSA


# Current serial connection
ser = None

def open_connection(port: str, gpib_addr: int):
    """Opens a new serial connection to the specified GPIB device."""
    global ser

    # Open the serial connection
    print(f'Opening serial connection on {port}...', end=' ', flush=True)
    baud = 19200
    ser = serial.Serial(port, baud, timeout=2)
    ser.reset_input_buffer()
    ser.reset_output_buffer()
    print('Done.')

    # Set address and timeout
    print('Bridge Version:', query('++ver'))
    send_command(f'++addr {gpib_addr}')
    send_command('++read_tmo_ms 30')

    # Clear existing output
    send_command('++read')

    # Query OSA model
    model = query('*idn?')
    print('OSA Model:', model)


##### Utility Functions #####
def send_command(command):
    """Send a command to the GPIB device."""
    ser.write((command + '\n').encode('utf-8'))
    time.sleep(0.5)

def query(command):
    """Send a command to the GPIB device, and return its response."""
    send_command(command)
    response = ser.readline().strip()
    return response.decode('utf-8')

def read_array(command):
    """Read a float array from the GPIB device."""
    entries = query(command).split(',')
    n = int(entries[0])
    data = np.array([float(x.strip()) for x in entries[1:]])
    assert len(data) == n
    return data


def get_spectrum(trace: str):
    """Retrieves the specified trace from the OSA."""
    # Retrieve data
    print('Retrieving wavelengths (nm)...')
    wavelengths = read_array(f'WDAT{trace}')

    print('Retrieving levels (dBm)...')
    levels = read_array(f'LDAT{trace}')
    return wavelengths, levels


if __name__ == '__main__':
    open_connection(SERIAL_PORT, GPIB_ADDRESS)

    # Get sample spectrum from OSA
    wavelengths, levels = get_spectrum('A')

    # Plot data
    plt.plot(wavelengths, levels, label=f'Trace {trace}')
    plt.xlabel('Wavelength (nm)')
    plt.ylabel('Power (dBm)')
    plt.title(f'Ambient Spectrum')
    plt.show()

    ser.close()
