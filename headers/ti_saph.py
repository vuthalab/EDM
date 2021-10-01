import time
import itertools as it

import matplotlib.pyplot as plt
import numpy as np
from uncertainties import ufloat, correlated_values

from headers.zmq_client_socket import connect_to

from headers.verdi import Verdi
from headers.rigol_dp832 import TiSaphMicrometer
from headers.wavemeter import WM

from headers.util import display, nom, std, uarray


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
        self.last_frequency = None


    def reset_backlash(self, direction):
        """Eats up the backlash in the system."""
        if direction != self.last_direction:
            self.micrometer.speed = direction * 100
            time.sleep(0.5)
            self.micrometer.off()

        self.last_direction = direction
            

    @property
    def wavemeter_intensity(self) -> float:
        """Returns the intensity coupled into the wavemeter [uW]."""
        return self.wm.read_laser_power(self.channel)

    @property
    def frequency(self) -> float:
        """Returns the frequency of the laser [GHz]."""
        try:
            current_frequency = float(self.wm.read_frequency(self.channel))
        except:
            current_frequency = self.last_frequency
        self.last_frequency = current_frequency
        return current_frequency

    @property
    def wavelength(self) -> float:
        """Returns the vacuum wavelength of the laser [nm]."""
        return float(speed_of_light) / float(self.frequency)


    @wavelength.setter
    def wavelength(self, target):
        """Coarsely set the wavelength."""
        print(f'Setting wavelength to {target:.3f} nm...')
        
        current = self.wavelength
        print(f'Starting wavelength is {current:.3f} nm.')

        direction = -1 if (current > target) else 1


        try:
            while True:
                speed = 15 * abs(current-target)
                speed = min(max(speed, 13), 100)
                self.micrometer.speed = direction * speed
                
                try:
                    current = self.wavelength
                except:
                    continue

                # Stop when target reached
                delta = direction * (target - current)
                if delta < 0:
                    break

                print(f'\rTarget: {target:.3f} nm | Current: {current:.3f} nm | Speed: {direction*speed:.1f} %', end='')
                time.sleep(0.4)
        finally:
            self.micrometer.off()
            print()

        print(f'Final wavelength: {self.wavelength:.3f} nm')
        return self.wavelength


    def on(self):
        self.verdi.on()

    def off(self):
        self.verdi.off()
        self.micrometer.off()