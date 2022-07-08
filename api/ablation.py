import time
import random
import numpy as np

from headers.mfc import MFC
from headers.wavemeter import WM
from api.ablation_hardware import AblationHardware

# CHANGE THIS CENTER POSITION PER RUN
center = np.array([648, 376]) # Center of target (pixels) on camera

def spiral(n):
    """Given an integer n, returns the location n steps along a spiral pattern out from the center."""
    assert n >= 0
#    theta = 3 * np.sqrt(n) # radians
#    r = theta * 1 # pixels

    theta = np.sqrt(n) # radians
    r = theta # pixels
    return center + r * np.array([np.cos(theta), np.sin(theta)])


class AblationSystem:
    def __init__(
        self,
        start_position=0, # Index of start position in spiral
        move_threshold = 0.6, # Dip size (%) below which to move to next spot
        frequency = 30,
    ):
        self.hardware = AblationHardware()
        self.hardware.frequency = frequency

        self.position = start_position
        self.threshold = move_threshold

        # Safety interlock devices
        self.wm = WM()
        self.mfc = MFC(31417)

        self.wm.set_baf()

    def _check_interlocks(self):
        # Set multiplexer to BaF channel
        baf_freq = self.wm.read_frequency(8)

        try:
            assert self.hardware.hene_intensity > 15
            if random.random() < 0.2:
                assert self.mfc.flow_rate_cell > 2
#            assert baf_freq is None or abs(baf_freq - 348676.3) < 0.05

            if baf_freq is None or abs(baf_freq - 348676.3) < 0.05:
                return True
            else:
                print(baf_freq)
                return False # TEMP

                if self.wm.get_external_output(8) < 1:
                    # Try to jiggle lock back into position
                    print('Fixing laser...')
                    self.wm.set_lock_setpoint(8, 380000)
                    time.sleep(5)
                    self.wm.set_lock_setpoint(8, 348676.3)
                    time.sleep(3)
        except Exception as e:
            self.off()
            raise ValueError(e)

        return False

    ##### Public API #####
    def on(self):
        self.wm.set_baf()
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
            dip_size = self.hardware.dip_size
            pos = self.hardware.position

            # TODO TEMP until laser is fixed
            if not self._check_interlocks():
                print('BaF laser unlocked!')
#                dip_size = np.random.uniform(0.195, 0.3)
                dip_size = 5
                if random.random() < 0.02: break

            if not self.hardware.is_on: break
            yield (self.position, pos, dip_size)
            if dip_size < self.threshold: break
            time.sleep(0.25)

    def ablate_continuously(self):
        """
        Run ablation continuously, rastering a spiral,
        until manually stopped.

        Returns a generator yielding information about ablation.
        Generator output is (timestamp, index_in_spiral, pixel_position, dip_size).
        """
        start_time = time.monotonic()
        while True:
            for update in self.ablate_until_depleted():
                ts = time.monotonic() - start_time
                n, pos, dip_size = update
                print(
                    f'{ts:7.3f} s',
                    f'{n:05d}',
                    f'({pos[0]:.3f}, {pos[1]:.3f}) pixels',
                    f'{dip_size:5.2f} % dip',
                    sep=' | ' 
                )
                yield (ts, *update)

            if not self.hardware.is_on: break
            self.position += 1
