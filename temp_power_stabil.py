import time

import numpy as np
import matplotlib.pyplot as plt

from api.pump_laser import PumpLaser
from api.power_stabilizer import PowerStabilizer
from headers.util import unweighted_mean, plot

pump = PumpLaser()

pump.ti_saph.verdi.power = 8
pump.eom.frequency = 10e6
pump.eom.start_pulse()
#pump.source = 'tisaph-low'
pump.source = 'tisaph-high'

print(pump.polarization)

#stabilizer = PowerStabilizer(pump, setpoint=0.9)
stabilizer = PowerStabilizer(pump, setpoint=25, sensitivity=19)

# PID Loop
powers = []
while True:
    power, error, gain = stabilizer.update()
    powers.append(power)

    if len(powers) > 20:
        stability = np.std(powers[20:]) / np.mean(powers[20:])
    else:
        stability = 0
    print(f'{power:.4f} mW | Gain: {gain:.3f} V | Stability: {stability * 100} %')
    time.sleep(0.5)
