"""
Header for EI-1050 Temperature + Humidity Probe.
"""

import time

try:
    from headers.usbtmc import USBTMCDevice
except:
    from usbtmc import USBTMCDevice

import uncertainties.unumpy as unp
from uncertainties import ufloat



def get_absolute_humidity(temperature, relative_humidity):
    """
    Compute the absolute humidity (g/m^3) from
    the temperature (°C) and relative humidity (%).
    """
    R = 0.08314 # gas constant
    return (
        6.112 * unp.exp(17.67 * temperature / (temperature + 243.5)) * (relative_humidity/100) * 18.02
        / ((273.15 + temperature) * R)
    )


class EI1050(USBTMCDevice):
    def __init__(self, multiplexer_port=31419):
        super().__init__(multiplexer_port, mode='multiplexed', name='EI1050 Temperature + Humidity Sensor')

    @property
    def temperature(self):
        """Return the temperature in °C."""
        response = self.query('READ_GENERIC SBUS11_TEMP 2')
        return ufloat(*map(float, response.split())) - 273.15

    @property
    def relative_humidity(self):
        """Return the relative humidity in percent."""
        response = self.query('READ_GENERIC SBUS11_RH 2')
        return ufloat(*map(float, response.split()))

    @property
    def absolute_humidity(self):
        """Return the absolute humidity in grams/m^3."""
        T = self.temperature
        RH = self.relative_humidity
        return get_absolute_humidity(T, RH)

if __name__ == '__main__':
    probe = EI1050()
