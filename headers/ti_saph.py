import time

import matplotlib.pyplot as plt
import numpy as np
from uncertainties import ufloat, correlated_values

from headers.zmq_client_socket import connect_to

from headers.verdi import Verdi
from headers.rigol_dp832 import TiSaphMicrometer
from headers.wavemeter import WM

from headers.util import display, nom, std, fit, plot


# Parameters for mode analysis
mask_width = 20
window_width = 50


speed_of_light = 299792458 # GHz-nm



class TiSapphire:
    def __init__(self):
        self.verdi = Verdi()
        self.micrometer = TiSaphMicrometer()

        self.wm = WM()
        self.channel = 7

        self.last_direction = None


    def reset_backlash(self, direction):
        """Eats up the backlash in the system."""
        if direction != self.last_direction:
            self.micrometer.speed = direction * 100
            time.sleep(0.8)
            self.micrometer.off()

        self.last_direction = direction


    def step(
        self, direction,
        duration = 0.3, speed = 15,
        backoff = 0.1, cooldown = 0.2,
    ):
        """Perform a small step in the given direction."""
        self.reset_backlash(direction)
        try:
            self.micrometer.speed = direction * speed
            time.sleep(duration)
            self.micrometer.speed = -direction * speed
            time.sleep(backoff)
        finally: # To intercept KeyboardInterrupt
            self.micrometer.off()
            time.sleep(cooldown)

    @property
    def wavemeter_intensity(self) -> float:
        """Returns the intensity coupled into the wavemeter [uW]."""
        return self.wm.read_power(self.channel)

    @property
    def frequency(self) -> float:
        """Returns the frequency of the laser [GHz]."""
        return self.wm.read_frequency(self.channel)

    @property
    def wavelength(self) -> float:
        """Returns the vacuum wavelength of the laser [nm]."""
        return speed_of_light / self.frequency

    @wavelength.setter
    def wavelength(self, target):
        """Coarsely set the wavelength."""
        print(f'Setting wavelength to {target:.3f} nm...')

        current = self.wavelength
        print(f'Starting wavelength is {current:.3f} nm.')

        direction = -1 if (current > target) else 1

        while True:
            self.step(direction, duration=0.8, speed=30)
            current = self.wavelength

            # Stop when target reached
            delta = direction * (target - current)
            if delta < 0: break

            print(f'Target: {target:.3f} nm | Current: {current:.3f} nm')

        print(f'Final wavelength: {self.wavelength:.3f} nm')

    @property
    def cleanliness(self):
        interferogram = np.array(self.wm.fetch_interferogram(self.channel)) / 1e8

        window_center = 300 + np.argmax(interferogram[300:-300])
        window = interferogram[window_center - window_width : window_center + window_width]

        peak_height = window[window_width]
        secondary_height = max(
            window[:window_width-mask_width].max(),
            window[window_width+mask_width:].max()
        )
        return 100 * (1 - secondary_height/peak_height)

    def next_clean_mode(self, increase_wavelength=True, threshold = 50):
        """Find the next clean lasing mode in the specified direction."""
        print('Finding next clean mode.')
        direction = 1 if increase_wavelength else -1

        while True:
            self.step(direction)

            cleanliness = self.cleanliness
            print(f'Cleanliness: {self.cleanliness:4.1f} % | Target: {threshold:.1f} % | Wavelength: {self.wavelength:.3f} nm')

            if cleanliness > threshold: break

        print(f'Final wavelength: {self.wavelength:.3f} nm')
        print(f'Final cleanliness: {self.cleanliness:.1f} %')


    def on(self):
        self.verdi.on()

    def off(self):
        self.verdi.off()
        self.micrometer.off()

    # Debug util
    def plot_history(self):
        t, y = zip(*self._history)
        plot(t, y)
        plt.xlabel('Time (s)')
        plt.ylabel('Wavelength (nm)')
        plt.title('Auto-Tuning History')
        plt.show()
