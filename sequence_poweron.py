import time

from headers.pulse_tube import PulseTube
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
countdown_for(0*HOUR)


# Ensure turbo is running.
if turbo.operation_status != 'normal':
    # If not started, turn on and wait for spinup.
    turbo.on()
    countdown_for(1*MINUTE)


# Make sure MFC is on. Slowly ramp down the saph temperature to liquid nitrogen temp.
mfc.off()
T1.enable_output()
T2.disable_output()
T1.ramp_temperature('heat saph', 77, 1e-2)
pt.on()


# Wait for 45K sorb to drop below 70 K.
wait_until_quantity(
    ('temperatures', 'srb45k'), '<', 70,
    unit='K'
)


# Let system cool naturally.
T1.disable_output()
