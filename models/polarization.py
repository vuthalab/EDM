import numpy as np

from uncertainties import ufloat
from uncertainties.umath import sqrt, atan2


base_1 = ufloat(0.993, 0.003) # Sensitivity of PD 1 @ 830 nm
base_2 = ufloat(1.602, 0.005) # Sensitivity of PD 2 @ 830 nm

slope_1 = ufloat(-1.81, 0.06) * 1e-3 # Slope of sensitivity of PD 1 w.r.t. wavelength
slope_2 = ufloat(-2.28, 0.10) * 1e-3 # Slope of sensitivity of PD 1 w.r.t. wavelength

bg_1 = ufloat(-0.102, 0.012) # Background voltage of PD 1
bg_2 = ufloat(-0.118, 0.012) # Background voltage of PD 2

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

bias_curvature = ufloat(-1.48, 0.19) * 1e-5 # V/nm^2
bias_slope = ufloat(-1.02, 0.08) * 1e-3 # V/nm
bias_intercept = ufloat(0.173, 0.007) # V

def eom_responsivity_and_bias(wl):
    z = wl - 830
    responsivity = z * responsivity_slope + responsivity_intercept
    bias = bias_curvature * z * z + bias_slope * z + bias_intercept
    return responsivity, bias

def eom_angle_from_gain(gain, wl):
    """
    Return the EOM twist angle, in degrees,
    for the given gain voltage (V) at the given wavelength (nm).
    """
    responsivity, bias = eom_responsivity_and_bias(wl)
    return responsivity * (gain - bias)

def eom_gain_from_angle(angle, wl):
    """
    Return the EOM gain voltage (V)
    required to obtain the desired twist angle (degrees)
    at the given wavelength (nm).
    """
    responsivity, bias = eom_responsivity_and_bias(wl)
    return angle/responsivity + bias
