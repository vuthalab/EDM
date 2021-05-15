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
mfc.flow_rate_cell = 0
mfc.flow_rate_neon_line = 3

#T1.disable_output()
