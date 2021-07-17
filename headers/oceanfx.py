"""
Header file for the Ocean Optics OceanFX spectrometer.

At the moment, only reads spectra.
Integration time must be set to 200 us manually
using the OceanView software.
"""

import socket, time

import numpy as np
from scipy.optimize import curve_fit

from colorama import Fore, Style

from uncertainties import ufloat
from uncertainties.unumpy import uarray, nominal_values, std_devs


# Dumped from packet capture
def pad_packet(message_type, content):
    return (
        b'\xc1\xc0' # Constant start bytes
        + b'\x00\x00' # Protocol Version
        + b'\x00\x00' # Flags
        + b'\x00\x00' # Error number
        + message_type
        + b'\x00\x00\x00\x00' # Request ID (will be echoed back)
        + b'\x00\x00\x00\x00\x00\x00' # Useless, reserved
        + b'\x00' # Checksum type (useless)
        + content
        + b'\x14\x00\x00\x00\x00\x00' # Bytes remaining (incl. checksum + footer)
        + b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' # Checksum
        + b'\xc5\xc4\xc3\xc2' # Footer
    )

FLAGS = [
    'Response',
    'ACK',
    'ACK Request',
    'NACK',
    'Exception',
    'Deprecated Protocol',
    'Deprecated Message'
]
def parse_packet(packet):
    flag = FLAGS[int(packet[4])]
    error = int.from_bytes(packet[6:8], byteorder='little')
    msg_type = packet[8:12]

    immediate_data_length = int(packet[23])
    immediate_data = packet[24:24 + immediate_data_length]

    payload_length = int.from_bytes(packet[40:44], byteorder='little') - 20
    payload = packet[44:44 + payload_length]
    return {
        'flag': flag,
        'error': error,
        'type': msg_type,
        'immediate': immediate_data,
        'payload': payload
    }


INTEGRATION_MESSAGE_TYPE = b'\x10\x00\x11\x00'
RESET_PACKET = pad_packet(
    b'\x00\x00\x00\x00',
    b'\x00' # Length of immediate data
    + b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' # Immediate data
)




SPECTRUM_LENGTH = 2136
OCEANFX_WAVELENGTHS = np.loadtxt('calibration/wavelengths.txt')
HENE_MASK = (OCEANFX_WAVELENGTHS < 630) | (OCEANFX_WAVELENGTHS > 634)


# Utilities for fitting surface roughness
ior = 1.23
def roughness_model(
        wavelength, # nm
        I0,
        roughness, # nm
        fourth_order_coefficient, # nm^3 * micron
    ):
    wavenumber = 2*np.pi/wavelength
    theta = np.arcsin(np.sin(45*np.pi/180) * ior)

    delta_n = ior - 1
    effective_roughness = roughness * np.cos(theta)

    roughness_factor = np.exp(-0.5 * np.square(wavenumber * effective_roughness * delta_n))
    fourth_order_factor = np.exp(-1e3 * fourth_order_coefficient * wavenumber**4)
    return I0 * roughness_factor * fourth_order_factor


def fit_roughness(wavelengths, transmission):
    y = nominal_values(transmission)
    y_err = std_devs(transmission)
    popt, pcov = curve_fit(
        roughness_model,
        wavelengths,
        y, sigma=y_err,
        p0=[100, 1e3, 0],
        bounds=[
            (0, 0, -1e6),
            (200, 5e3, 1e6)
        ]
    )
    perr = np.sqrt(np.diag(pcov))

    y_pred = roughness_model(wavelengths, *popt)
    chisq = np.square((y - y_pred) / y_err).sum()
    dof = len(y) - len(popt)

    return [
        ufloat(popt[0], perr[0]),
        ufloat(abs(popt[1]), perr[0]),
        ufloat(popt[2], perr[2]),
        chisq/dof,
    ]


class OceanFX:
    def __init__(self, ip_addr: str = '192.168.0.100', port: int = 57357):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(1)

        try:
            self.sock.connect((ip_addr, port))
        except:
            print(f'  [{Fore.YELLOW}WARN{Style.RESET_ALL}] OceanFX failed to connect!')
            self.sock = None

        self._cache = None
        self._integration_time = None
        self.load_calibration()

        # Disable buffering
