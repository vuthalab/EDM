import time 
from collections import defaultdict

import numpy as np 

# Devices
from api.pump_laser import PumpLaser
from headers.ximea_camera import Ximea
from headers.qe_pro import QEProSpectrometer

from uncertainties import ufloat
from headers.util import unweighted_mean, nom




class FluorescenceSystem:
    def __init__(
        self, 
        pump_source: str = 'tisaph-low', # Excitation laser source.
        ximea_exposure: float = 10, # Ximea exposure (s)

        power_calibration_factor: float = 95.0/5.72 # Manually determined.
    ):
        """
        `pump_source`: Which pump laser to use for foreground expousures.
        `ximea_exposure`: Exposure time (s) for the Ximea camera.
        `power_calibration_factor`: Ratio of power onto crystal to power meter reading.
        """
        self.cam = Ximea(exposure = ximea_exposure)
        self.pump = PumpLaser()

        self.pump_source = pump_source
        self.power_calibration_factor = power_calibration_factor

        self._background = None


    def take_background(self, n_samples: int = 10) -> None:
        """Take background samples for later background-subtraction."""
        if self.pump.source is not None:
            self.pump.source = None
            time.sleep(3)

        self._background = self.take_samples(
            n_samples = n_samples,
            _is_background = True
        )


    def take_samples(
        self,
        n_samples: int = 3,
        _is_background: bool = False
    ):
        """
        Get fluorescence rate using Ximea.
        """

        if not _is_background and self._background is None:
            raise ValueError('You must call `FluorescenceSystem.take_background` first!')

        if self.pump.source is None and not _is_background:
            self.pump.source = self.pump_source
            time.sleep(3)

        rates = []
        powers = []

        for i in range(n_samples):
            print('Fluorescence sample', i, end='\r')
            self.cam.capture(fresh_sample=True)
            rates.append(self.cam.raw_rate)
            powers.append(self.pump.pm_power)
        print()

        rate = ufloat(np.median(rates), np.std(rates))
        power = unweighted_mean(powers) * self.power_calibration_factor

        if not _is_background:
            rate = rate - self._background['rate']
            power = power - self._background['power']

        print('Ximea rate:', 1e-6 * rate, 'Mcounts/s')
        print('Pump power:', power, 'mW')

        return {
            'rate': rate,
            'power': power,
        }
