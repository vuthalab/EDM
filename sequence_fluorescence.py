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
from headers.util import unweighted_mean, nom

#Devices
from headers.verdi import Verdi
#from headers.ximea_camera import Ximea
from headers.qe_pro import QEProSpectrometer
from headers.CTC100 import CTC100

from headers.api import EOM, PumpLaser


configuration = {
    'exposure': 30, # s
    'samples_per_point': 1,
    'eom_trials': 4,

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
        'start': 8, # W
        'end': 8, # W
        'steps': 1,
    },

#    'wavelength_range': 'custom',
    'wavelength_range': {
        'start': 840, # nm
        'end': 890, # nm
        'steps': 101,
    },
    
    'temperature_range': {
        'start': 5.5, # K
        'end': 5.5, # K
        'steps': 1,
     },


    'growth': {
        'temperature': 8, #K
        'time': 0.5, # hours
        'buffer_flow': 0, # sccm
        'neon_flow': 14, # sccm
        'ablation_frequency': 0, # Hz
    },

    'eom': {
        'bias': -55, # V
        'drive': 'lambda/4',
    },

    'front_filters': [ # (name, count, angle)
#        ('SEMROCKTLP01-887-SP1', 1, 172.67),
#        ('SEMROCKTLP01-887-SP2', 1, 99.83),
        ('automated-SEMROCKFF01-900/11-25', 1, 0),
#        ('FELH0800',1,45),
#        ('FELH0800',1,45),
        #('FESH0900', 1, 0),
        # ('FES0800', 1, 0),
        #('SEMROCK842', 2, 0),
       # ('FILTER_WHEEL', 1, 0),
    ],
    'spectrometer_filters': [# (name, count, angle)
#        ('FELH850_IN_BP2_MOUNT', 1, 0),
#        ('FELH850_IN_BP3_MOUNT', 1, 0),
       ('SEMROCKTLP01-887-LP1', 1, 270),
       ('SEMROCKTLP01-887-LP2', 1, 270),
#       ('FESH0700', 1, 0),
#       ('SEMROCK842FF01', 1, 30),
#       ('SEMROCK842FF01', 1, 30),
#        ('FELH900', 1, 25),
#        ('FELH900', 1, 25),
    ],
    'back_filters': [ # (name, count)
        ('FELH0900', 3),
        ('FEL0900', 1),
        ('SEMROCKFF01-893/209-25', 1),
    ],
}


if configuration['wavelength_range'] == 'custom':
    WAVELENGTH_RANGE = [
        *np.linspace(814, 817, 7),
        *np.linspace(858, 862, 9)
    ]
else:
    WAVELENGTH_RANGE = np.linspace(
        configuration['wavelength_range']['start'],
        configuration['wavelength_range']['end'],
        configuration['wavelength_range']['steps'],
    )


CRYSTAL_TEMP_RANGE = np.linspace( 
    configuration['temperature_range']['start'],
    configuration['temperature_range']['end'],
    configuration['temperature_range']['steps'],
)

VERDI_POWER = np.linspace(
    configuration['verdi_power']['start'],
    configuration['verdi_power']['end'],
    configuration['verdi_power']['steps'],
)


#Start communication with devices
#cam = Ximea(exposure = configuration['exposure'])
#cam = Ximea(exposure = 1e-3)

verdi = Verdi()
pump = PumpLaser()

spec = QEProSpectrometer()
eom = EOM()
T1 = CTC100(31415)
#T2 = CTC100(31416)


#Initialize devices
spec.exposure = configuration['exposure'] * 1e6
spec.temperature = configuration['qe_pro_temperature']
pump.source = 'tisaph'
#T1.ramp_temperature('heat coll', 8, 0.5)

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
#with open(folder / f'data.txt', 'w') as f:
#    print('# Timestamp\tRun Number\tVerdi Power(W)\tEOM Enabled\tTemperature (K)\tTemp Err(K)\tWavelength (nm)\tWavelength Err\tPD Current (mA)\tCurrent Err\tXimea Count Rate\tRate Err\tWavelength Source', file=f, flush=True)
    
with open(folder / f'data.txt', 'w') as f:
    print('# Timestamp\tRun Number\tVerdi Power(W)\tEOM Enabled\tTemperature (K)\tTemp Err(K)\tWavelength (nm)\tWavelength Err\tCurrent Err', file=f, flush=True)
    

run_number = 0
total_samples = 0

background_cache = None

while True:
    try:
        np.random.shuffle(WAVELENGTH_RANGE)
        for wavelength in WAVELENGTH_RANGE:
            pump.wavelength = wavelength
            run_number += 1

            np.random.shuffle(CRYSTAL_TEMP_RANGE)
            for temp in CRYSTAL_TEMP_RANGE:
                print(f'Setting temperature to {temp:.3f} K.')
                T1.ramp_temperature('heat saph', temp, 0.3)
                T1.enable_output()
#                time.sleep(10)
                time.sleep(1)

                np.random.shuffle(VERDI_POWER)
                for pump_power in VERDI_POWER:
                    print(f'Setting pump power to {pump_power:.1f} W.')
                    verdi.power = pump_power


                    for eom_enabled in [True, False] * configuration['eom_trials']:
                        print(f'EOM Enabled: {eom_enabled}.')
                        if eom_enabled:
                            eom.on()
                        else:
                            eom.off()

                        wavelengths = []
                        linewidths = []

                        background_voltages = []
                        foreground_voltages = []

                        foreground_images = []
                        background_images = []
                        net_rates = []

                        foreground_spectra = []
                        background_spectra = []

                        temperatures = []


                        total_samples += 1

                        # Take background if it has been a while
                        take_background = (total_samples % 8 == 1)

                        if not take_background:
