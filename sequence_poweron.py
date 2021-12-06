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

# Ensure MFC is off.
mfc.off()

# Optional pause
countdown_for(0*HOUR)

# Wait for pressure to drop sufficiently,  then enable turbo.
wait_until_quantity(
    ('pressure',), '<', 0.5,
    unit='torr', source='pressure',
)
if turbo.operation_status != 'normal':
    # If not started, turn on and wait for spinup.
    turbo.on()
    countdown_for(1*MINUTE)

# Ensure system is cool (optional).
T1.disable_output()
T2.disable_output()
wait_until_quantity(
    ('temperatures', 'srb45k',), '<', 320,
    unit='K', source='ctc',
)


# Wait for pressure to drop sufficiently.
wait_until_quantity(
    ('pressure',), '<', 1.5e-5,
    unit='torr', source='pressure',
)

# Slowly ramp down the saph temperature to liquid nitrogen temp.
T1.ramp_temperature('heat saph', 77, 1e-2)
T1.ramp_temperature('heat coll', 77, 1e-2)
T1.enable_output()
T2.disable_output()
pt.on()


# Wait for 45K sorb to drop below 70 K.
wait_until_quantity(
    ('temperatures', 'srb45k'), '<', 70,
    unit='K', source='ctc',
)


# Let system cool naturally.
T1.disable_output()
