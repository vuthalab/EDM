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
from api.pmt import PMT

ximea_roi = {
    'center_x': 465*2,
    'center_y': 346*2,
    'radius': 110*2,

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

        ximea_exposure = 10, # Ximea exposure (s)

        use_qe_pro = True,
        qe_pro_exposure = 20, # QE Pro exposure (s)
        qe_pro_temperature = -29, # QE Pro CCD temp. Do not set this too low.
    ):
        self.cam = Ximea(exposure = ximea_exposure)
        self.samples_per_point = samples_per_point

        self.pump = PumpLaser()
        self.pump.source = None
        self.pump.ti_saph.verdi.power = 8
        self.pump_source = pump_source

        self.ctc = CTC100(31415)
        self.ctc.ramp_temperature('heat coll', 8, 0.5)
        self.ctc.ramp_temperature('heat saph', 4, 0.3)
        self.ctc.enable_output()

        if use_qe_pro:
            self.spec = QEProSpectrometer()
            self.spec.exposure = qe_pro_exposure * 1e6
            self.spec.temperature = qe_pro_temperature
        else:
            self.spec = None

        self.pmt = PMT()
        self.pmt.gain = 1.0


    def _take_samples_raw(self, data_store, background=False, n_spectra=1):
        """
        Take Ximea and spectrometer samples. Append samples to the given datastore.

        Datastore is expected to be a defaultdict(list).
        """

        name = 'background' if background else 'foreground'

        if background:
            # Block TiSaph beam
            self.pump.source = None
            time.sleep(3)

        # Reset camera/spectrometer, collect data
        self.cam.async_capture(fresh_sample=True)
        if self.spec is not None: self.spec.async_capture(fresh_sample = True)
        while True:
            n_samples = len(data_store['power'])
            print(f'Collecting {name} samples... {n_samples}', end='\r', flush=True)

            try:
                data_store['sample-times'].append(time.time())
                data_store['power'].append(self.pump.pm_power)
                data_store['pmt-current'].append(self.pmt.current)
                data_store['temperature'].append(self.ctc.read('saph'))

                if not background:
                    data_store['wavelength'].append(self.pump.wavelength)
                    data_store['linewidth'].append(self.pump.ti_saph.linewidth)
                    data_store['angle'].append(self.pump.polarization)
            except Exception as e:
                time.sleep(0.5)
                continue
            time.sleep(0.5)

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

                if self.spec is None and len(data_store['image-time']) >= n_spectra:
                    break
                self.cam.async_capture()

            # Check for spectrometer images
            if self.spec is not None and self.spec.intensities is not None:
                spectrum = self.spec.intensities
                qe_pro_rate = spectrum.sum()/configuration['exposure']

                data_store['spectrum'].append(spectrum)
                data_store['spectrum-time'].append(self.spec._capture_time)
                data_store['ccd-temperature'].append(self.spec.temperature)
                print(f'{name.title()} QE Pro rate sample: {qe_pro_rate*1e-3:.4f} kcounts/s.')

                if len(data_store['spectrum-time']) >= n_spectra:
                    break
                spec.async_capture()


        # Unblock TiSaph beam
        if background: self.pump.source = self.pump_source


    def take_data(
        self,
        wavelength = 815, # nm.
        power = 8, # W
        temperature = 5, # K
    ):
        """Take data with the given conditions."""
        ##### Initialize Conditions #####
        print(f'Setting temperature to {temperature:.3f} K.')
        self.ctc.ramp_temperature('heat saph', temperature, 0.3)

        if abs(wavelength - self.pump.wavelength) > 0.5:
            self.pump.source = None # Block tisaph while wavelength is changing.
            self.pump.wavelength = wavelength

        print(f'Setting pump power to {power:.1f} W.')
        self.pump.ti_saph.verdi.power = power

        
        # Datastores for background and foreground data
        background = defaultdict(list)
        foreground = defaultdict(list)

        # Take background sample
        self._take_samples_raw(background, background=True, n_spectra=1)

        # Take foreground samples
        self._take_samples_raw(foreground, n_spectra=self.samples_per_point)


        # Process data
        fg = foreground

        processed = {
            'power': unweighted_mean(fg['power']) - unweighted_mean(background['power']),
            'wavelength': unweighted_mean(fg['wavelength']),
            'linewidth': unweighted_mean(fg['linewidth']),
            'angle': unweighted_mean(fg['angle']),

            'pmt-gain': self.pmt.gain,
            'pmt-current': unweighted_mean(fg['pmt-current']) - unweighted_mean(background['pmt-current']),
            'crystal-temperature': unweighted_mean(fg['temperature']),
            'foreground-rate': unweighted_mean(fg['rate']),
            'background-rate': unweighted_mean(background['rate']),
        }

        print(f'Wavelength: {processed["wavelength"]:.4f} nm.')
        print(f'Linewidth: {processed["linewidth"]:.4f} nm.')
        print(f'EOM Angle: {processed["angle"]:.2f} degrees.')
        print(f'Optical Power: {processed["power"]:.4f} mW.')
        print(f'PMT Current: {processed["pmt-current"]:.2f} uA.')
        print(f'Crystal Temperature: {processed["crystal-temperature"]:.3f} K.')

        if self.spec is not None:
            processed['ccd-temperature'] = unweighted_mean(fg['ccd-temperature']),
            processed['foreground-spectra'] = np.array(fg['spectrum'])
            processed['background-spectrum'] = np.array(background['spectrum'])
            print(f'CCD Temperature: {processed["ccd-temperature"]:.3f} K.')

        print()
        return {
            'foreground-raw': foreground,
            'background-raw': background,
            'processed': processed,
        }


    def off(self):
        self.pump.source = None
        self.pump.ti_saph.power = 5
        self.cam.close()
        self.ctc.disable_output()
        self.pmt.off()