#                            background_images, background_spectra, background_voltages, background_rate = background_cache
                            background_spectra, background_voltages = background_cache

                        for i in range(configuration['samples_per_point']):
                            if take_background and i == 0:
                                # Block TiSaph beam
                                wheel.position = 2
                                time.sleep(3)

                                # Reset camera/spectrometer, collect background data
                                print('Collecting background rate...', end='\r', flush=True)
#                                cam.async_capture(fresh_sample=True)
                                spec.async_capture(fresh_sample=True)
#                                while cam.image is None or spec.intensities is None:
                                while spec.intensities is None:
                                    print(f'Collecting background samples...', end='\r', flush=True)
                                    background_voltages.append(np.average(scope.trace))
                                    temperatures.append(T1.read('saph'))

                                    # Don't collect wavelength here - there is slight feedback from shutter
                                    time.sleep(0.5)

#                                image = cam.raw_rate_image
#                                background_images.append(image)
                                background_spectra.append(spec.intensities)

#                                background_rate = get_intensity(image)
                                qe_pro_rate = spec.intensities.sum()/configuration['exposure']
#                                print(f'Background Ximea rate is {background_rate*1e-3:.4f} kcounts/s.')
                                print(f'Background QE Pro rate is {qe_pro_rate*1e-3:.4f} kcounts/s.')

                                # Unblock TiSaph beam
                                wheel.position = 6
                                time.sleep(3)

                            # Reset camera/spectrometer, collect foreground data
#                            cam.async_capture(fresh_sample=True)
                            spec.async_capture(fresh_sample=True)
#                            while cam.image is None or spec.intensities is None:
                            while spec.intensities is None:
                                print(f'Collecting foreground samples... {len(spec_wavelengths)}', end='\r', flush=True)
                                foreground_voltages.append(np.average(scope.trace))

                                try:
                                    wm_wavelengths.append(ti_saph.wavemeter_wavelength)
                                except AssertionError:
                                    pass

                                spec_wavelengths.append(ti_saph.spectrometer_wavelength)
                                linewidths.append(ti_saph.linewidth)

                                temperatures.append(T1.read('saph'))

                                time.sleep(0.5)

#                            image = cam.raw_rate_image
#                            foreground_images.append(image)
                            foreground_spectra.append(spec.intensities)

#                            foreground_rate = get_intensity(image)
                            qe_pro_rate = spec.intensities.sum()/configuration['exposure']
#                            print(f'Foreground rate is {foreground_rate*1e-3:.4f} kcounts/s. Saturation: {cam.saturation:.3f} %')
                            print(f'Foreground QE Pro rate is {qe_pro_rate*1e-3:.4f} kcounts/s.')


#                            net_rates.append(foreground_rate - background_rate)

                        # Cache background for later runs
#                        background_cache = (background_images, background_spectra, background_voltages, background_rate)
                        background_cache = (background_spectra, background_voltages)

                        # Process data
                        voltage = unweighted_mean(foreground_voltages) - unweighted_mean(background_voltages)
                        if wm_wavelengths:
                            source = 'wavemeter'
                            wavelength = unweighted_mean(wm_wavelengths)
                        else:
                            source = 'spectrometer'
                            wavelength = unweighted_mean(spec_wavelengths)
                        linewidth = unweighted_mean(linewidths)
#                        rate = unweighted_mean(net_rates)

                        current = voltage / configuration['photodiode_resistor']

                        temperature = unweighted_mean(temperatures)

                        print(f'Wavelength Source: {source}.')
                        print(f'Wavelength: {wavelength:.4f} nm.')
                        print(f'Linewidth: {linewidth:.4f} nm.')
                        print(f'Ti sapph photodiode reads {voltage:.4f} V ({current*1e3:.4f} mA).')
                        print(f'Background voltage is {1e3*unweighted_mean(background_voltages):.4f} mV.')
#                        print(f'Camera intensity is {rate*1e-3:.4f} kcounts/s.')
                        print(f'Crystal temperature is set to {temperature:.3f} K.')
                        print()

                        # Save Image
                        timestamp = time.strftime('%Y-%m-%d-%H-%M-%S')
                        if False: # We are not really using ximea
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

                                temperatures = nom(temperatures),
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
                            temperatures = nom(temperatures),
                        )

                        # Save Data
#                        with open(folder / f'data.txt', 'a') as f:
#                            print(f'{timestamp}\t{run_number}\t{pump_power}\t{eom_enabled}\t{temperature.n}\t{temperature.s}\t{wavelength.n}\t{wavelength.s}\t{current.n}\t{current.s}\t{rate.n}\t{rate.s}\t{source}', file=f, flush=True)

                        with open(folder / f'data.txt', 'a') as f:
                            print(f'{timestamp}\t{run_number}\t{pump_power}\t{eom_enabled}\t{temperature.n}\t{temperature.s}\t{wavelength.n}\t{wavelength.s}\t{current.n}\t{current.s}\t{source}', file=f, flush=True)


    except Exception as e:
        print(repr(e))
#        cam.close()
        T1.disable_output()
        ti_saph.power = 4.5
        ti_saph.micrometer.off()
        eom.off()
        os.exit()
