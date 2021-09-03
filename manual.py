import time
import os, shutil
from pathlib import Path
import numpy as np


#Import class objects
from headers.CTC100 import CTC100
from headers.mfc import MFC
from pulsetube_compressor import PulseTube
from headers.turbo import TurboPump
from headers.ti_saph import TiSapphire

MINUTE = 60
HOUR = 60 * MINUTE


# Initialize devices.
# Port numbers are defined in multiplexer.py.
T1 = CTC100(31415)
T2 = CTC100(31416)
mfc = MFC(31417)
turbo = TurboPump()
pt = PulseTube()
#ti_saph = TiSapphire()


## Uncomment whatever commands you want and run the file ##
#mfc.flow_rate_cell = 10
#mfc.flow_rate_neon_line = 0
mfc.off()
#time.sleep(1*HOUR)
#turbo.on()

#ti_saph.wavelength = 888

#print(ti_saph.wavelength)

#T1.enable_output()
#T2.enable_output()
#T1.ramp_temperature('heat saph', 90.0, 1.0)
#T1.ramp_temperature('heat coll', 90.0, 1.0)

#T1.ramp_temperature('heat saph', 30, 1.0)
#T1.ramp_temperature('heat coll', 320, 1.0)
#T2.ramp_temperature('srb4k out', 320, 1.0)
#T2.ramp_temperature('srb45k out', 320, 1.0)
#time.sleep(30 * MINUTE)

#time.sleep(2 * HOUR)
#T1.disable_PID('heat saph')
#T1.disable_PID('heat coll')
#T2.disable_PID('srb4k out')
#T2.disable_PID('srb45k out')
#T1.disable_output()
#T2.disable_output()
