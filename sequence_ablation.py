import time
import sys

import numpy as np
import matplotlib.pyplot as plt

from colorama import Fore, Style

from headers.mfc import MFC
from api.ablation import AblationSystem

# Ensure neon is flowing
mfc = MFC(31417)
assert mfc.flow_rate_cell > 2

# Initialize ablation system
ablation = AblationSystem()

# Auxiliary functions
center = np.array([700, 550]) # Center of target (pixels) on camera
RADIUS = 150 # radius (pixels) of target on camera
def spiral(n):
    """Given an integer n, returns the location n steps along a spiral pattern out from the center."""
    assert n >= 0
    theta = 5 * np.sqrt(n) # radians
    r = theta/3 # pixels
    assert r <= 150
    return center + r * np.array([np.cos(theta), np.sin(theta)])

def exit():
    """Turn off all systems and exit."""
    ablation.off()
    sys.exit()


# Begin initial (slow) ablation
ablation.position = center + np.random.uniform(size=2, low=-50, high=50)
input(f'{Fore.RED}Press Enter to start ablation, or press Ctrl + C to cancel.{Style.RESET_ALL}')
ablation.frequency = 2
ablation.on()

# Wait for absorption signal
print('Waiting for absorption signal...')
for i in range(20):
    dip_size = ablation.dip_size
    print(f'Dip Size: {dip_size:5.2f}%', end='\r')
    if dip_size > 10: break
    time.sleep(0.5)
else:
    print('Absorption signal not detected, exiting!')
    exit()

# Begin full ablation
ablation.frequency = 30

plt.axis([center[0]-RADIUS, center[0]+RADIUS, center[1] - RADIUS, center[1] + RADIUS])
plt.xlabel('X Position')
plt.ylabel('Y Position')
plt.title('Ablation Progress')

try:
    start_time = time.monotonic()
    with open('ablation_progress.txt', 'a') as f:
        for n in range(5000):
            point = spiral(n)
            print(n, point)

            ablation.position = point

            # Safety checks
            assert ablation.hene_intensity > 20
            assert mfc.flow_rate_cell > 2

            plt.scatter(*point, color='C0', alpha=0.6, s=2)
            plt.pause(0.05)

            while True:
                ts = time.monotonic() - start_time
                dip_size = ablation.dip_size
                pos = ablation.position

                print(f'{ts:7.3f} s | {n:05d} | ({pos[0]:.3f}, {pos[1]:.3f}) pixels | {dip_size:5.2f} % dip')
                print(ts, n, pos[0].n, pos[1].n, dip_size, file=f, flush=True)

                if dip_size < 10: break
                plt.pause(0.5)
        plt.show()
finally:
    ablation.off()
