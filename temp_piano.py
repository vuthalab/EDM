from headers.mirror_mount import microcontroller, NOTES

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

MAP = {
    'a': 'C_',
    'w': 'C#_',
    's': 'D_',
    'e': 'D#_',
    'd': 'E_',
    'f': 'F_',
    't': 'F#',
    'g': 'G',
    'y': 'G#',
    'h': 'A',
    'u': 'A#',
    'j': 'B',
    'k': 'C',
    'o': 'C#',
    'l': 'D',
    'p': 'D#',
    ';': 'E',
    "'": 'F',
}

getch = _GetchUnix()

sign = 1
while True:
#    note = input()
    note = getch()
    print(note)

    if note == 'b': break
    try:
        mirror.abort()
        speed = NOTES[MAP[note.lower()]]
        mirror.set_speed(1, speed)
        dist = round(speed * 0.05)
        mirror.move(1, dist * sign)
        sign *= -1
    except:
        continue
