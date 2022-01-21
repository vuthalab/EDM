import time
import itertools as it

import matplotlib.pyplot as plt
import numpy as np
from uncertainties import ufloat, correlated_values

try:
    from headers.zmq_client_socket import connect_to

    from headers.verdi import Verdi
    from headers.rigol_dp832 import TiSaphMicrometer
    from headers.wavemeter import WM

    from headers.util import display, nom, std, uarray
except:
    from zmq_client_socket import connect_to

    from verdi import Verdi
    from rigol_dp832 import TiSaphMicrometer
    from wavemeter import WM

    from util import display, nom, std, uarray

speed_of_light = 299792458 # GHz-nm




class TiSapphire:
    def __init__(self):
        self.verdi = Verdi()
        self.micrometer = TiSaphMicrometer()

        self.wm = WM()
        self.channel = 7

        self.last_direction = None

        self._spec_conn = connect_to('usb4000')
        self._cache = None


    def reset_backlash(self, direction):
        """Eats up the backlash in the system."""
        if direction != self.last_direction:
            self.micrometer.speed = direction * 100
            time.sleep(0.5)
            self.micrometer.off()

        self.last_direction = direction


    def _grab_data(self):
        """Read usb4000 thread until last entry."""
        while True:
            ts, data = self._spec_conn.grab_json_data()
            if data is not None:
                self._cache = (time.time(), data)
            else:
                if self._cache is not None:
                    break
            time.sleep(0.01)
            

    @property
    def wavemeter_intensity(self) -> float:
        """Returns the intensity coupled into the wavemeter [uW]."""
        return self.wm.read_laser_power(self.channel)

    @property
    def wavemeter_wavelength(self) -> float:
        """Returns the wavelength from the wavemeter [nm]."""

#        assert False # TEMP

        # Try reading from wavemeter
        freq = self.wm.read_frequency(self.channel)

        if not isinstance(freq, float) or freq > 500000:
            # If we get a bad reading, throw an exception
            assert False

        return speed_of_light/freq

    @property
    def spectrometer_wavelength(self) -> float:
        """Returns the vacuum wavelength of the laser as given by spectrometer [nm]."""
        return float(speed_of_light) / self.frequency

    @property
    def frequency(self) -> float:
        """Returns the frequency of the laser from spectrometer [GHz]."""
        self._grab_data()
        if time.time() - self._cache[0] > 2: raise ValueError('Stale data!') # Check if data is stale
        return ufloat(*self._cache[1]['frequency'])

    @property
    def linewidth(self) -> float:
        """Returns the linewidth of the laser [nm]."""
        self._grab_data()
        return self._cache[1]['linewidth']
    
    @property
    def wavelength(self) -> float:
        """Returns the vacuum wavelength of the laser [nm]. Tries to use the wavemeter, but uses the spectrometer if this does not work."""
        try:
            return self.wavemeter_wavelength
        except AssertionError:
            return self.spectrometer_wavelength

    @property
    def fast_wavelength(self) -> float:
        """Returns the vacuum wavelength of the laser [nm]. Tries to use the spectrometer, but uses the wavemeter if this does not work."""
        try:
            return self.spectrometer_wavelength
        except ValueError:
            return self.wavemeter_wavelength


    @wavelength.setter
    def wavelength(self, target):
        """Coarsely set the wavelength."""
        print(f'Setting wavelength to {target:.3f} nm...')
       
        current = self.wavelength
        print(f'Starting wavelength is {current:.3f} nm.')

        direction = -1 if (current > target) else 1

        try:
            min_delta = 999999

            while True:
                speed = 7 * abs(current-target)
#                speed = min(max(speed, 13), 100)
                speed = min(max(speed, 13), 40)
                self.micrometer.speed = direction * speed
                
                try:
                    current = nom(self.fast_wavelength)
#                current = nom(self.wavelength)
                except Exception as e:
                    time.sleep(0.5)
                    continue

                # Stop when target reached
                delta = direction * (target - current)
                if delta < 0.1: # Allow stopping a bit early
                    break

                min_delta = min(min_delta, delta)
                if delta > min_delta + 20: # Wavelength jumps up: wraparound?
                    self.micrometer.speed = -100 * direction
                    time.sleep(5)
                    raise ValueError('Wavelength out of range!')


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

if __name__ == '__main__':
    ti_saph = TiSapphire()
    print('Current wavelength is ', ti_saph.wavelength, 'nm.')
