"""
Allows real-time control of the ablation mirror with WASD keys.
"""
from headers.mirror_mount import microcontroller


mirror = microcontroller()

class _GetchUnix:
    def __init__(self):
        import tty, sys

    def __call__(self):
        import sys, tty, termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

getch = _GetchUnix()


print('Use WASD to move ablation spot. Press Q to quit.')

while True:
    note = getch()

    if note == 'q': break

    if note == 'w': mirror.move(1, -400)
    if note == 's': mirror.move(1, 400)
    if note == 'a': mirror.move(2, -400)
    if note == 'd': mirror.move(2, 400)
