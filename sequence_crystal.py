"""
Grow a BaF-doped crystal.
"""
import time

from colorama import Fore, Style

from api.crystal import CrystalSystem
from api.ablation import AblationSystem

GROWTH_TIME = 200 # seconds
GROWTH_TEMPERATURE = 4.8 # K


# Initialize systems
ablation = AblationSystem(start_position=3788) 
crystal = CrystalSystem()


print('DOUBLE CHECK START POSITION BEFORE RUNNING! (api/ablation.py)')
input(f'{Fore.RED}Press Enter to start growth and ablation, or press Ctrl + C to cancel.{Style.RESET_ALL}')


#crystal.melt()
crystal.melt(end_temp = 12)
crystal.anneal()
crystal.grow(temperature = GROWTH_TEMPERATURE)

ablation.on()
try:
    with open('ablation_progress.txt', 'a') as f:
        for (ts, n, pos, dip_size) in ablation.ablate_continuously():
            print(ts, n, pos[0].n, pos[1].n, dip_size, file=f, flush=True)

            if ts > GROWTH_TIME: break
finally:
    ablation.off()
    crystal.stop()
