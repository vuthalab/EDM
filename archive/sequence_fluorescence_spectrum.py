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


configuration = {
    'filter_mount_angle': {
        'start': 0, # deg
        'end': 35, # deg
        'steps': 32,
    },

    'ximea_exposure': 10, # s
    'samples_per_point': 2,
    'roi': {
#        'center_x': 526*2,
#        'center_y': 375*2,
#        'radius': 30*2,

        'x_min': 481*2,
        'x_max': 651*2,
        'y_min': 338*2,
        'y_max': 420*2,
    },

    'photodiode_resistor': 100, # ohm

    'verdi_power': {
        'start': 7, # W
        'end': 7,
        'steps': 1,
    },

#    'wavelength_range': 'custom',
    'wavelength_range': {
        'start': 750, # nm
        'end': 850, # nm
        'steps': 101,
    },

    'growth': {
        'time': 0, # hours
        'buffer_flow': 0, # sccm
        'neon_flow': 0, # sccm
        'ablation_frequency': 0, # Hz
    },

    'front_filters': [ # (name, count, angle)
        ('SEMROCKTSP01-887-SP1', 1, 147),
        ('SEMROCKTSP01-887-SP2', 1, 77),
       # ('FESH0900', 1, 35),
        ('SEMROCK842', 2, 0),
       # ('FILTER_WHEEL', 1, 0),
    ],
    'back_filters': [ # (name, count)
        ('FELH0850', 2),
        ('FEL0850', 2),
    ],
    'mounted_filters': [ # (name, count)
#        ('FELH0900', 3),
        ('FESH0900', 1),
    ],
}


WAVELENGTH_RANGE = np.linspace(
    configuration['wavelength_range']['start'],
    configuration['wavelength_range']['end'],
    configuration['wavelength_range']['steps'],
)

VERDI_POWER = np.linspace(
    configuration['verdi_power']['start'],
    configuration['verdi_power']['end'],
    configuration['verdi_power']['steps'],
)

FILTER_STAGE_ANGLES = np.sqrt(np.linspace(
    configuration['filter_mount_angle']['start']**2,
    configuration['filter_mount_angle']['end']**2,
    configuration['filter_mount_angle']['steps'],
)) # Linear in filter cutoff (square of angle)



#Start communication with devices
scope = RigolDS1102e('/dev/fluorescence_scope')
ti_saph = TiSapphire()
cam = Ximea(exposure = configuration['ximea_exposure'])
filter_stage = ElliptecRotationStage()
wheel = FilterWheel()

#Initialize devices
#filter_stage.angle = configuration['filter_mount_angle']
scope.active_channel = 1


#====Set Up Files ====#
timestamp = time.strftime('%Y-%m-%d')
full_timestamp = time.strftime('%Y-%m-%d-%H-%M-%S')

folder = Path(f'/home/vuthalab/Desktop/edm_data/fluorescence/scans/{timestamp}/{full_timestamp}') # make folder for todays runs
folder.mkdir(parents = True, exist_ok = True) # if folder doesnt exist, create it

(folder / 'images').mkdir(exist_ok = True) # Create images folder

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
with open(folder / f'data.txt','w') as f:
    print('# Timestamp\tRun Number\tVerdi Power(W)\tAngle (°)\tAngle Err\tWavelength (nm)\tWavelength Err\tPD Current (mA)\tCurrent Err\tXimea Count Rate\tRate Err', file=f, flush=True)

    run_number = 0
    while True:
        np.random.shuffle(VERDI_POWER)
        for pump_power in VERDI_POWER:
            print(f'Setting pump power to {pump_power:.1f} W.')
            ti_saph.verdi.power = pump_power

            np.random.shuffle(WAVELENGTH_RANGE)
            try:
                for wavelength in WAVELENGTH_RANGE:
                    ti_saph.wavelength = wavelength
                    run_number += 1

                    np.random.shuffle(FILTER_STAGE_ANGLES)
                    for angle in FILTER_STAGE_ANGLES:
                        print(f'{angle} degrees')
                        filter_stage.angle = angle

                        voltages = []
                        wavelengths = []
                        angles = []

                        images = []
                        background_images = []
                        net_rates = []

                        for i in range(configuration['samples_per_point']):
                            wheel.position = 2
                            time.sleep(3)

                            print('Collecting background rate...', end='\r', flush=True)
                            cam.interrupt()
                            cam.async_capture()
                            while cam.image is None:
                                print(f'Collecting background samples... {len(wavelengths)}', end='\r', flush=True)
                                wavelengths.append(ti_saph.wavelength)
                                angles.append(filter_stage.angle)
                                time.sleep(0.5)
                            image = cam.raw_rate_image
                            background_rate = get_intensity(image)
                            background_images.append(image)
                            print(f'Background rate is {background_rate*1e-3:.4f} kcounts/s.')

                            wheel.position = 6
                            time.sleep(3)

                            # Reset camera and start a capture
                            cam.interrupt()
                            cam.async_capture()

                            # Read power + wavelength samples until capture finishes
                            while cam.image is None:
                                print(f'Collecting foreground samples... {len(wavelengths)}', end='\r', flush=True)
                                voltages.append(np.average(scope.trace))
                                wavelengths.append(ti_saph.wavelength)
                                angles.append(filter_stage.angle)
                                time.sleep(0.5)
                            image = cam.raw_rate_image
                            rate = get_intensity(image)
                            images.append(image)
                            print(f'Foreground rate is {rate*1e-3:.4f} kcounts/s. Saturation: {cam.saturation:.3f} %')

                            net_rates.append(rate - background_rate)


                        # Process data
                        voltage = unweighted_mean(voltages)
                        wavelength = unweighted_mean(wavelengths)
                        rate = unweighted_mean(net_rates)

                        current = voltage / configuration['photodiode_resistor']

                        print(f'Wavelength: {wavelength:.4f} nm.')
                        print(f'Ti sapph photodiode reads {voltage:.4f} V ({current*1e3:.4f} mA).')
                        print(f'Camera intensity is {rate*1e-3:.4f} kcounts/s.')
                        print()

                        # Save Image
                        timestamp = time.strftime('%Y-%m-%d-%H-%M-%S')
                        np.savez(
                            folder / 'images' / f'{timestamp}.npz',
                            foreground=np.mean(images, axis=0),
                            background=np.mean(background_images, axis=0),
                            net_rates=net_rates,
                            voltages=voltages,
                            angles=angles,
                            wavelengths=wavelengths,
                        )

                        # Save Data
                        real_angle = unweighted_mean(angles)
                        print(f'{timestamp}\t{run_number}\t{pump_power}\t{real_angle.n}\t{real_angle.s}\t{wavelength.n}\t{wavelength.s}\t{current.n}\t{current.s}\t{rate.n}\t{rate.s}', file=f, flush=True)

            except Exception as e:
                print(repr(e))
                cam.close()
                ti_saph.power = 4.5
                ti_saph.micrometer.off()
                os.exit()
