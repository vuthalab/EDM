"""
Header file for the Ocean Optics OceanFX spectrometer.

At the moment, only reads spectra.
Integration time must be set to 200 us manually
using the OceanView software.
"""

import socket

import numpy as np
from scipy.optimize import curve_fit

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
SPECTRUM_LENGTH = 2136


# Load previously recorded background and baseline
background = uarray(*np.loadtxt('spectra/background.txt'))
baseline = uarray(*np.loadtxt('spectra/baseline.txt'))
baseline -= background


# Utilities for fitting surface roughness
def roughness_model(wavelength, I0, roughness):
    wavenumber = 2*np.pi/wavelength
    theta = 45 * np.pi/180
    delta_n = 0.1
    return I0 * np.exp(-0.5 * np.square(wavenumber * roughness * delta_n * np.cos(theta)))

def fit_roughness(wavelengths, transmission):
    y = nominal_values(transmission)
    y_err = std_devs(transmission)
    popt, pcov = curve_fit(
        roughness_model,
        wavelengths,
        y, sigma=y_err,
        p0=[100, 100]
    )
    return (
        ufloat(popt[0], np.sqrt(pcov[0][0])),
        ufloat(popt[1], np.sqrt(pcov[1][1])),
    )


class OceanFX:
    def __init__(self, ip_addr: str = '192.168.0.100', port: int = 57357):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(1)
        self.sock.connect((ip_addr, port))

        self.cache = None
    
    def close(self):
        self.sock.close()

    def capture(self):
        N_AVERAGE = 128
        spectrum = np.zeros((N_AVERAGE, SPECTRUM_LENGTH), dtype=float)

        # Average 128 spectra
        for i in range(N_AVERAGE):
            # Send the same 64 data bytes from packet capture
            self.sock.send(PROBE_PACKET)

            # Get the response. Read packets until we have 4404 bytes.
            data = b''
            while len(data) < 4404: data += self.sock.recv(8192)

            # Decode from little-endian 16-byte unsigned int,
            # and discard metadata.
            sample = np.frombuffer(data, dtype=np.uint16)[54:2190]
            spectrum[i] = sample

        # Scale to [0, 100]
        spectrum *= 100/65536

        # Return mean + std
        self.cache = uarray(spectrum.mean(axis=0), spectrum.std(axis=0))

    @property
    def wavelengths(self):
        # Hard-coded, but proabably good enough for now.
        return np.linspace(318.408, 1015.653, SPECTRUM_LENGTH)

    @property
    def intensities(self):
        if self.cache is None: self.capture()
        return self.cache

    @property
    def transmission(self):
        """Return the transmission (in percent) at each wavelength."""
        return 100 * (self.intensities - background) / baseline

    @property
    def transmission_scalar(self):
        """Return the overall percent transmission."""
        return 100 * (self.intensities - background).sum() / baseline.sum()

    @property
    def optical_density(self):
        """Return the optical density at each wavelength."""
        return -np.log10(transmission/100)

    @property
    def roughness_full(self):
        """Return the estimated roughness and unexplained overall transmission of a transmissive surface."""
        wavelengths = self.wavelengths
        mask = (wavelengths > 450) & (wavelengths < 750)

        try:
            I0, roughness = fit_roughness(self.wavelengths[mask], self.transmission[mask])
        except Exception as e:
            print(e)
            I0, roughness = self.transmission_scalar, ufloat(0, 0)

        max_transmission = max(nominal_values(self.transmission[mask]))
        if roughness.s > roughness.n or max_transmission < 20:
            I0, roughness = self.transmission_scalar, ufloat(0, 0)
        return I0, roughness

    @property
    def roughness(self):
        """Return the estimated roughness of a transmissive surface."""
        return self.roughness_full[1]