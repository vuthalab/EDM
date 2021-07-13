import time

#Import class objects
from pulsetube_compressor import PulseTube
from headers.turbo import TurboPump
from headers.CTC100 import CTC100
from headers.mfc import MFC


MINUTE = 60
HOUR = 60 * MINUTE


# Initialize devices.
# Port numbers are defined in multiplexer.py.
T1 = CTC100(31415)
T2 = CTC100(31416)
mfc = MFC(31417)
turbo = TurboPump()
pt = PulseTube()


# Turn off everything.
mfc.off()
T1.disable_output()
T2.disable_output()
turbo.off()


# Wait for turbo to spin down, then turn off pulsetube.
time.sleep(10 * MINUTE)
pt.off()
