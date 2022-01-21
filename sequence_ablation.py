import time
import sys

import numpy as np

from colorama import Fore, Style

from api.ablation import AblationSystem


# Initialize ablation system
ablation = AblationSystem(start_position=0)
input(f'{Fore.RED}Press Enter to start ablation, or press Ctrl + C to cancel.{Style.RESET_ALL}')
ablation.on()

try:
    start_time = time.monotonic()
    with open('ablation_progress.txt', 'a') as f:
        for (n, pos, dip_size) in ablation.ablate_continuously():
            ts = time.monotonic() - start_time
            print(f'{ts:7.3f} s | {n:05d} | ({pos[0]:.3f}, {pos[1]:.3f}) pixels | {dip_size:5.2f} % dip')
            print(ts, n, pos[0].n, pos[1].n, dip_size, file=f, flush=True)
finally:
    ablation.off()
