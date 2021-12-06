import time
import os, shutil
from pathlib import Path
import numpy as np


#Import class objects
from headers.CTC100 import CTC100
from headers.mfc import MFC
from headers.pulse_tube import PulseTube
from headers.turbo import TurboPump
from headers.ti_saph import TiSapphire
from headers.filter_wheel import FilterWheel
from usb_power_meter.Power_meter_2 import PM16 

from api.pump_laser import EOM, MountedBandpass, PumpLaser
from api.ablation import AblationSystem

MINUTE = 60
HOUR = 60 * MINUTE


# Initialize devices.
# Port numbers are defined in multiplexer.py.
#T1 = CTC100(31415)
#T2 = CTC100(31416)
#mfc = MFC(31417)
#turbo = TurboPump()
#pt = PulseTube()

#eom = EOM()
#bandpass = MountedBandpass()
pump = PumpLaser()
#pm = PM16('/dev/power_meter')

#ablation = AblationSystem()

## Uncomment whatever commands you want and run the file ##
#pump.source = 'tisaph'
#pump.ti_saph.verdi.power = 8
#while True:
#    print(pump)
#    pump.wavelength = int(input('Wavelength? '))
#
#print(bandpass.wavelength)
#
#eom.high = 5
#eom.low = 0
#eom.frequency = 0.05

#mfc.flow_rate_cell = 10
#mfc.flow_rate_neon_line = 0
#mfc.off()
#time.sleep(1*HOUR)
#turbo.on()
#turbo.off()

#pt.on()
#pt.off()

#cracking crystal procedure
#print('cracking')
#T1.enable_output()
#T2.enable_output()
#T1.ramp_temperature('heat saph', 11.0, 0.5)
#T1.ramp_temperature('heat saph', 7.0 , 0.5)
#T1.ramp_temperature('heat saph', 11.0, 0.5)
#T1.ramp_temperature('heat saph', 5.0, 0.5)
#T1.ramp_temperature('heat saph',11.0, 0.5)
#T1.ramp_temperature('heat saph',4.5, 0.5 )
#T1.ramp_temperature('heat saph',12.0, 0.5)
#T1.disable_output()
