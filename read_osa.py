import time

from headers.ando_aq6317 import AndoAQ6317

serial_port = '/dev/ttyUSB0' # TODO remap the serial port to something human-readable
gpib_address = 1 # Configurable on the OSA

# Initialize connection
osa = AndoAQ6317(serial_port, gpib_address)

###### Configure capture settings #####
#osa.active_trace = 'c'

#osa.resolution = 0.01 # nm
#osa.range = (600, 660) # nm
#osa.center()
#osa.scale = 'log'

#osa.sweep_mode = 'repeat'

# Display configuration
print('Getting configuration...')
print(osa)
print()

# Wait for trigger, then plot trace
time.sleep(0.5)
osa.quick_plot()

#osa.stop()
