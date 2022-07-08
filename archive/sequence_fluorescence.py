#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct 12 17:37:47 2021

@author: vuthalab
"""

from pathlib import Path
import time 
from datetime import datetime
import json
import os

import numpy as np 
import matplotlib.pyplot as plt

from uncertainties import ufloat
from headers.util import unweighted_mean, nom

from api.fluorescence import FluorescenceSystem


configuration = {
    'laser_mode': 'CW', # CW or ML
    'verdi_power': {
        'start': 8, # W
        'end': 8, # W
        'steps': 1,
    },

#    'wavelength_range': 'custom',
    'wavelength_range': {
        'start': 745, # nm
        'end': 800, # nm
        'steps': 321,
    },
    
    'temperature_range': {
        'start': 3, # K
        'end': 3, # K
        'steps': 1,
     },

    'polarization_range': {
        'start': 0, # deg
#        'end': 0, # deg
#        'steps': 1,

#        'end': 360, # deg
#        'steps': 721,
#        'steps': 25,

        'end': 45,
        'steps': 2,
     },

    'growth': {
        'temperature': 5, #K
        'time': 10, # minutes
        'buffer_flow': 20, # sccm
        'neon_flow': 0, # sccm
        'ablation_frequency': 30, # Hz
    },
}

system = FluorescenceSystem(
    ximea_exposure = 3,
    samples_per_point = 1,

#    ximea_exposure = 0.01,
#    samples_per_point = 10,
    #background_samples = 10,

#    pump_source = 'tisaph-high'
    pump_source = 'tisaph-low'
)


def linspace(name):
    """Generates evenly spaced values according to the given key in the configuration dictionary."""
    config = configuration[name]
    return np.linspace(config['start'], config['end'], config['steps'])


if configuration['wavelength_range'] == 'custom':
    WAVELENGTH_RANGE = [
#        *np.linspace(790, 801, 12),
        *np.linspace(802, 809.5, 16),
        *np.linspace(810, 818, 33),
        *np.linspace(818.5, 822.5, 9),
        *np.linspace(823, 830, 29),
        *np.linspace(831, 849, 19),
        *np.linspace(850, 865, 61),
#        *np.linspace(866, 885, 20),
    ]
else:
    WAVELENGTH_RANGE = linspace('wavelength_range')

CRYSTAL_TEMP_RANGE = linspace('temperature_range')
VERDI_POWER = linspace('verdi_power')
POLARIZATION = linspace('polarization_range')

#system.pump.eom.frequency = 2e6


###### Set Up Files #####
timestamp = time.strftime('%Y-%m-%d')
full_timestamp = time.strftime('%Y-%m-%d-%H-%M-%S')

folder = Path(f'/home/vuthalab/Desktop/edm_data/fluorescence/scans/{timestamp}/{full_timestamp}') # make folder for todays runs
folder.mkdir(parents = True, exist_ok = True) # if folder doesnt exist, create it
(folder / 'data').mkdir(exist_ok = True) # Create data folder

# Write configuration
with open(folder / 'configuration.json', 'w') as f: json.dump(configuration, f, indent=4)


##### BEGIN MAIN DATA COLLECTION LOOP #####
run_number = 0
total_samples = 0

## TODO TEMP
np.random.shuffle(WAVELENGTH_RANGE)
#WAVELENGTH_RANGE = [815, *WAVELENGTH_RANGE]

while True:
    try:
#        np.random.shuffle(WAVELENGTH_RANGE)
        for wavelength in WAVELENGTH_RANGE:
            run_number += 1

            np.random.shuffle(CRYSTAL_TEMP_RANGE)
            for temp in CRYSTAL_TEMP_RANGE:

                np.random.shuffle(VERDI_POWER)
                for pump_power in VERDI_POWER:

                    np.random.shuffle(POLARIZATION)
                    for i, polarization in enumerate(POLARIZATION):
                        data = system.take_data(
                            wavelength = wavelength if i == 0 else None,
                            power = pump_power,
                            temperature = temp,
                            polarization=polarization,
                        )
                        fg = data['foreground-raw']
                        background = data['background-raw']

                        # Save data
                        timestamp = datetime.now().strftime('%Y-%m-%d-%H-%M-%S-%f')
                        np.savez(
                            folder / 'data' / f'{timestamp}.npz',
                            run = run_number,

#                           foreground_image = fg['image'].meanstderr,
#                           background_image = background['image'].meanstderr,

                            image_times = fg['image-time'],
                            foreground_rates = fg['rate'],
                            background_rates = background['rate'],

                            sample_times = fg['sample-times'],

                            pump_power = pump_power,
                            pump_wavelength = nom(fg['wavelength']),
                            pump_linewidth = nom(fg['linewidth']),

                            foreground_power = nom(fg['power']),
                            background_power = nom(background['power']),

                            polarization = nom(fg['angle']),
                            crystal_temperature = nom(fg['temperature']),

                            transmission = fg['transmission'] - np.mean(background['transmission']),
                    )

    except Exception as e:
        print(repr(e))
        system.off()
        quit()
