#program to generate photodiode calibration table

from headers.ti_saph import TiSapphire
from headers.labjack_device import Labjack
from headers.rigol_ds1102e import RigolDS1102e
from headers.edm_util import deconstruct
from usb_power_meter.Power_meter_2 import PM16 
from pathlib import Path
# import the USB Powermeter. IF IT DOESNT CONNECT, DOUBLE CHECK THAT THE USB DEV is correctly written in the Power_meter_2.py  
#or you could just write the Dev Rule so that the USB power meter always works...your calll
# also sometime the power meter randomly times out...seems to be fixed by unplugging/plugging in the power meter.
import time
import numpy as np
import os, shutil

LABJACK_SCOPE = '/dev/fluorescence_scope' # ADDRESS OF THE OSCILOSCOPE
pm = PM16('/dev/power_meter')

#=====Define Operating parameters===#


VERDI_POWER = 8 # watts

#Ti_Saph wavelengths to scan
START_WAVELENGTH = 750 # nm
END_WAVELENGTH = 920 # nm
WAVELENGTH_SCAN_SPEED = 15 # percentage of maximum


#=======Communicate with Devices===#

ti_saph = TiSapphire()
scope = RigolDS1102e(LABJACK_SCOPE)

#===Set up Calibration Save file ===#

cali_filepath = '/home/vuthalab/gdrive/code/edm_control/fluorescence'+time.strftime('%Y-%m-%d')
Path(cali_filepath).mkdir(parents = True, exist_ok = True)

cali_filename = 'pd_calibration' + time.strftime('%Y-%m-%d-%H-%M-%S') + '.txt'
complete_path = os.path.join(cali_filepath, cali_filename)

#=== Calibration sequence===#

if True:
    #open text file and write header
    fil = open(complete_path, 'w')
    fil.write('wavelength(nm)'+'\t'+'photodiode(V)'+'\t'+'power(W)'+'\n')

    ti_saph.verdi.power = VERDI_POWER
    ti_saph.wavelength = START_WAVELENGTH

    while True:
        # Eat up backlash
        ti_saph.micrometer.speed = 50
        time.sleep(0.5)

        # Set Ti:Saph scanning speed
        ti_saph.micrometer.speed = WAVELENGTH_SCAN_SPEED
        increasing_scan = True

        scope.active_channel = 1
            
        try:
            while True:
                # read the voltage on the ti_saph monitoring photodiode
                power_pd_sample = np.average(scope.trace)

                # Get wavelength
                wavelength = ti_saph.wavelength

                pm.set_wavelength(wavelength)
                power = pm.power()

                print(f'Wavelength: {wavelength:.4f} nm')
                print(f'Ti sapph photodiode reads {power_pd_sample:.4f} V.')
                print(f'Power is {power*1000:.3f} mW.')
                print()

                if wavelength > START_WAVELENGTH and wavelength < END_WAVELENGTH:
                    #save values to data file
                    fil.write(f'{wavelength}\t{power_pd_sample}\t{power}\n')

                if wavelength > END_WAVELENGTH:
                    # Eat up backlash
                    ti_saph.micrometer.speed = -50
                    time.sleep(0.5)

                    # Flip direction at end of travel
                    ti_saph.micrometer.speed = -WAVELENGTH_SCAN_SPEED
                    increasing_scan = False

                # Stop, record data once we go back to start
                if wavelength < START_WAVELENGTH and not increasing_scan:
                    break

                time.sleep(0.2) 
        except:
            ti_saph.micrometer.off()
            break

    fil.close()

