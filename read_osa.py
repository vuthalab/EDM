import time

from headers.ando_aq6317 import AndoAQ6317

serial_port = '/dev/ttyUSB3' # TODO remap the serial port to something human-readable
gpib_address = 1 # Configurable on the OSA

# Initialize connection
with AndoAQ6317(serial_port, gpib_address) as osa:

    ###### Configure capture settings #####
    osa.active_trace = 'c' # choose which trace to read

    osa.resolution = 0.2 # set resolution (nm)
    osa.range = (500, 1000) # set range (nm)
    #osa.center() # self-center
    #osa.scale = 'log'

    #osa.sweep_mode = 'repeat' # continuously sweep (for logging)
    osa.trigger() # trigger once

    # Display configuration
    print('Getting configuration...')
    print(osa)
    print()

    # Wait for trigger, then plot trace
    time.sleep(0.5)
    osa.quick_plot()
