import numpy as np

from uncertainties import ufloat
from uncertainties.umath import sqrt, atan2

from headers.util import nom


bg_1 = ufloat(-0.102, 0.006) # Background voltage of PD 1
bg_2 = ufloat(-0.119, 0.006) # Background voltage of PD 2

# PD Sensitivity Calibration
cal_wl, cal_sens_1, cal_sens_2 = np.loadtxt('calibration/pd_coefficients.txt').T

def power_and_polarization(v1_raw, v2_raw, wl):
    """
    Estimate the vertical + horizontal components of the output power (mW)
    and polarization angle (deg) of the beam leaving the EOM,
    given voltages from both photodiodes.
    """
    v1 = v1_raw - bg_1
    v2 = v2_raw - bg_2

    sens_1 = np.interp(nom(wl), cal_wl, cal_sens_1)
    sens_2 = np.interp(nom(wl), cal_wl, cal_sens_2)

    power_1 = v1 * sens_1
    power_2 = v2 * sens_2

    ampl_1 = sqrt(power_1) if power_1.n > 0 else ufloat(0, 0)
    ampl_2 = sqrt(power_2) if power_2.n > 0 else ufloat(0, 0)

    angle = atan2(ampl_1, ampl_2) * 180/np.pi

    return power_1, power_2, angle


# EOM Response Characteristics
responsivity_slope = ufloat(-0.0164, 0.0002) # degrees/V/nm
responsivity_intercept = ufloat(11.045, 0.011) # degrees/V

bias_curvature = ufloat(-1.31, 0.10) * 1e-5 # V/nm^2
bias_slope = ufloat(-1.25, 0.04) * 1e-3 # V/nm
bias_intercept = ufloat(0.096, 0.002) # V

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
