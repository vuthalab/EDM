from headers.CTC100 import CTC100

a = CTC100('192.168.0.107')
print(a.channels)
a.close()
