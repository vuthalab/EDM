#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct 12 17:37:47 2021

@author: vuthalab
"""

#Import required python files and packages
#Packages
from pathlib import Path
import time 
import json
import traceback
import os

import numpy as np 
import matplotlib.pyplot as plt
from PIL import Image

from uncertainties import ufloat
from headers.util import unweighted_mean

#Devices
from headers.verdi import Verdi
from headers.ti_saph import TiSapphire
from headers.rigol_ds1102e import RigolDS1102e
from headers.rigol_dp832 import RigolDP832
from headers.elliptec_rotation_stage  import ElliptecRotationStage
from headers.ximea_camera import Ximea
from headers.filter_wheel import FilterWheel
from headers.qe_pro import QEProSpectrometer
from headers.rigol_dp832 import EOM


configuration = {
    'exposure': 20, # s
    'samples_per_point': 1,

    'roi': {
        'center_x': 468*2,
        'center_y': 386*2,
        'radius': 50*2,

#        'x_min': 481*2,
#        'x_max': 651*2,
#        'y_min': 338*2,
#        'y_max': 420*2,
    },

    'qe_pro_temperature': -30, # °C
    'photodiode_resistor': 100, # ohm

    'laser_mode': 'CW', #CW or ML
    'verdi_power': {
        'start': 6, # W
        'end': 10,
        'steps': 5,
    },

#    'wavelength_range': 'custom',
    'wavelength_range': {
        'start': 840, # nm
        'end': 870, # nm
        'steps': 61,
    },

    'growth': {
        'time': 3, # hours
        'buffer_flow': 30, # sccm
        'neon_flow': 0, # sccm
        'ablation_frequency': 50, # Hz
    },

    'eom': {
        'bias': -55, # V
        'drive': 'lambda/4',
    },

    'front_filters': [ # (name, count, angle)
        ('SEMROCKTLP01-887-LP1', 1, 234.00),
        ('SEMROCKTLP01-887-LP2', 1, 228.00),
        #('FELH0800',1,0),
        #('FESH0900', 1, 0),
        # ('FES0800', 1, 0),
        #('SEMROCK842', 2, 0),
       # ('FILTER_WHEEL', 1, 0),
    ],
    'spectrometer_filters': [# (name, count, angle)
#        ('SEMROCKTSP01-887-SP1', 1, 146.10),
#        ('SEMROCKTSP01-887-SP2', 1, 76.20),
        ('SEMROCK842FF01', 1, 0),
        ('SEMROCK842FF01', 1, 0),
    ],
    'back_filters': [ # (name, count)
        ('FELH0900', 3),
        ('FEL0900', 1),
        ('SEMROCKFF01-893/209-25', 1),
    ],
}


WAVELENGTH_RANGE = np.linspace(
    configuration['wavelength_range']['start'],
    configuration['wavelength_range']['end'],
    configuration['wavelength_range']['steps'],
)

#WAVELENGTH_RANGE = [
#    *np.linspace(810, 820, 21),
#    840,
#    *np.linspace(855, 865, 21)
#]

VERDI_POWER = np.linspace(
    configuration['verdi_power']['start'],
    configuration['verdi_power']['end'],
    configuration['verdi_power']['steps'],
)


#Start communication with devices
scope = RigolDS1102e('/dev/fluorescence_scope')
ti_saph = TiSapphire()
#cam = Ximea(exposure = configuration['exposure'])
cam = Ximea(exposure = 1e-3)
wheel = FilterWheel()
spec = QEProSpectrometer()
eom = EOM()

#Initialize devices
scope.active_channel = 1
spec.exposure = configuration['exposure'] * 1e6
spec.temperature = configuration['qe_pro_temperature']

#====Set Up Files ====#
timestamp = time.strftime('%Y-%m-%d')
full_timestamp = time.strftime('%Y-%m-%d-%H-%M-%S')

folder = Path(f'/home/vuthalab/Desktop/edm_data/fluorescence/scans/{timestamp}/{full_timestamp}') # make folder for todays runs
folder.mkdir(parents = True, exist_ok = True) # if folder doesnt exist, create it

(folder / 'images').mkdir(exist_ok = True) # Create images folder
(folder / 'spectra').mkdir(exist_ok = True) # Create spectra folder

# Write configuration
with open(folder / 'configuration.json', 'w') as f: json.dump(configuration, f, indent=4)

def get_intensity(rate_image):
    roi = configuration['roi']

    if 'radius' in roi:
        # Circular ROI
        h, w = rate_image.shape
        x, y = np.meshgrid(np.arange(w), np.arange(h))
        mask = (x - roi['center_x'])**2 + (y - roi['center_y'])**2 < roi['radius']**2
        return rate_image[mask].sum()
    else:
        # Rectangular ROI
        return rate_image[roi['y_min']:roi['y_max'], roi['x_min']:roi['x_max']].sum()


# Main data collection loop
with open(folder / f'data.txt', 'w') as f:
    print('# Timestamp\tRun Number\tVerdi Power(W)\tEOM Enabled\tWavelength (nm)\tWavelength Err\tPD Current (mA)\tCurrent Err\tXimea Count Rate\tRate Err\tWavelength Source', file=f, flush=True)
    

run_number = 0
while True:
    np.random.shuffle(WAVELENGTH_RANGE)
    try:
        for wavelength in WAVELENGTH_RANGE:
            ti_saph.wavelength = wavelength
            run_number += 1

            np.random.shuffle(VERDI_POWER)
            for pump_power in VERDI_POWER:
                print(f'Setting pump power to {pump_power:.1f} W.')
                ti_saph.verdi.power = pump_power

#                for eom_enabled in [False, True]:
                for eom_enabled in [False]:
                    print(f'EOM Enabled: {eom_enabled}.')
                    if eom_enabled:
                        eom.on()
                    else:
                        eom.off()

                    wm_wavelengths = []
                    spec_wavelengths = []
                    linewidths = []

                    background_voltages = []
                    foreground_voltages = []

                    foreground_images = []
                    background_images = []
                    net_rates = []

                    foreground_spectra = []
                    background_spectra = []

                    for i in range(configuration['samples_per_point']):
                        # Block TiSaph beam
                        wheel.position = 2
                        time.sleep(3)

                        # Reset camera/spectrometer, collect background data
                        print('Collecting background rate...', end='\r', flush=True)
                        cam.async_capture(fresh_sample=True)
                        spec.async_capture(fresh_sample=True)
                        while cam.image is None or spec.intensities is None:
                            print(f'Collecting background samples...', end='\r', flush=True)
                            background_voltages.append(np.average(scope.trace))

                            # Don't collect wavelength here - there is slight feedback from shutter
                            time.sleep(0.5)

                        image = cam.raw_rate_image
                        background_images.append(image)
                        background_spectra.append(spec.intensities)

                        background_rate = get_intensity(image)
                        qe_pro_rate = spec.intensities.sum()/configuration['exposure']
                        print(f'Background Ximea rate is {background_rate*1e-3:.4f} kcounts/s.')
                        print(f'Background QE Pro rate is {qe_pro_rate*1e-3:.4f} kcounts/s.')

                        # Unblock TiSaph beam
                        wheel.position = 6
                        time.sleep(3)

                        # Reset camera/spectrometer, collect foreground data
                        cam.async_capture(fresh_sample=True)
                        spec.async_capture(fresh_sample=True)
                        while cam.image is None or spec.intensities is None:
                            print(f'Collecting foreground samples... {len(spec_wavelengths)}', end='\r', flush=True)
                            foreground_voltages.append(np.average(scope.trace))

                            try:
                                wm_wavelengths.append(ti_saph.wavemeter_wavelength)
                            except AssertionError:
                                pass

                            spec_wavelengths.append(ti_saph.spectrometer_wavelength)
                            linewidths.append(ti_saph.linewidth)

                            time.sleep(0.5)

                        image = cam.raw_rate_image
                        foreground_images.append(image)
                        foreground_spectra.append(spec.intensities)

                        foreground_rate = get_intensity(image)
                        qe_pro_rate = spec.intensities.sum()/configuration['exposure']
                        print(f'Foreground rate is {foreground_rate*1e-3:.4f} kcounts/s. Saturation: {cam.saturation:.3f} %')
                        print(f'Foreground QE Pro rate is {qe_pro_rate*1e-3:.4f} kcounts/s.')


                        net_rates.append(foreground_rate - background_rate)


                    # Process data
                    voltage = unweighted_mean(foreground_voltages) - unweighted_mean(background_voltages)
                    if wm_wavelengths:
                        source = 'wavemeter'
                        wavelength = unweighted_mean(wm_wavelengths)
                    else:
                        source = 'spectrometer'
                        wavelength = unweighted_mean(spec_wavelengths)
                    linewidth = unweighted_mean(linewidths)
                    rate = unweighted_mean(net_rates)

                    current = voltage / configuration['photodiode_resistor']

                    print(f'Wavelength Source: {source}.')
                    print(f'Wavelength: {wavelength:.4f} nm.')
                    print(f'Linewidth: {linewidth:.4f} nm.')
                    print(f'Ti sapph photodiode reads {voltage:.4f} V ({current*1e3:.4f} mA).')
                    print(f'Background voltage is {1e3*unweighted_mean(background_voltages):.4f} mV.')
                    print(f'Camera intensity is {rate*1e-3:.4f} kcounts/s.')
                    print()

                    # Save Image
                    timestamp = time.strftime('%Y-%m-%d-%H-%M-%S')
                    np.savez(
                        folder / 'images' / f'{timestamp}.npz',
                        run = run_number,
                        foreground = np.mean(foreground_images, axis=0),
                        background = np.mean(background_images, axis=0),
                        net_rates = net_rates,

                        pump_power = pump_power,
                        pump_wavelengths_wm = wm_wavelengths,
                        pump_wavelengths_spec = spec_wavelengths,

                        eom_enabled = eom_enabled,

                        linewidths = linewidths,
                        foreground_voltages = foreground_voltages,
                        background_voltages = background_voltages,
                    )
                    np.savez(
                        folder / 'spectra' / f'{timestamp}.npz',
                        run = run_number,
                        foreground = np.array(foreground_spectra),
                        background = np.array(background_spectra),
                        temperature = spec.temperature,

                        pump_power = pump_power,
                        pump_wavelengths_wm = wm_wavelengths,
                        pump_wavelengths_spec = spec_wavelengths,

                        eom_enabled = eom_enabled,

                        foreground_voltages = foreground_voltages,
                        background_voltages = background_voltages,

                        linewidths = linewidths,
                        wavelengths = spec.wavelengths,
                    )

                    # Save Data
                    with open(folder / f'data.txt', 'a') as f:
                        print(f'{timestamp}\t{run_number}\t{pump_power}\t{eom_enabled}\t{wavelength.n}\t{wavelength.s}\t{current.n}\t{current.s}\t{rate.n}\t{rate.s}\t{source}', file=f, flush=True)


    except Exception as e:
        print(repr(e))
        cam.close()
        ti_saph.power = 4.5
        ti_saph.micrometer.off()
        eom.off()
        os.exit()