#        self.send(b'\x10\x08\x10\x00', 0, data_length=1)


    def load_calibration(self):
        self.background = uarray(*np.loadtxt('calibration/background.txt'))
        self.baseline = uarray(*np.loadtxt('calibration/baseline.txt'))
        self.baseline -= self.background
    
    def close(self):
        if self.sock is not None:
            self.sock.close()

    def reset(self): self.sock.send(RESET_PACKET)

    def ping(self):
        self.send(b'\x01\xF1\x0F\x00', 31415)
        return parse_packet(self.sock.recv(8192))

    def send(self, message_type, data, data_length=4):
        self.sock.send(pad_packet(
            message_type,
            data_length.to_bytes(1, byteorder='little')
            + int(data).to_bytes(16, byteorder='little')
        ))

    def set_averaging(self, n_scans: int):
        """Set the OceanFX to internally average `n_scans` scans for each returned spectra."""
        self.send(b'\x10\x00\x12\x00', n_scans, data_length=2)


    def _capture_sample(self):
        # Get 5 spectra (up to 15)
        self.send(b'\x80\x09\x10\x00', 5)

        # Get the response. Read packets until the checksum.
        data = b''
        while not data.endswith(b'\xc5\xc4\xc3\xc2'):
            data += self.sock.recv(8192)
        data = parse_packet(data)

        # Check if spectrum is valid
        error = data['error']
        if error != 0:
            self.reset()
            raise RuntimeError(f'OceanFX in error state {error}')

        payload = data['payload']
        segment_length = 64 + 2 * SPECTRUM_LENGTH + 4
        n_spectra, checksum = divmod(len(payload), segment_length)
        if checksum != 0:
            raise RuntimeError('Invalid packet length!')

        # Extract metadata, then decode
        # from little-endian 16-byte unsigned int.
        integration_times = []
        samples = []
        for i in range(n_spectra):
            segment = payload[segment_length*i : segment_length*(i+1)]
            metadata = segment[:64]
            sample = np.frombuffer(segment[64:-4], dtype=np.uint16)

            # Extract spectrum length and integration time.
            spectrum_length = int.from_bytes(metadata[4:8], byteorder='little')
            integration_time = int.from_bytes(metadata[16:20], byteorder='little')

            # Return if spectrum has expected length.
            if spectrum_length == 2 * SPECTRUM_LENGTH:
                integration_times.append(integration_time)
                samples.append(sample)

        return integration_times, samples


    def _capture_samples(self, integration_time, time_limit=0.2):
        self._set_integration_time(integration_time)

        # Average some spectra
        start_time = time.monotonic()
        samples = []
        while True:
            for sample_integration_time, spectrum in zip(*self._capture_sample()):
                if integration_time != sample_integration_time: continue
                samples.append(spectrum)
            if time.monotonic() - start_time > time_limit: break

        samples = np.array(samples)

        # Return mean + std
        print(f'  [{Fore.BLUE}INFO{Style.RESET_ALL}] {Style.DIM}Captured{Style.RESET_ALL} {Style.BRIGHT}{len(samples)}{Style.RESET_ALL} {Style.DIM}spectra at{Style.RESET_ALL} {Style.BRIGHT}{integration_time}{Style.RESET_ALL} {Style.DIM}μs exposure.{Style.RESET_ALL}')
        return uarray(samples.mean(axis=0), samples.std(axis=0, ddof=1))


    def capture(self, time_limit = 1):
        if self.sock is None: return

        try:
            self.load_calibration()
        except:
            pass

        self.set_averaging(1)


        # Capture over a range of integration times.
        log_integration_times = np.linspace(1.3, 5, 40)
        log_integration_times += np.random.uniform(-0.02, 0.02, 40)
        integration_times = np.array([
            10, 11, 12, 13, # Make sure to get hene properly exposed
            *np.power(10, log_integration_times)
        ], dtype=int)

        # Randomize
        np.random.shuffle(integration_times)

        samples = []
        for integration_time in integration_times:
            sample = self._capture_samples(
                integration_time,
                time_limit/len(integration_times)
            )
            samples.append(sample)
        samples = np.array(samples).T

        # Fit a linear slope at each wavelength, excluding saturated spectra.
        points = []
        intercepts = []
        slopes = []
        curvature = []
        for i in range(SPECTRUM_LENGTH):
            y = samples[i]
            mask = (nominal_values(y) + 2 * std_devs(y)) < 64000
            y = y[mask]
            x = integration_times[mask]

            if len(y) < 5:
                print(f'Saturated at {OCEANFX_WAVELENGTHS[i]:.2f} nm! Only {len(y)} valid points')

            degree = 2 if i in HENE_MASK else 1
            try:
                popt, pcov = np.polyfit(
                    x, nominal_values(y), degree,
                    w=1/np.maximum(std_devs(y), 20),
                    cov=True
                )
                perr = np.sqrt(np.diag(pcov))
                perr[np.isinf(perr)] = 10
            except:
                popt = [0, 1000]
                perr= [1000, 1000]

            points.append(len(y))
            intercepts.append(ufloat(popt[-1], perr[-1]))
            slopes.append(ufloat(popt[-2], perr[-2]))
#            curvature.append(ufloat(popt[-3], perr[-3]))


        # Return mean + std slopes
        self._cache = np.array(slopes)
        self._intercepts = np.array(intercepts)
#        self._curvature = np.array(curvature)
        self._points = np.array(points)


    def _set_integration_time(self, val: int):
        """Sets the integration time, in microseconds."""
        assert val >= 10
        assert val <= 1e6
        self.send(b'\x10\x00\x11\x00', round(val))
        

    @property
    def wavelengths(self):
        # Taken from an OceanFX save file
        return OCEANFX_WAVELENGTHS


    @property
    def intensities(self):
        if self._cache is None: self.capture()
        return self._cache


    @property
    def transmission(self):
        """Return the transmission (in percent) at each wavelength."""
        return 100 * (self.intensities - self.background) / self.baseline


    @property
    def transmission_scalar(self):
        """Return the overall percent transmission."""
        if self.sock is None: return None

        return 100 * (self.intensities - self.background).sum() / self.baseline.sum()


    @property
    def roughness_full(self):
        """Return the estimated roughness and unexplained overall transmission of a transmissive surface."""
        if self.sock is None: return (None, None)

        wavelengths = self.wavelengths
        mask = (
            (wavelengths > 440) & (wavelengths < 620)
#            | (wavelengths > 640) & (wavelengths < 680)
            | (wavelengths > 780) & (wavelengths < 870)
        )
#        mask = (wavelengths > 430) & (wavelengths < 600)

        try:
            return fit_roughness(self.wavelengths[mask], self.transmission[mask])
        except Exception as e:
            print(e)
            return self.transmission_scalar, ufloat(0, 0), ufloat(0, 0), None


    @property
    def roughness(self):
        """Return the estimated roughness of a transmissive surface."""
        return self.roughness_full[1]
