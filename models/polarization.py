import numpy as np

from uncertainties import ufloat
from uncertainties.umath import sqrt, atan2


base_1 = ufloat(1.4495, 0.0016) # Sensitivity of PD 1 @ 860 nm
base_2 = ufloat(2.3037, 0.0011) # Sensitivity of PD 2 @ 860 nm

slope_1 = ufloat(-1.82, 0.08) * 1e-3 # Slope of sensitivity of PD 1 w.r.t. wavelength
slope_2 = ufloat(-3.46, 0.05) * 1e-3 # Slope of sensitivity of PD 1 w.r.t. wavelength

bg_1 = ufloat(-0.0853, 0.0032) # Background voltage of PD 1
bg_2 = ufloat(-0.0947, 0.0032) # Background voltage of PD 2

def power_and_polarization(v1_raw, v2_raw, wl):
    """
    Estimate the vertical + horizontal components of the output power (mW)
    and polarization angle (deg) of the beam leaving the EOM,
    given voltages from both photodiodes.
    """
    v1 = v1_raw - bg_1
    v2 = v2_raw - bg_2

    sens_1 = slope_1 * (wl - 860) + base_1
    sens_2 = slope_2 * (wl - 860) + base_2

    power_1 = v1 * sens_1
    power_2 = v2 * sens_2

    ampl_1 = sqrt(power_1) if power_1.n > 0 else ufloat(0, 0)
    ampl_2 = sqrt(power_2) if power_2.n > 0 else ufloat(0, 0)

    angle = atan2(ampl_1, ampl_2) * 180/np.pi

    return power_1, power_2, angle


# EOM Response Characteristics
responsivity_slope = ufloat(-0.0143, 0.0003) # degrees/V/nm
responsivity_intercept = ufloat(10.258, 0.008) # degrees/V

bias_slope = ufloat(-0.0160, 0.0006) # degrees/nm
bias_intercept = ufloat(-1.521, 0.015) # degrees
def eom_angle_from_gain(gain, wl):
    """
    Return the EOM twist angle, in degrees,
    for the given gain voltage (V) at the given wavelength (nm).
    """
    x = wl - 860
    bias = x * bias_slope + bias_intercept
    responsivity = x * responsivity_slope + responsivity_intercept 
    return bias + responsivity * gain

def eom_gain_from_angle(angle, wl):
    """
    Return the EOM gain voltage (V)
    required to obtain the desired twist angle (degrees)
    at the given wavelength (nm).
    """
    x = wl - 860
    bias = x * bias_slope + bias_intercept
    responsivity = x * responsivity_slope + responsivity_intercept 
    return (angle - bias)/responsivity
