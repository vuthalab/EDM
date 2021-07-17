import time

from uncertainties import ufloat
import uncertainties.unumpy as unp

# Linear coefficients, from empirical fits
neon_coeff = ufloat(0.359, 0.010)  # microns/min/sccm
buffer_coeff = ufloat(0.060, 0.005) # microns/min/sccm

E_a = ufloat(19.94, 0.09) * 1e-3 # Neon binding energy, from literature (eV)
k_B = 1.381e-23 / 1.61e-19 # Boltzmann constant, eV/K
T_0 = ufloat(9.60, 0.03) # Temperature at which evaporation = 1 micron/min


class GrowthModel:
    def __init__(self):
        self.height = ufloat(0, 0) # microns
        self._last_update = time.monotonic()

    def update(self, neon_flow, buffer_flow, temperature):
        dt = (time.monotonic() - self._last_update)/60

        # Prevent drift
        if neon_flow.n < 0.2: neon_flow = 0
        if buffer_flow.n < 0.2: buffer_flow = 0

        # Update height (create new object to destroy correlations)
        self._growth_rate = self.growth_rate(neon_flow, buffer_flow, temperature)
        new_height = self.height + self._growth_rate * dt
        if new_height.n > 0:
            self.height = ufloat(new_height.n, new_height.s)
        else:
            self.reset()

        self._last_update = time.monotonic() - dt

    def reset(self):
        self.height = ufloat(0, 0)

    def growth_rate(self, neon_flow, buffer_flow, temperature):
        evaporation_rate = unp.exp(-E_a/k_B * (1/temperature - 1/T_0))
        return neon_coeff * neon_flow + buffer_coeff * buffer_flow - evaporation_rate
