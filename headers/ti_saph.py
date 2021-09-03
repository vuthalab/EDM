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


    def step(
        self, direction,
        duration = 0.3, speed = 15,
        backoff = 0.1, cooldown = 0.2,
    ):
        """Perform a small step in the given direction."""
        self.reset_backlash(direction)
        try:
            #print('Going the right way.')
            #print('Direction is ', direction)
            #print('Speed is ', speed)
            self.micrometer.speed = direction * speed
            time.sleep(duration)
            #print('Going the wrong way.')
            #print('Direction is ', direction)
            #print('Speed is ', speed)
            self.micrometer.speed = -direction * speed
            time.sleep(backoff)
        finally: # To intercept KeyboardInterrupt
            self.micrometer.off()
            time.sleep(cooldown)
            
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
        counter = 0

        previous_wavelengths = np.empty(3) #storage for previous 4 wavelengths
        
        current = self.wavelength
        print(f'Starting wavelength is {current:.3f} nm.')

        direction = -1 if (current > target) else 1
        while True:
            counter += 1
            print('Current is ', current)
            print('Target is ', target)
            print('Direction is ', direction)
            
            self.step(direction, duration=0.8, speed=50)
            previous_wavelengths[counter%previous_wavelengths.size] = round(self.wavelength) # stores last 3 wavelengths round to a decimal place
            if previous_wavelengths[0] == previous_wavelengths[1] == previous_wavelengths[2]:
                print(f'Micrometer is stuck at: {self.wavelength:.3f} nm')
                return self.wavelength
            try:
                current = self.wavelength
            except:
                continue

            # Stop when target reached
            delta = direction * (target - current)
            if delta < 0: break

            print(f'Target: {target:.3f} nm | Current: {current:.3f} nm')

        print(f'Final wavelength: {self.wavelength:.3f} nm')
        return self.wavelength

    @property
    def mode_window(self):
        interferogram = np.array(self.wm.fetch_interferogram(self.channel)) / 1e8

        window_center = 300 + np.argmax(interferogram[300:-300])
        window = interferogram[window_center - window_width : window_center + window_width]
        return window

    def next_clean_mode(
        self,
        increase_wavelength=True,
        threshold = 0.05, # Stability threshold
        minimum_delta = 0.2, # minimum wavelength change, in nm
    ):
        """Find the next clean lasing mode in the specified direction."""
        print('Finding next clean mode.')
        direction = 1 if increase_wavelength else -1

        start_wavelength = self.wavelength

        while True:
            self.step(direction, duration=0.8)

            try:
                wavelength = self.wavelength
            except:
                wavelength = start_wavelength

            print(f'Wavelength: {wavelength:.3f} nm')

            if abs(wavelength - start_wavelength) > minimum_delta:
                print('Checking long-term stability...')
                samples = []
                for i in range(10):
                    samples.append(self.mode_window)
                    time.sleep(0.25)

                mean = np.mean(samples, axis=0)
                std = np.std(samples, axis=0, ddof=1)
                stability = np.max(std)/np.max(mean)

                if stability < threshold:
                    print(f'Passed with stability {stability:.3f}.')
                    break
                else:
                    print(f'Failed (stability {stability:.3f}), continuing.')

        return self.wavelength, uarray(mean, std)


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
