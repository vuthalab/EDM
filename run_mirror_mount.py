import time

from headers.mirror_mount import microcontroller

mc = microcontroller()
#mc.home()

#print('Homed')
#print(mc.get_xy_position())
#time.sleep(2)

input('Press enter once on pulse tube beat')
mc.music_scan()

#mc.play_song('prelude_c_minor')
