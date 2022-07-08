from headers.CTC100 import CTC100
from headers.mfc import MFC

from headers.edm_util import countdown_for, wait_until_quantity


class CrystalSystem():
    def __init__(self):
        self.T1 = CTC100(31415)
        self.mfc = MFC(31417)

        self.T1.ramp_temperature('heat saph', 4, 10)
        self.T1.enable_output()


    def _wait_for_temperature(self, direction: str, temperature: float):
        """
        Wait until a specific sapphire temperature is reached.

        `direction` must be `>` or `<`.
        """
        wait_until_quantity(
            ('temperatures', 'saph'),
            direction, temperature,
            unit='K', source='ctc'
        )

    def _ramp_temperature(self, target: float, speed: float):
        """Ramp the sapphire temperature to `target` K at `speed` K/s."""
        self.T1.ramp_temperature('heat saph', target, speed)


    @property
    def temperature(self) -> float:
        return self.T1.read('saph')

    @temperature.setter
    def temperature(self, temp: float) -> None:
        self._ramp_temperature(temp, 0.2)
        self._wait_for_temperature('<', temp + 0.02)
        self._wait_for_temperature('>', temp - 0.02)


    def melt(
        self,
        melt_temp: float = 25,
        melt_time: float = 120,
        end_temp: float = 10,
        speed: float = 0.1
    ):
        """
        Melt the crystal at `melt_temp` for `melt_time` seconds,
        then lower the temperature to `end_temp`.
        Temperature is ramped up and down at `speed` K/s.
        """

        # Raise saph temperature
        print('Melting crystal.')
        self._ramp_temperature(melt_temp, speed)
        self._wait_for_temperature('>', melt_temp - 0.1)

        # Ensure crystal is melted
        countdown_for(melt_time)

        # Cool down to end temperature.
        print('Cooling crystal.')
        self._ramp_temperature(end_temp, speed)
        self._wait_for_temperature('<', end_temp + 0.05)


    def anneal(self, anneal_temp: float = 9, duration: float = 30):
        """
        Anneal a few layers of the crystal, slowly lowering the temperature to `anneal_temp`.
        Then continue slow growth at this temperature for `duration` seconds.
        Assumes that starting temperature is above sublimation point.
        """

        # Anneal first few layers at low flow rate.
        print('Annealing first few layers.')
        self.mfc.flow_rate_cell = 1
        self._ramp_temperature(anneal_temp, 0.02)
        self._wait_for_temperature('<', anneal_temp + 0.1)

        # Grow a few layers at 9K.
        countdown_for(duration)


    def grow(self, temperature: float = 4.8, flow_rate: float = 20):
        """
        Grows a crystal at the specified temperature and flow rate.
        Does not automatically melt or anneal the crystal, or shutoff growth.
        """

        # Cool down to temp slowly.
        self._ramp_temperature(temperature, 0.1)
        self.mfc.off()
        self._wait_for_temperature('<', temperature + 0.05)
        self._wait_for_temperature('>', temperature - 0.05)

        # Begin growth.
        print(f'Growing crystal at {flow_rate:.2f} sccm, {temperature:.2f} K.')
        self.mfc.flow_rate_cell = flow_rate


    def stop(self, base_temperature: float = 4.8):
        """
        Immediately stop crystal growth and lower temperature to `base_temperature` K.
        """
        self.mfc.off()
        self._ramp_temperature(base_temperature, 10)
        self._wait_for_temperature('<', base_temperature + 0.05)
        self._wait_for_temperature('>', base_temperature - 0.05)
