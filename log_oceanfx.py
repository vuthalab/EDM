import time
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

from headers.oceanfx import OceanFX

from headers.util import nom, std, plot


##### Parameters #####
root_dir = Path('~/Desktop/edm_data/logs/oceanfx/').expanduser()
log_file = root_dir / (time.strftime('%Y-%m-%d %H꞉%M꞉%S') + '.txt')

def format_array(arr):
    return ' '.join(f'{x:.6f}' for x in arr)

spec = OceanFX()

# Liveplot
if False:
    plt.ion()
    fig = plt.figure()
    while True:
        spec.capture(32)
        plot(spec.wavelengths, spec.intensities, continuous=True)
        fig.canvas.draw()
        fig.canvas.flush_events()
        time.sleep(0.5)


with open(log_file, 'a') as f:
    print(format_array(spec.wavelengths), file=f)
    while True:
        start = time.monotonic()
        spec.capture(n_samples=16384)

        print(time.time(), format_array(nom(spec.intensities)), format_array(std(spec.intensities)), file=f)

        elapsed = time.monotonic() - start
        time.sleep(max(0, 20 - elapsed))
