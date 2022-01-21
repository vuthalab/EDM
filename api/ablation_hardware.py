import time

import numpy as np

from colorama import Fore, Style

from uncertainties import ufloat

from headers.zmq_client_socket import connect_to
from headers.util import display

from headers.rigol_ds1102e import RigolDS1102e
from headers.mirror_mount import microcontroller
from headers.rigol_dg4162 import RigolDG4162


def moving_average(a, n=3) :
    ret = np.cumsum(a, dtype=float)
    ret[n:] = ret[n:] - ret[:-n]
    return ret[n - 1:] / n


x_calibration = -0.01858 # pixels per mirror step
y_calibration =  0.01871 # pixels per mirror step

class AblationHardware:
    """Class for managing ablation with the Nd:YAG laser."""


    def __init__(self, mirror_speed=1000):
        self.scope = RigolDS1102e('/dev/absorption_scope')
        self.mirror = microcontroller()
        self.fg = RigolDG4162()

        # Set mirror speeds
        self.mirror.set_speed(1, mirror_speed)
        self.mirror.set_speed(2, mirror_speed)
        self._mirror_speed = mirror_speed
        self._delay_buffer = 0.2

        self._plume_camera = connect_to('plume-cam')
        self._cache = None

    def _update_cache(self):
        while True:
            _, data = self._plume_camera.grab_json_data()
            if data is not None: self._cache = data
            if data is None and self._cache is not None: break

    def _monitor_move(self, motor, steps):
        """
        Move mirror motor for given number of steps.
        Monitor the spot intensity to make sure it does not disappear.
        """
        if abs(steps) > 20000: raise ValueError

        duration = abs(steps)/self._mirror_speed + self._delay_buffer

        self.mirror.move(motor, steps)

        start_time = time.monotonic()
        while time.monotonic() < start_time + duration:
            intensity = self.hene_intensity
            print(f'Moving mirror motor {motor} for {steps} steps. Intensity: {intensity:.3f}', end='\r')
            time.sleep(0.2)

        if intensity < 20:
            print('Spot disappeared, retracing.')
            self.mirror.move(motor, -steps)
            time.sleep(duration)
            raise ValueError('Spot disappeared!')
        print()

    @property
    def _delay(self):
        """Returns the delay of the current cache contents."""
        return time.time() - self._cache['timestamp']

    ##### Public API #####
    @property
    def is_on(self): return self.fg.enabled
    def on(self):
        self.fg.enabled = True
        print(f'{Fore.RED}##### ABLATION ON #####{Style.RESET_ALL}')

    def off(self):
        self.fg.enabled = False
        print(f'{Fore.RED}##### ABLATION OFF #####{Style.RESET_ALL}')


    @property
    def position(self):
        """Returns the XY position of the ablation target, in pixel space on the camera."""
        self._update_cache()
        center = self._cache['center']
        return (ufloat(*center['x']), ufloat(*center['y']))

    @position.setter
    def position(self, xy):
        """Sets the XY position of the ablation target, in pixel space on the camera."""
        xp, yp = xy
        assert 0 < xp < 1440
        assert 0 < yp < 1080 

        x, y = self.position
        dx, dy = xp - x.n, yp - y.n

        dx_steps = round(dx/x_calibration)
        dy_steps = round(dy/y_calibration)

        self._monitor_move(2, dx_steps)
        self._monitor_move(1, dy_steps)

    @property
    def frequency(self):
        """Returns the ablation frequency."""
        return self.fg.frequency

    @frequency.setter
    def frequency(self, value):
        """Sets the ablation frequency."""
        self.fg.frequency = value

    @property
    def hene_intensity(self):
        """Returns the intensity of the HeNe spot on the camera. Arbitrary units."""
        self._update_cache()
        return self._cache['intensity']

    @property
    def trace(self):
        """
        Return the absorption trace.
        Depending on how the scope in configured, may involve adding together multiple channels (AC/DC coupled).
        """
        self.scope.active_channel = 1
        trace = self.scope.trace
        self.scope.active_channel = 2
        trace2 = self.scope.trace
        return trace + trace2.mean()

    @property
    def dip_size(self):
        """Return the size of the ablation dip, in percent."""
        trace = self.trace
        trace = moving_average(trace, 7)
        baseline = np.percentile(trace, 95)
        dip = np.min(trace)
        return 100 * (1 - dip/baseline)
