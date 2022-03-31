import time 
from collections import defaultdict

import numpy as np 

from uncertainties import ufloat
from headers.util import unweighted_mean, nom

# Devices
from headers.ximea_camera import Ximea
from headers.qe_pro import QEProSpectrometer
from headers.CTC100 import CTC100

from models.image_accumulator import ImageAccumulator

from api.pump_laser import PumpLaser
from api.power_stabilizer import PowerStabilizer
#from api.pmt import PMT



# CHANGE THIS AFTER EACH UPDATE TO THE FLUORESCENCE OPTICS
ximea_roi = {
    'center_x': 460*2,
    'center_y': 350*2,
    'radius': 140*2,

#        'x_min': 481*2,
#        'x_max': 651*2,
#        'y_min': 338*2,
#        'y_max': 420*2,
}


def get_intensity(rate_image, roi = ximea_roi):
    """Returns the intensity (counts/s) summed over the ROI given a rate image."""

    if 'radius' in roi:
        # Circular ROI
        h, w = rate_image.shape
        x, y = np.meshgrid(np.arange(w), np.arange(h))
        mask = (x - roi['center_x'])**2 + (y - roi['center_y'])**2 < roi['radius']**2
        return rate_image[mask].sum()
    else:
        # Rectangular ROI
        return rate_image[roi['y_min']:roi['y_max'], roi['x_min']:roi['x_max']].sum()


class FluorescenceSystem:
    def __init__(
        self, 
        pump_source = 'tisaph-low', # Laser pump source
        samples_per_point = 5, # QE pro samples to take per point. (If QE pro disabled, counts Ximea samples.)
        background_samples = 1,

        ximea_exposure = 10, # Ximea exposure (s)
    ):
        self.cam = Ximea(exposure = ximea_exposure)
        self.background_samples = background_samples
        self.samples_per_point = samples_per_point

        self.pump = PumpLaser()
        self.pump.source = None
        self.pump_source = pump_source
        if pump_source != 'baf': self.pump.ti_saph.verdi.power = 8

        self.stabilizer = PowerStabilizer(self.pump)

        self.ctc = CTC100(31415)
        self.ctc.ramp_temperature('heat mirror', 10, 0.5)
        self.ctc.ramp_temperature('heat saph', 4, 0.3)
        self.ctc.enable_output()

        print('Fluorescence system initialized.')


    def _take_samples_raw(self, data_store, background=False, n_samples=1):
        """
        Take Ximea samples. Append samples to the given datastore.

        Datastore is expected to be a defaultdict(list).
        """

        name = 'background' if background else 'foreground'

        if background:
            # Block TiSaph beam
            self.pump.source = None
            time.sleep(3)

        # Reset camera, collect data
        self.cam.async_capture(fresh_sample=True)
        while True:
            curr_samples = len(data_store['sample-times'])
            power = data_store['power'][-1] if data_store['power'] else 0
            print(f'Collecting {name} samples... {curr_samples} | Power: {power:.3f} mW', end='\r', flush=True)

            try:
                if background:
                    power = self.pump.pm_power
                else:
                    power, error, gain = self.stabilizer.update()

                data_store['sample-times'].append(time.time())
                data_store['power'].append(power)
                data_store['temperature'].append(self.ctc.read('saph'))

                if not background:
                    data_store['angle'].append(self.pump.polarization)
                    data_store['wavelength'].append(self.pump.wavelength)
#                    data_store['linewidth'].append(self.pump.ti_saph.linewidth)
            except Exception as e:
                print(e)
                time.sleep(0.5)
                continue

            time.sleep(0.1)

            # Check for camera images
            if self.cam.image is not None:
                image = self.cam.raw_rate_image
                saturation = self.cam.saturation
                image_rate = get_intensity(image)


                data_store['rate'].append(image_rate)
                data_store['image-time'].append(self.cam._capture_time)

                if 'image' not in data_store: data_store['image'] = ImageAccumulator()
                data_store['image'].update(image)
                print(f'{name.title()} Ximea rate sample: {image_rate*1e-3:.4f} kcounts/s. Saturation: {saturation:.1f} %')

                if len(data_store['image-time']) >= n_samples: break
                self.cam.async_capture()

        # Unblock TiSaph beam
        if background: self.pump.source = self.pump_source


    def take_data(
        self,
        wavelength = 815, # nm.
        power = 8, # W
        temperature = 5, # K
        polarization = 0, # degree
    ):
        """Take data with the given conditions."""
        ##### Initialize Conditions #####
        print(f'Setting temperature to {temperature:.3f} K.')
        if temperature > 5.1: self.ctc.ramp_temperature('heat saph', temperature, 0.3)

        if self.pump_source != 'baf':
#            self.pump.wm.set_tisaph()
            if wavelength is not None:
                if abs(wavelength - self.pump.wavelength) > 1.0:
                    self.pump.source = None # Block tisaph while wavelength is changing.
                    self.pump.wavelength = wavelength

                    if self.background_samples == 0:
                        self.pump.source = self.pump_source

            print(f'Setting pump power to {power:.1f} W.')
            self.pump.ti_saph.verdi.power = power

        print(f'Setting polarization to {polarization:.1f}°.')
        self.pump.polarization = polarization

        
        # Datastores for background and foreground data
        background = defaultdict(list)
        foreground = defaultdict(list)


        # Take background samples
        if self.background_samples > 0:
            self._take_samples_raw(background, background=True, n_samples=self.background_samples)
            time.sleep(2)
        else:
            background['power'] = [0]
            background['rate'] = [0]


        # Stabilize pump power
        print('Stabilizing power...')
        self.stabilizer.reset(reset_accumulator=False)
        for i in range(60):
            try:
                power, error, gain = self.stabilizer.update()
            except Exception as e:
                print('Error stabilizing power:', e)
                time.sleep(1)
                continue
            print(f'Power: {power:.4f} mW | Gain: {gain:.3f} V', end='\r')
            time.sleep(0.25)

            # Break if within 0.3%
#            if abs(power/self.stabilizer.setpoint - 1) < 3e-3: break
            if abs(power/self.stabilizer.setpoint - 1) < 2e-2: break

        print()

        # Take foreground samples
        self._take_samples_raw(foreground, n_samples=self.samples_per_point)


        # Process data
        fg = foreground

        processed = {
            'power': unweighted_mean(fg['power']) - unweighted_mean(background['power']),
            'wavelength': unweighted_mean(fg['wavelength']),
#            'linewidth': unweighted_mean(fg['linewidth']),
            'angle': unweighted_mean(fg['angle']),

            'crystal-temperature': unweighted_mean(fg['temperature']),
            'foreground-rate': unweighted_mean(fg['rate']),
            'background-rate': unweighted_mean(background['rate']),
        }

        print(f'Wavelength: {processed["wavelength"]:.4f} nm.')
#        print(f'Linewidth: {processed["linewidth"]:.4f} nm.')
        print(f'Waveplate Angle: {processed["angle"]:.2f} degrees.')
        print(f'Optical Power: {processed["power"]:.4f} mW.')
        print(f'Crystal Temperature: {processed["crystal-temperature"]:.3f} K.')
        print()

        return {
            'foreground-raw': foreground,
            'background-raw': background,
            'processed': processed,
        }


    def off(self):
        self.pump.source = None
        self.pump.ti_saph.power = 4
        self.cam.close()
        self.ctc.disable_output()
#        self.pmt.off()
