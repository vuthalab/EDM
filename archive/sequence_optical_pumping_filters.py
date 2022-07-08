import time
from datetime import datetime
from pathlib import Path
import numpy as np

from headers.elliptec_rotation_stage import ElliptecRotationStage
from headers.util import nom

from api.pump_laser import PumpLaser
from api.fluorescence import FluorescenceSystem


mount = ElliptecRotationStage(port='/dev/rotation_mount', offset=22434)
mount_2 = ElliptecRotationStage(port='/dev/rotation_mount_2', offset=29866)
mount_3 = ElliptecRotationStage(port='/dev/rotation_mount_3', offset=-9896)
pump = PumpLaser()




WAVELENGTH_RANGE = [815]
#WAVELENGTH_RANGE = [820]

POLARIZATION = np.linspace(0, 360, 721)

LONGPASS_ANGLE = [35, -35, 0]


pump_power = 8
shortpass_angle = 22 # Semrock 842 SP @ 815 nm


mount.angle = shortpass_angle


system = FluorescenceSystem(
    ximea_exposure = 15,
    samples_per_point = 2,
    background_samples = 1,

    pump_source = 'tisaph-high'
)



###### Set Up Files #####
timestamp = time.strftime('%Y-%m-%d')
full_timestamp = time.strftime('%Y-%m-%d-%H-%M-%S')

folder = Path(f'/home/vuthalab/Desktop/edm_data/fluorescence/scans/{timestamp}/{full_timestamp}') # make folder for todays runs
folder.mkdir(parents = True, exist_ok = True) # if folder doesnt exist, create it
(folder / 'data').mkdir(exist_ok = True) # Create data folder


##### BEGIN MAIN DATA COLLECTION LOOP #####
run_number = 0
total_samples = 0

while True:
    try:
        np.random.shuffle(WAVELENGTH_RANGE)
        for wavelength in WAVELENGTH_RANGE:
            run_number += 1

            np.random.shuffle(POLARIZATION)
            for i, polarization in enumerate(POLARIZATION):

                for j, longpass_angle in enumerate(LONGPASS_ANGLE):
                    print(f'Longpass angle: {longpass_angle:.2f}°')
                    mount_2.angle = longpass_angle
                    mount_3.angle = longpass_angle

                    if longpass_angle == 0:
                        system.background_samples = 1
                        system.samples_per_point = 2
                        system.cam.exposure = 30
                    else:
                        system.background_samples = 10
                        system.samples_per_point = 10
                        system.cam.exposure = 0.01

                    data = system.take_data(
                        wavelength = wavelength if (i+j) == 0 else None,
                        power = pump_power,
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

                        longpass_angle = longpass_angle,
                        shortpass_angle = shortpass_angle,

                        foreground_power = nom(fg['power']),
                        background_power = nom(background['power']),

                        polarization = nom(fg['angle']),
                        crystal_temperature = nom(fg['temperature']),
                )

    except Exception as e:
        print(repr(e))
        system.off()
        quit()
