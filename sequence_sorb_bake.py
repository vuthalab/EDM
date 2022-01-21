import time

from headers.pulse_tube import PulseTube
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


assert not pt.is_on()

# Turn turbo off before bake.
#if turbo.operation_status == 'normal': turbo.off()

# Bake sorbs.
T2.ramp_temperature('srb45k out', 320, 0.5)
T2.ramp_temperature('srb4k out', 320, 0.5)
T2.enable_output()

# Wait for a while, then end bake.
#time.sleep(90 * MINUTE)
#T2.disable_output()
