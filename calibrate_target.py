import time
import math

import numpy as np

from api.ablation_hardware import AblationHardware

from headers.util import unweighted_mean

ablation = AblationHardware(mirror_speed = 1000)

def random_point():
    """Return random point in a circle."""
    while True:
        x = np.random.uniform(-200, 200)
        y = np.random.uniform(-200, 200)
        if math.hypot(x, y) > 200**2: continue
        return (x+650, y+550)


last_point = (650, 550)
with open('calibration/target_map.txt', 'a') as f:
    while True:
        point = random_point()
        if math.hypot(point[0]-last_point[0], point[1] - last_point[1]) > 30: continue
        print(point)

        try:
            ablation.position = point
        except ValueError:
            print('Spot disappeared, trying another location.')
            continue

        last_point = point

        position_samples = []
        intensity_samples = []
        for i in range(20):
            position_samples.append(ablation.position)
            intensity_samples.append(ablation.hene_intensity)
            if i % 5 == 0: print(ablation._delay, position_samples[-1])
            time.sleep(0.1)

        xs, ys = zip(*position_samples)
        x = unweighted_mean(xs)
        y = unweighted_mean(ys)
        intensity = unweighted_mean(intensity_samples)

        print(x, y, intensity)
        print(f'{point[0]} {point[1]} {x.n} {x.s} {y.n} {y.s} {intensity.n} {intensity.s}', file=f, flush=True)
