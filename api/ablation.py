import time
import numpy as np

from headers.mfc import MFC
from headers.wavemeter import WM
from api.ablation_hardware import AblationHardware

# Auxiliary functions
center = np.array([780, 560]) # Center of target (pixels) on camera
RADIUS = 100 # radius (pixels) of target on camera

def spiral(n):
    """Given an integer n, returns the location n steps along a spiral pattern out from the center."""
    assert n >= 0
    theta = 3 * np.sqrt(n) # radians
    r = theta * 1.0 # pixels
    return center + r * np.array([np.cos(theta), np.sin(theta)])


class AblationSystem:
    def __init__(
        self,
        start_position=0, # Index of start position in spiral
        move_threshold = 0.2, # Dip size (%) below which to move to next spot
        frequency = 15,
    ):
        self.hardware = AblationHardware()
        self.hardware.frequency = frequency

        self.position = start_position
        self.threshold = move_threshold

        # Safety interlock devices
        self.wm = WM()
        self.mfc = MFC(31417)

    def _check_interlocks(self):
        baf_freq = self.wm.read_frequency(8)

        try:
            assert self.hardware.hene_intensity > 20
            assert self.mfc.flow_rate_cell > 2
            assert baf_freq is None or abs(baf_freq - 348676.3) < 0.05
        except Exception as e:
            self.off()
            raise ValueError(e)

    ##### Public API #####
    def on(self):
        self._check_interlocks()
        self.hardware.on()

    def off(self):
        self.hardware.off()

    def ablate_until_depleted(self):
        """
        Ablate the current position in spiral until absorption threshold is reached.

        Returns a generator yielding information about ablation.
        """
        print(f'Ablating at position {self.position} in spiral.')
        self.hardware.position = spiral(self.position)
        while True:
            self._check_interlocks()
            dip_size = self.hardware.dip_size
            pos = self.hardware.position

            if not self.hardware.is_on: break
            if dip_size < self.threshold: break
            yield (self.position, pos, dip_size)
            time.sleep(0.25)

    def ablate_continuously(self):
        """
        Run ablation until stopped.

        Returns a generator yielding information about ablation.
        """
        while True:
            for update in self.ablate_until_depleted():
                yield update

            if not self.hardware.is_on: break
            self.position += 1

