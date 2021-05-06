from headers.ando_aq6317 import AndoAQ6317

serial_port = '/dev/ttyUSB0' # TODO remap the serial port to something human-readable
gpib_address = 1 # Configurable on the OSA

# Initialize connection
osa = AndoAQ6317(serial_port, gpib_address)
print(osa)
print()

# Trigger OSA and plot trace
osa.active_trace = 'A'
osa.range = (800, 890)
osa.trigger()
osa.quick_plot()

osa.stop()
