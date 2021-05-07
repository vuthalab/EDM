from headers.rigol_dg4162 import RigolDG4162

ip_address = '192.168.0.131'

# Initialize connection
scope = RigolDG4162(ip_address)
print(scope)

#scope.stop()
