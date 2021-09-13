import time
from datetime import datetime
import resource

import numpy as np

from PIL import Image, ImageFont, ImageDraw

from colorama import Fore, Style
from uncertainties import ufloat

from headers.zmq_client_socket import connect_to

from headers.util import display

font = ImageFont.truetype('headers/cmunrm.ttf', 24)





def deconstruct(val): 
    """Deconstructs an uncertainty object into a tuple (value, uncertainty)"""
    if val is None: return None
    return (val.n, val.s)


def add_timestamp(image, label=''):
    short_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    pad_size = [(32, 0), (0, 0)]
    fill = 255

    if len(image.shape) == 3:
        pad_size.append((0, 0))
        fill = (255, 255, 255)

    image = np.pad(image, pad_size)
    image = Image.fromarray(image)
    draw = ImageDraw.Draw(image)
    draw.text((8, 4), f'{short_timestamp} {label}', fill=fill, font=font)
    return image


## nice print function
def print_tree(obj, indent=0):
    lines = 0
    for key, value in sorted(obj.items()):
        print('   ' * indent + f'{Fore.YELLOW}{key}{Style.RESET_ALL}', end='')
        lines += 1

        if isinstance(value, dict):
            print()
            lines += 1 + print_tree(value, indent=indent+1)
        else:
            if isinstance(value, tuple):
                value = display(ufloat(*value))
            print(':', value)
    return lines


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




# Countdown utils
def show_interrupt_menu(): input(f'Press {Style.BRIGHT}enter{Style.RESET_ALL} to skip countdown, or press {Style.BRIGHT}Ctrl + C{Style.RESET_ALL} again to exit.')

def countdown_until(t):
    try:
        while True:
            remaining = t - time.monotonic()
            if remaining < 0: break

            m, s = divmod(round(remaining), 60)
            h, m = divmod(m, 60)
            print(f'{Style.BRIGHT}{h:02d}:{m:02d}:{s:02d}{Style.RESET_ALL} {Style.DIM}remaining{Style.RESET_ALL}', end='\r')
            time.sleep(0.5)
    except KeyboardInterrupt:
        show_interrupt_menu()

def countdown_for(dt): countdown_until(time.monotonic() + dt)

def wait_until_quantity(
    qty, operator, target,
    unit='',
    buffer_size=4,
    source='edm-monitor'
):
    label = f'{Style.DIM}.{Style.RESET_ALL}'.join(
        f'{Fore.GREEN}{entry}{Style.RESET_ALL}' for entry in qty
    )

    buff = []

    monitor_socket = connect_to(source)
    try:
        while True:
            _, data = monitor_socket.blocking_read()

            for entry in qty:
                data = data[entry]

            if isinstance(data, float):
                data = ufloat(data, 0)
            else:
                data = ufloat(*data)


            # Keep rolling buffer for stability
            buff.append(data.n)
            buff = buff[-buffer_size:]

            curr = np.mean(buff)
            curr_s = np.std(buff)

            unit_str = f'{Style.DIM}{unit}{Style.RESET_ALL}'
            disp_curr = f'{display(data)} {unit_str}'
            if operator == 'stable to within':
                disp_curr = f'{curr_s} {unit_str}' if len(buff) == buffer_size else f'{Style.DIM}collected {len(buff)}/{buffer_size} samples{Style.RESET_ALL}'
            print(
                f'[{label}]',
                f'{Fore.YELLOW}Target{Style.RESET_ALL}:', operator, target, unit_str,
                '|',
                f'{Fore.YELLOW}Current{Style.RESET_ALL}:', disp_curr,
                end='\r'
            )

            if operator == '>' and curr > target: break
            if operator == '<' and curr < target: break
            if operator == 'stable to within' and curr_s < target and len(buff) == buffer_size: break
    except KeyboardInterrupt:
        show_interrupt_menu()

    monitor_socket.socket.close()
    print()


def memory_usage():
    """Get the current memory usage, in KB."""
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
