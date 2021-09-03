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


VERDI_POWER = 5 #watts

#Ti_Saph wavelengths to scan
START_WAVELENGTH = 750 #nm
END_WAVELENGTH = 925 #nm
WAVELENGTH_STEP = 1 #nm
NUM_WAVE_STEPS = int((END_WAVELENGTH - START_WAVELENGTH)/WAVELENGTH_STEP)

#containers for Outputs
target_wavelengths = np.linspace(START_WAVELENGTH, END_WAVELENGTH, NUM_WAVE_STEPS)
actual_wavelengths = np.zeros(NUM_WAVE_STEPS)
ti_saph_power_pd = np.zeros(NUM_WAVE_STEPS)
power_meter = np.zeros(NUM_WAVE_STEPS)


#=======Communicate with Devices===#

ti_saph = TiSapphire()
#labjack = Labjack('470022275') 
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
    while True:
        try:
            for i in range(NUM_WAVE_STEPS):
                ti_saph.wavelength = round(target_wavelengths[i],4)
                actual_wavelengths[i] = ti_saph.wavelength
            
                scope.active_channel = 1
                ti_saph_power_pd[i] = np.average(scope.trace)
            
                pm.set_wavelength(target_wavelengths[i])
                power_meter[i] = pm.power()
                print('Voltage is ', ti_saph_power_pd[i], 'V.')
                print('Power is ', power_meter[i] * 1000.0, 'mW.\n')
                fil.write(f'{actual_wavelengths[i]}'+'\t'+f'{ti_saph_power_pd[i]}'+'\t'+f'{power_meter[i]}'+'\n')
        except:
            ti_saph.micrometer.off()
            break

    fil.close()

