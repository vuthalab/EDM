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




# Input parameters
XRANGE = [600,1100] # X, Y ROI of Ximea
YRANGE = [600,1200]


configuration = {
    'filter_mount_angle': 0, # deg

    'ximea_exposure': 200, # s

    'verdi_power': {
        'start': 5, # W
        'end': 7,
        'steps': 2,
    },

    'wavelength_range': {
        'start': 840, # nm
        'end': 900, # nm
        'steps': 61,
    },

    'growth': {
        'time': 3, # sccm
        'buffer_flow': 30, # sccm
        'neon_flow': 0, # sccm
    },

    'front_filters': [ # (name, count, angle)
        ('FESH0900', 1, 0),
        ('FILTER_WHEEL', 1, 0),
    ],
    'back_filters': [ # (name, count)
        ('FELH0900', 3),
        ('FEL0900', 1),
    ],
    'mounted_filters': [ # (name, count)
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



#Start communication with devices
scope = RigolDS1102e('/dev/fluorescence_scope')
ti_saph = TiSapphire()
cam = Ximea()
filter_stage = ElliptecRotationStage()

#Initialize devices
filter_stage.angle = configuration['filter_mount_angle']
scope.active_channel = 1


#====Set Up Files ====#
timestamp = time.strftime('%Y-%m-%d')
full_timestamp = time.strftime('%Y-%m-%d-%H-%M-%S')

folder = Path(f'/home/vuthalab/Desktop/edm_data/fluorescence/scans/{timestamp}/{full_timestamp}') # make folder for todays runs
folder.mkdir(parents = True, exist_ok = True) # if folder doesnt exist, create it

(folder / 'images').mkdir(exist_ok = True) # Create images folder

# Write configuration
with open(folder / 'configuration.json', 'w') as f: json.dump(configuration, f, indent=4)

# Main data collection loop
with open(folder / f'data.txt','w') as f:
    print('# Timestamp\tVerdi Power(W)\tWavelength (nm)\tTi:Sapph Power (V)\tCamera Intensity (counts/pixel)\tWavelength Uncertainty\tPower Uncertainty\tIntensity Uncertainty', file=f)

    while True:
        try:
            pump_power = np.random.choice(VERDI_POWER)
            wavelength = np.random.choice(WAVELENGTH_RANGE)

            ti_saph.verdi.power = pump_power
            ti_saph.wavelength = wavelength

            # Reset camera and start a capture
            cam.exposure = configuration['ximea_exposure']
            cam.async_capture()

            # Read power + wavelength samples until capture finishes
            powers = []
            wavelengths = []
            while cam.image is None:
                print(f'Collecting samples... {len(powers)}', end='\r', flush=True)
                while True:
                    wavelength = ti_saph.wavelength
                    if wavelength > 700: break # Prevent occasional glitches down to 400

                powers.append(np.average(scope.trace))
                wavelengths.append(wavelength)
                time.sleep(0.5)
            print()

            # Process data
            power = unweighted_mean(powers)
            wavelength = unweighted_mean(wavelengths)

            image = cam.image
            clipped = image[XRANGE[0]:XRANGE[1],YRANGE[0]:YRANGE[1]]
            intensity = ufloat(np.mean(clipped), np.std(clipped)/np.sqrt(clipped.size))

            print(f'Wavelength: {wavelength:.4f} nm.')
            print(f'Ti sapph photodiode reads {power:.4f} V.')
            print(f'Camera intensity is {intensity:.4f} counts.')
            print()

            # Save data
            timestamp = time.strftime('%Y-%m-%d-%H-%M-%S')
            img = Image.fromarray(np.minimum(0.3 * image, 255).astype(np.uint8))
            img.save(folder / 'images' / f'{timestamp}.png')

            print(f'{timestamp}\t{pump_power}\t{wavelength.n}\t{power.n}\t{intensity.n}\t{wavelength.s}\t{power.s}\t{intensity.s}', file=f, flush=True)
        except Exception as e:
            print(repr(e))
            cam.close()
            ti_saph.micrometer.off()
