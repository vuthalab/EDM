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
        'end': 0, # deg
        'steps': 1,
    },

    'ximea_exposure': 30, # s

    'photodiode_resistor': 100, # ohm

    'verdi_power': {
        'start': 7, # W
        'end': 7,
        'steps': 1,
    },

    'wavelength_range': {
        'start': 800, # nm
        'end': 850, # nm
        'steps': 17,
    },

    'growth': {
        'time': 3, # sccm
        'buffer_flow': 30, # sccm
        'neon_flow': 0, # sccm
        'ablation_frequency': 0, # Hz
    },

    'front_filters': [ # (name, count, angle)
        ('SEMROCKTSP01-887-SP1',1,147),
        ('SEMROCKTSP01-887-SP2',1,77)
       # ('FESH0900', 1, 35),
       # ('SEMROCK842', 2, 0),
       # ('FILTER_WHEEL', 1, 0),
    ],
    'back_filters': [ # (name, count)
        ('FELH0850', 2),
        ('FEL0850', 2),
    ],
    'mounted_filters': [ # (name, count)
#        ('FELH0900', 3),
#        ('FESH0900', 1),
    ]
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

FILTER_STAGE_ANGLES = np.linspace(
    configuration['filter_mount_angle']['start'],
    configuration['filter_mount_angle']['end'],
    configuration['filter_mount_angle']['steps'],
)



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




# Get Ximea background
background_rate = None
background_image = None
def calibrate_background():
    global background_rate
    print('Collecting background rate...')
    wheel.position = 2
    time.sleep(3)

    images = []
    rates = []
    for i in range(3):
        print(f'Capture {i}')
        cam.interrupt()
        cam.capture()
        image = cam.raw_rate_image
        images.append(image)
        rates.append(image.sum())
    background_rate = unweighted_mean(rates)
    background_image = np.mean(images, axis=0)
    print(f'Background rate is {background_rate*1e-6:.4f} Mcounts/s.')

    wheel.position = 6
    time.sleep(3)

filter_stage.angle = np.random.choice(FILTER_STAGE_ANGLES)
calibrate_background()



# Main data collection loop
with open(folder / f'data.txt','w') as f:
    print('# Timestamp\tVerdi Power(W)\tWavelength (nm)\tWavelength Err\tPD Current (mA)\tCurrent Err\tXimea Count Rate\tRate Err', file=f, flush=True)

    while True:
        try:
            pump_power = np.random.choice(VERDI_POWER)
            wavelength = np.random.choice(WAVELENGTH_RANGE)

            if np.random.random() < 0.1:
                filter_stage.angle = np.random.choice(FILTER_STAGE_ANGLES)
                calibrate_background()


            print(f'Setting pump power to {pump_power:.1f} W.')
            ti_saph.verdi.power = pump_power
            ti_saph.wavelength = wavelength


            voltages = []
            wavelengths = []
            images = []
            rates = []
            for i in range(4):
                # Reset camera and start a capture
                cam.interrupt()
                cam.async_capture()

                # Read power + wavelength samples until capture finishes
                while cam.image is None:
                    print(f'Collecting samples... {len(voltages)}', end='\r', flush=True)
                    voltages.append(np.average(scope.trace))
                    wavelengths.append(ti_saph.wavelength)
                    time.sleep(0.5)
                print(f'Saturation: {cam.saturation} %')

                image = cam.raw_rate_image
                rate = image.sum()

                images.append(image)
                rates.append(rate)

            # Process data
            voltage = unweighted_mean(voltages)
            wavelength = unweighted_mean(wavelengths)
            rate = unweighted_mean(rates) - background_rate

            current = voltage / configuration['photodiode_resistor']

            print(f'Wavelength: {wavelength:.4f} nm.')
            print(f'Ti sapph photodiode reads {voltage:.4f} V ({current*1e3:.4f} mA).')
            print(f'Camera intensity is {rate*1e-6:.4f} Mcounts/s.')
            print()

            # Save Image
            timestamp = time.strftime('%Y-%m-%d-%H-%M-%S')
            np.save(folder / 'images' / f'{timestamp}-foreground.npy', np.mean(images, axis=0))
            np.save(folder / 'images' / f'{timestamp}-background.npy', background_image)

            # Save Data
            print(f'{timestamp}\t{pump_power}\t{filter_stage.angle}\t{wavelength.n}\t{wavelength.s}\t{current.n}\t{current.s}\t{rate.n}\t{rate.s}', file=f, flush=True)

        except Exception as e:
            print(repr(e))
            cam.close()
            ti_saph.micrometer.off()
            os.exit()
