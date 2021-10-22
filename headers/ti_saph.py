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

        self._spec_conn = connect_to('usb4000')


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
        # Failsafe
        current_frequency = self.last_frequency

#        try:
#            # Read until we get a reasonable sample (i.e. not a second harmonic).
#            while True:
#                current_frequency = float(self.wm.read_frequency(self.channel))
#                if current_frequency < 430e3: break
#        except:
#            pass

        # Read usb4000 thread until last entry
        while True:
            ts, data = self._spec_conn.grab_json_data()
            if data is None:
                if current_frequency is not None or self.last_frequency is not None:
                    break
                else:
                    time.sleep(0.05)
                    continue
            current_frequency = data['frequency']

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
                speed = 7 * abs(current-target)
                speed = min(max(speed, 13), 100)
                self.micrometer.speed = direction * speed
                
                current = self.wavelength

                # Stop when target reached
                delta = direction * (target - current)
                if delta < 0:
                    break

                print(f'\rTarget: {target:.3f} nm | Current: {current:.3f} nm | Speed: {direction*speed:.1f} %', end='')
                time.sleep(0.2)
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
