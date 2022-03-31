"""
Cools down the experiment from room temperature. Takes ~12 hours to run.

Make sure the roughing pump is on before running.
"""
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

# Ensure MFC, pulse tube are off.
mfc.off()
assert not pt.is_on()

# [Optional] Bake sorbs to reduce final pressure
#T2.ramp_temperature('srb45k out', 320, 0.5)
T2.ramp_temperature('heat cell', 4, 1)
T2.enable_output()

# [Optional] Pause to schedule cooldown
countdown_for(0*HOUR)

# Wait for pressure to drop sufficiently, then enable turbo.
wait_until_quantity(
    ('pressure',), '<', 0.5,
    unit='torr', source='pressure',
)
turbo.on()

# Wait for pressure to drop sufficiently, then enable pulse tube.
wait_until_quantity(
    ('pressure',), '<', 1.5e-5,
    unit='torr', source='pressure',
)
print('Turning on pulse tube.')
pt.on()

# Slowly ramp down the saph temperature to liquid nitrogen temp.
T1.ramp_temperature('heat saph', 77, 1e-2)
T1.ramp_temperature('heat mirror', 4, 1)
T2.ramp_temperature('srb45k out', 4, 1)
T1.enable_output()
T2.disable_output()


# Wait for 45K plateto drop below 70 K, to get rid of all nitrogen.
wait_until_quantity(
    ('temperatures', '45k plate'), '<', 70,
    unit='K', source='ctc',
)


# Let system cool naturally.
T1.ramp_temperature('heat saph', 4, 1)
T1.ramp_temperature('heat mirror', 10, 1)
