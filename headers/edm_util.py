import time
from datetime import datetime

import numpy as np

from PIL import Image, ImageFont, ImageDraw

from colorama import Fore, Style
from uncertainties import ufloat

from headers.util import display

font = ImageFont.truetype('headers/cmunrm.ttf', 24)





def deconstruct(val): 
    """Deconstructs an uncertainty object into a tuple (value, uncertainty)"""
    if val is None: return None
    return (val.n, val.s)


def add_timestamp(image):
    short_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    pad_size = [(32, 0), (0, 0)]
    fill = 255

    if len(image.shape) == 3:
        pad_size.append((0, 0))
        fill = (255, 255, 255)

    image = np.pad(image, pad_size)
    image = Image.fromarray(image)
    draw = ImageDraw.Draw(image)
    draw.text((8, 4), short_timestamp, fill=fill, font=font)
    return image


## nice print function
def print_tree(obj, indent=0):
    for key, value in sorted(obj.items()):
        print('   ' * indent + f'{Fore.YELLOW}{key}{Style.RESET_ALL}', end='')

        if isinstance(value, dict):
            print()
            print_tree(value, indent=indent+1)
        else:
            if isinstance(value, tuple):
                value = display(ufloat(*value))
            print(':', value)


class Timer:
    """Context manager for timing code."""
    def __init__(self, name=None, times=None):
        self.name = name
        self._times = times

    def __enter__(self):
        self.start = time.monotonic()
        print(f'  [{Fore.BLUE}INFO{Style.RESET_ALL}] {Style.DIM}Reading {Style.RESET_ALL}{Style.BRIGHT}{self.name}{Style.RESET_ALL}')

    def __exit__(self, exc_type, exc_value, traceback):
        dt = time.monotonic() - self.start
        print(f'  [{Fore.BLUE}INFO{Style.RESET_ALL}] {Style.DIM}Reading {self.name} took {Style.RESET_ALL}{Style.BRIGHT}{dt:.3f} seconds{Style.RESET_ALL}')
        if self._times is not None:
            self._times[self.name] = round(1e3 * dt)

