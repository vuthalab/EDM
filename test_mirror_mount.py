import time

from headers.mirror_mount import microcontroller

mc = microcontroller()
mc.home()

print('Homed')
print(mc.get_xy_position())
time.sleep(2)

mc.music_scan()
