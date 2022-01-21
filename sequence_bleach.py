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
from collections import defaultdict

import numpy as np 
import matplotlib.pyplot as plt

from uncertainties import ufloat
from headers.util import unweighted_mean, nom

# Devices
from headers.ximea_camera import Ximea
from headers.qe_pro import QEProSpectrometer
from headers.CTC100 import CTC100

from api.pump_laser import PumpLaser
from api.pmt import PMT


configuration = {
    'ximea_exposure': 5, # s

    'recovery_time': [60], # s
    'recovery_wavelength': {
        'start': 830, # W
        'end': 885, # W
        'steps': 56,
    },
    'recovery_power': 6,
#    'recovery_power': {
#        'start': 6, # W
#        'end': 9, # W
#        'steps': 7,
#    },

    'bleach_time': 400, # s
    'bleach_wavelength': 815,
    'bleach_power': 6,

    'roi': {
        'center_x': 465*2,
        'center_y': 346*2,
        'radius': 110*2,
    },

    'growth': {
        'temperature': 6.5, #K
        'time': 3, # hours
        'buffer_flow': 30, # sccm
        'neon_flow': 0, # sccm
        'ablation_frequency': 30, # Hz
    },

    'front_filters': [ # (name, count, angle)
        ('SEMROCKTLP01-887-SP1', 1, 0),
        ('SEMROCKTLP01-887-SP2', 1, 0),
#        ('automated-SEMROCKFF01-900/11-25', 1, 0),
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



def linspace(name):
    """Generates evenly spaced values according to the given key in the configuration dictionary."""
    config = configuration[name]
    return np.linspace(config['start'], config['end'], config['steps'])


#RECOVERY_POWER = linspace('recovery_power')
RECOVERY_WAVELENGTHS = linspace('recovery_wavelength')


# Start communication with devices
cam = Ximea(exposure = configuration['ximea_exposure'])
pump = PumpLaser()
T1 = CTC100(31415)
pmt = PMT()

pmt.gain = 1.0
T1.ramp_temperature('heat coll', 8, 0.5)


###### Set Up Files #####
timestamp = time.strftime('%Y-%m-%d')
full_timestamp = time.strftime('%Y-%m-%d-%H-%M-%S')

folder = Path(f'/home/vuthalab/Desktop/edm_data/fluorescence/scans/{timestamp}/{full_timestamp}') # make folder for todays runs
folder.mkdir(parents = True, exist_ok = True) # if folder doesnt exist, create it
(folder / 'data').mkdir(exist_ok = True) # Create data folder


# Write configuration
with open(folder / 'configuration.json', 'w') as f: json.dump(configuration, f, indent=4)



def get_intensity(rate_image):
    """Returns the intensity (counts/s) summed over the ROI given a rate image."""
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



def take_samples(data_store, duration=100):
    """Take Ximea and spectrometer samples. Append samples to the given datastore."""

    print(f'Taking data for {duration} seconds...')

    # Reset camera/spectrometer, collect data
    start_time = time.monotonic()
    cam.async_capture(fresh_sample=True)
    while True:
        elapsed = time.monotonic() - start_time
        if elapsed > duration: break

        n_samples = len(data_store['wavelength'])
        print(f'Collecting samples... {n_samples} {elapsed:.2f} s', end='\r', flush=True)


        try:
            data_store['sample-times'].append(time.time())
            data_store['power'].append(pump.pm_power)
            data_store['pmt-current'].append(pmt.current)
            data_store['temperature'].append(T1.read('saph'))
            data_store['wavelength'].append(pump.wavelength)
            data_store['linewidth'].append(pump.ti_saph.linewidth)
        except Exception as e:
            time.sleep(0.5)
            continue


        # Continually get camera images
        if cam.image is not None:
            image = cam.raw_rate_image
            image_rate = get_intensity(image)

            data_store['rate'].append(image_rate)
            data_store['image-time'].append(cam._capture_time)
            print(f'Ximea rate sample: {image_rate*1e-3:.4f} kcounts/s.')

            cam.async_capture()

        time.sleep(0.3)





##### BEGIN MAIN DATA COLLECTION LOOP #####
pump.source = None
pump.ti_saph.verdi.power = 9
time.sleep(2)

# Start data collection run
#pump.ti_saph.verdi.power = 2
#pump.source = 'tisaph'

run_number = -1
while True:
    np.random.shuffle(RECOVERY_WAVELENGTHS)
    for recovery_wavelength in RECOVERY_WAVELENGTHS:
        run_number += 1

        np.random.shuffle(configuration['recovery_time'])
        for recovery_time in configuration['recovery_time']:
            try:
                recovery_pump_power = configuration['recovery_power']
                bleach_pump_power = configuration['bleach_power']
                print(recovery_pump_power, bleach_pump_power, recovery_time, recovery_wavelength)

                # Datastores for background and foreground data
                background = defaultdict(list)
                recovery = defaultdict(list)
                bleach = defaultdict(list)

                # Move to recovery wavelength
                print(f'Moving to recovery wavelength...')
                start_time = time.monotonic()
                pump.source = None
                time.sleep(1)
                pump.wavelength = recovery_wavelength
                pump.ti_saph.verdi.power = recovery_pump_power
                time.sleep(1)
                gap1 = time.monotonic() - start_time
                print(f'Gap 1: {gap1:.4f} s.')

                # Take recovery samples
                print('Recovery exposure.')
                recovery_start = time.monotonic()
                pump.source = 'tisaph-vert'
                take_samples(recovery, duration=recovery_time)

                # Move to bleach wavelength
                print(f'Moving to bleach wavelength...')
                start_time = time.monotonic()
                pump.source = None
                time.sleep(1)
                pump.ti_saph.verdi.power = bleach_pump_power
                pump.wavelength = configuration['bleach_wavelength']
                elapsed = time.monotonic() - recovery_start
                take_samples(background, duration=max(0, 200-elapsed))
                gap2 = time.monotonic() - start_time
                print(f'Gap 2: {gap2:.4f} s.')

                # Take bleach samples
                print('Bleach exposure.')
                pump.source = 'tisaph-vert'
                take_samples(bleach, duration=configuration['bleach_time'])

                # Save data
                timestamp = datetime.now().strftime('%Y-%m-%d-%H-%M-%S-%f')
                np.savez(
                    folder / 'data' / f'{timestamp}.npz',
                    run = run_number,

                    gap_1 = gap1,
                    gap_2 = gap2,
                    recovery_time = recovery_time,

                    recovery_pump_power = recovery_pump_power,
                    bleach_pump_power = bleach_pump_power,

                    background_sample_times = background['sample-times'],
                    recovery_sample_times = recovery['sample-times'],
                    bleach_sample_times = bleach['sample-times'],

                    recovery_power = nom(recovery['power']),
                    bleach_power = nom(bleach['power']),

                    recovery_pmt_current = nom(recovery['pmt-current']),
                    bleach_pmt_current = nom(bleach['pmt-current']),
                    background_pmt_current = nom(background['pmt-current']),

                    background_rate = [
                        background['image-time'],
                        background['rate']
                    ],
                    recovery_rate = [
                        recovery['image-time'],
                        recovery['rate']
                    ],
                    bleach_rate = [
                        bleach['image-time'],
                        bleach['rate']
                    ],

                    recovery_wavelength = nom(recovery['wavelength']),
                    bleach_wavelength = nom(bleach['wavelength']),

                    crystal_temperature = nom(bleach['temperature']),
                )

            except Exception as e:
                print(repr(e))
                cam.close()
                T1.disable_output()
                pump.ti_saph.verdi.power = 3
                pump.ti_saph.micrometer.off()
                pmt.off()
                quit()
