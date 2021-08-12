import time

from pulsetube_compressor import PulseTube
from headers.turbo import TurboPump
from headers.CTC100 import CTC100
from headers.mfc import MFC

from headers.edm_util import countdown_for, wait_until_quantity


MINUTE = 60
HOUR = 60 * MINUTE


# Initialize devices.
# Port numbers are defined in multiplexer.py.
T1 = CTC100(31415)
T2 = CTC100(31416)
mfc = MFC(31417)
turbo = TurboPump()
pt = PulseTube()

# Optional pause
#countdown_for(10 * MINUTE)

# Turn off everything.
mfc.off()
T1.disable_output()
T2.disable_output()
turbo.off()


# Wait for turbo to spin down, then turn off pulsetube.
countdown_for(3 * MINUTE)
pt.off()



# [Optional] Accelerate warmup.
#T1.enable_output()
#T2.enable_output()
#T1.ramp_temperature('heat saph', 310, 0.5)
#T2.ramp_temperature('srb45k out', 310, 0.5)
#T2.ramp_temperature('srb4k out', 310, 0.5)

# Wait for room temperature.
#wait_until_quantity(
#    ('temperatures', 'saph'), '>', 300,
#    unit='K'
#)
