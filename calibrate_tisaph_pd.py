#program to generate photodiode calibration table
from pathlib import Path
import time
import os, shutil

import numpy as np

from colorama import Fore, Style

from headers.ti_saph import TiSapphire
from headers.labjack_device import Labjack
from headers.rigol_ds1102e import RigolDS1102e
from headers.edm_util import deconstruct

# import the USB Powermeter. IF IT DOESNT CONNECT, DOUBLE CHECK THAT THE USB DEV is correctly written in the Power_meter_2.py  
#or you could just write the Dev Rule so that the USB power meter always works...your calll
# also sometime the power meter randomly times out...seems to be fixed by unplugging/plugging in the power meter.
from usb_power_meter.Power_meter_2 import PM16 


# ===== Communicate with Devices =====
LABJACK_SCOPE = '/dev/fluorescence_scope' # ADDRESS OF THE OSCILOSCOPE
pm = PM16('/dev/power_meter')
ti_saph = TiSapphire()
scope = RigolDS1102e(LABJACK_SCOPE)

# ===== Define Operating parameters =====
RESISTANCE = 10000 # photodiode resistor
FILTER = 1.0 #ND filter

# Ti:Saph wavelengths to scan
START_WAVELENGTH = 760 # nm
END_WAVELENGTH = 900 # nm
WAVELENGTH_SCAN_SPEED = 15 # percentage of maximum

VERDI_POWERS = np.array([5.0])#np.linspace(5, 9, 17) # Powers to scan over
SCANS_PER_POWER = 10 # Number of scans at each tisaph power


#=== Calibration sequence===#
save_directory = Path('/home/vuthalab/Desktop/edm_data/fluorescence/pd_calibration/')


while True:
    np.random.shuffle(VERDI_POWERS)

    for pump_power in VERDI_POWERS:
        #===Set up Calibration Save file ===#
        timestamp = time.strftime('%Y-%m-%d-%H-%M-%S')
        name = f'{pump_power:.2f}W_{START_WAVELENGTH}-{END_WAVELENGTH}nm_{RESISTANCE}ohm_ND{FILTER}_{timestamp}'
        filename = save_directory / f'{name}.txt'


        ti_saph.verdi.power = pump_power
        ti_saph.wavelength = START_WAVELENGTH

        with open(filename, 'w') as f:
            print('wavelength (nm)\tphotodiode (V)\tpower (W)', file=f)

            for scan_number in range(SCANS_PER_POWER):
                print(f'{Fore.GREEN}Running scan {scan_number+1} of {SCANS_PER_POWER} @ {pump_power} W{Style.RESET_ALL}')
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
                        power = pm.power() * 1000

                        print(f'{wavelength:.4f} nm | {power_pd_sample:8.4f} V on PD | {power:8.3f} mW on Power Meter\r', end='')

                        if wavelength > START_WAVELENGTH and wavelength < END_WAVELENGTH:
                            #save values to data file
                            print(f'{wavelength}\t{power_pd_sample}\t{power}', file=f)

                        if wavelength > END_WAVELENGTH:
                            # Eat up backlash
                            ti_saph.micrometer.speed = -50
                            time.sleep(0.5)

                            # Flip direction at end of travel
                            ti_saph.micrometer.speed = -WAVELENGTH_SCAN_SPEED
                            increasing_scan = False

                        # Stop, record data once we go back to start
                        if 700 < wavelength < START_WAVELENGTH and not increasing_scan:
                            break

                        time.sleep(0.2) 
                except:
                    ti_saph.micrometer.off()
                    break

                print()
