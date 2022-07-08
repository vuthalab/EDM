import time
import itertools
import numpy as np

from api.pump_laser import PumpLaser
from api.ablation import AblationSystem
from api.crystal import CrystalSystem
from api.fluorescence import FluorescenceSystem

from headers.util import nom, std


# List of temperatures to run at.
temperatures = np.linspace(4.8, 8, 33)
np.random.shuffle(temperatures)

# Connect to devices
ablation = AblationSystem(start_position=0, move_threshold=1)
crystal = CrystalSystem()
optics = FluorescenceSystem(ximea_exposure=1, pump_source='tisaph-high')


for RUN in itertools.count(6):
    try:
        for temp in temperatures:
            print(f'Running at {temp:.2f} K.')
            optics.pump.source = None

            # Grow new crystal at specified temperature.
            crystal.melt(melt_temp = 20, melt_time = 60, speed=0.5)
            crystal.anneal()
            crystal.grow(temperature = temp)

            # Ablate for 60 seconds during crystal growth.
            times = []
            dips = []
            ablation.on()
            try:
                for (ts, n, pos, dip_size) in ablation.ablate_continuously():
                    if ts > 60: break
                    times.append(ts)
                    dips.append(dip_size)
            finally:
                ablation.off()

            # Stop crystal growth.
            crystal.stop(base_temperature = 5.5)


            # Take rate data
            optics.take_background(n_samples = 20)
            data = optics.take_samples(n_samples = 20)
            rate = data['rate']
            power = data['power']

            # Save file.
            np.savez(
                f'sticking-factor/{temp:.2f}K-run{RUN}.npz',
                ts = time.time(),
                dip_times = [nom(times), std(times)],
                dips = [nom(dips), std(dips)],
                rate = [rate.n, rate.s],
                power = [power.n, power.s],
                temperature = temp,
            )
    finally:
        crystal.stop()
        ablation.off()
