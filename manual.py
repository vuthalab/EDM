import time
import os, shutil
from pathlib import Path

import numpy as np


#Import class objects
from headers.CTC100 import CTC100
from headers.mfc import MFC


MINUTE = 60
HOUR = 60 * MINUTE


# Initialize devices.
# Port numbers are defined in multiplexer.py.
T1 = CTC100(31415)
T2 = CTC100(31416)
mfc = MFC(31417)

## Uncomment whatever commands you want and run the file ##
#mfc.flow_rate_cell = 10
#mfc.flow_rate_neon_line = 8
#mfc.off()

#T1.enable_output()
#T2.enable_output()
#T1.ramp_temperature('heat saph', 5.0, 0.016)
#T1.ramp_temperature('heat coll', 30.0, 1.0)

#T1.ramp_temperature('heat saph', 300, 1.0)
#T1.ramp_temperature('heat coll', 300, 1.0)
#T2.ramp_temperature('srb4k out', 320.0, 1.0)
#T2.ramp_temperature('srb45k out', 320.0, 1.0)

#time.sleep(2 * HOUR)

#T1.disable_output()
#T2.disable_output()
