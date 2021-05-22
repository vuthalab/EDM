"""
Header file for the Ocean Optics OceanFX spectrometer.

At the moment, only reads spectra.
Integration time must be set to 250 us manually
using the OceanView software.
"""

import socket

import numpy as np


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
background = np.loadtxt('spectra/background.txt')
baseline = np.loadtxt('spectra/baseline.txt')
baseline -= background

class OceanFX:
    def __init__(self, ip_addr: str = '192.168.0.100', port: int = 57357):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((ip_addr, port))

    @property
    def wavelengths(self):
        # Hard-coded, but proabably good enough for now.
        return np.linspace(318.408, 1015.653, SPECTRUM_LENGTH)

    @property
    def intensities(self):
        spectrum = np.zeros(SPECTRUM_LENGTH, dtype=float)
        N_AVERAGE = 128

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
            spectrum += sample

        # Compute average and scale to [0, 100]
        spectrum *= 100/(65536 * N_AVERAGE)
        return spectrum

    @property
    def transmission(self):
        """Return the transmission (in percent) at each wavelength."""
        return 100 * (self.intensities - background) / baseline

    @property
    def optical_density(self):
        """Return the optical density at each wavelength."""
        return -np.log10(transmission/100)
