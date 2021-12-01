import numpy as np

from uncertainties import ufloat
from uncertainties.umath import sqrt, asin, sin

base_wavelength = ufloat(900.25, 0.24)
ior = ufloat(2.024, 0.008)

def target_angle(target_wavelength):
    try:
        return asin(ior * sqrt(1 - (target_wavelength / base_wavelength)**2)) * 180/np.pi
    except:
        return ufloat(0, 0.1)

def target_wavelength(target_angle):
    return base_wavelength * sqrt(1 - (sin(target_angle*np.pi/180)/ior)**2)
