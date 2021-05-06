from headers.rigol_ds1102e import RigolDS1102e

ip_address = '192.168.0.131'

# Initialize connection
scope = RigolDS1102e(ip_address)
print(scope)

#scope.stop()
