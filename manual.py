import time
import os, shutil
from pathlib import Path

import numpy as np


#Import class objects
from headers.CTC100 import CTC100
from headers.mfc import MFC


# Initialize devices.
# Port numbers are defined in multiplexer.py.
T1 = CTC100(31415)
T2 = CTC100(31416)
mfc = MFC(31417)

## Uncomment whatever commands you want and run the file ##
#mfc.flow_rate_cell = 5
#mfc.flow_rate_neon_line = 10
#mfc.off()

T1.enable_output()
T1.ramp_temperature('heat saph', 9.0, 0.1)

#T1.disable_output()
