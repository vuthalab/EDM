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
PROBE_PACKET = (
    b'\xc1\xc0\x00\x00\x00\x00\x00\x00\x80\x09\x10\x00\x00\x00'
    + b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x04\x01\x00\x00\x00\x00\x00'
    + b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x14\x00\x00\x00\x00\x00'
    + b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xc5\xc4'
    + b'\xc3\xc2'
)
INTEGRATION_HEADER = (
    b'\xc1\xc0\x00\x00\x04\x00\x00\x00\x10\x00\x11\x00\x00\x00\x00\x00'
    + b'\x00\x00\x00\x00\x00\x00\x00\x04'
)
INTEGRATION_FOOTER = (
    b'\x00\x00\x00\x00\x00\x00'
    + b'\x00\x00\x00\x00\x00\x00\x00\x00\x14\x00\x00\x00\x00\x00\x00\x00'
    + b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xc5\xc4\xc3\xc2'
)

SPECTRUM_LENGTH = 2136

OCEANFX_WAVELENGTHS, SYSTEMATIC_BACKGROUND, _ = np.loadtxt('calibration/systematic-background.txt').T

HENE_MASK = (OCEANFX_WAVELENGTHS < 610) | (OCEANFX_WAVELENGTHS > 650)


# Utilities for fitting surface roughness
ior = 1.23
rayleigh_constant = 2/3 * np.pi**5 * np.square((ior*ior-1)/(ior*ior+2))
def roughness_model(
        wavelength, # nm
        I0,
        roughness, # nm
#        rayleigh_strength, # nm^3 * micron
    ):
    wavenumber = 2*np.pi/wavelength
    theta = 45 * np.pi/180
    delta_n = ior - 1

    roughness_factor = np.exp(-0.5 * np.square(wavenumber * roughness * delta_n * np.cos(theta)))
#    rayleigh_factor = np.exp(-1e3 * rayleigh_strength * wavenumber**4 * rayleigh_constant)
    return I0 * roughness_factor


def fit_roughness(wavelengths, transmission):
    y = nominal_values(transmission)
    y_err = std_devs(transmission)
    popt, pcov = curve_fit(
        roughness_model,
        wavelengths,
        y, sigma=y_err,
        p0=[100, 1e3],
        bounds=[
            (0, 0),
            (200, 5e3)
        ]
    )
    return [
        ufloat(popt[0], np.sqrt(pcov[0][0])),
        ufloat(popt[1], np.sqrt(pcov[1][1]))
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


    def load_calibration(self):
        self.background = uarray(*np.loadtxt('calibration/background.txt'))
        self.baseline = uarray(*np.loadtxt('calibration/baseline.txt'))
        self.baseline -= self.background
    
    def close(self):
        if self.sock is not None:
            self.sock.close()

    def capture(self, n_samples = 256, time_limit = None):
        if self.sock is None: return

        try:
            self.load_calibration()
        except:
            pass

        # Average some spectra
        start_time = time.monotonic()
        spectrum = np.zeros((n_samples, SPECTRUM_LENGTH), dtype=float)
        for i in range(n_samples):
            # Get spectra until we get a stable one (full integration time)
            while True:
                # Send the same 64 data bytes from packet capture
                self.sock.send(PROBE_PACKET)

                # Get the response. Read packets until we have 4404 bytes.
                data = b''
                while len(data) < 4404: data += self.sock.recv(8192)

                # Decode from little-endian 16-byte unsigned int,
                # and discard metadata.
                sample = np.frombuffer(data, dtype=np.uint16)

                # Set integration time if valid spectrum
                canary, integration_time = sample[29:31]
                if canary == 5: break

            raw_spectrum = sample[54:2190]
            spectrum[i] = (raw_spectrum  - SYSTEMATIC_BACKGROUND) / integration_time
            saturation = max(raw_spectrum[HENE_MASK])

#            spectrum[i] = raw_spectrum * 100/65536 # legacy, delete this line soon.

            if i % 200 == 0 and i > 0:
                print(f'{i}/{n_samples}')

            if time_limit is not None and time.monotonic() - start_time > time_limit:
                spectrum = spectrum[:i+1]
                break

        # Return mean + std
        self._cache = uarray(spectrum.mean(axis=0), spectrum.std(axis=0))
        self._raw_cache = self._cache * integration_time + SYSTEMATIC_BACKGROUND

        # Auto-set integration time to get good dynamic range
        target = integration_time * 50000/saturation
        target = round(max(min(target, 20000), 50))
        if self.integration_time != target: self.integration_time = target


    @property
    def integration_time(self) -> int:
        return self._integration_time

    @integration_time.setter
    def integration_time(self, val: int):
        """Sets the integration time, in microseconds."""
        packet = (
            INTEGRATION_HEADER
            + val.to_bytes(2, byteorder='little')
            + INTEGRATION_FOOTER
        )
        print(f'  [{Fore.RED}SEND{Style.RESET_ALL}] Setting OceanFX integration time to {val} μs')
        self.sock.send(packet)
        self._integration_time = val
        

    @property
    def wavelengths(self):
        # Taken from an OceanFX save file
        return OCEANFX_WAVELENGTHS

    @property
    def intensities(self):
        if self._cache is None: self.capture()
        return self._cache

    @property
    def raw_intensities(self): return self._raw_cache

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
    def optical_density(self):
        """Return the optical density at each wavelength."""
        return -np.log10(transmission/100)

    @property
    def roughness_full(self):
        """Return the estimated roughness and unexplained overall transmission of a transmissive surface."""
        if self.sock is None: return (None, None)

        wavelengths = self.wavelengths
        mask = ((wavelengths > 430) & (wavelengths < 600)) | ((wavelengths > 750) & (wavelengths < 900))
#        mask = (wavelengths > 430) & (wavelengths < 600)

        try:
            I0, roughness = fit_roughness(self.wavelengths[mask], self.transmission[mask])
        except Exception as e:
            print(e)
            I0, roughness = self.transmission_scalar, ufloat(0, 0)

        max_transmission = max(nominal_values(self.transmission[mask]))
        if roughness.s > roughness.n or max_transmission < 3 or I0.n < 0:
            I0, roughness = self.transmission_scalar, ufloat(0, 0)
        return I0, roughness

    @property
    def roughness(self):
        """Return the estimated roughness of a transmissive surface."""
        return self.roughness_full[1]
