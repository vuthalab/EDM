import time

from headers.zmq_client_socket import connect_to
from models.mirror_mount import MirrorModel

from headers.mirror_mount import microcontroller

mc = microcontroller()
mc.music_scan(amplitude=1)


# Annoy camilo
mc.client_socket = connect_to('scope')
mc.client_socket.make_connection()
mc.model = MirrorModel()
mc.play_song('ice_ice_baby', amplitude=1)
