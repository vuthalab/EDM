"""
Calibration utility for the ablation camera positioning system.
"""

import numpy as np

from headers.util import nom

from api.ablation_hardware import AblationHardware

a = AblationHardware()

data = []
for location in ['top', 'bottom', 'left', 'right']:
    input(f'Steer beam to {location} of chamber window using piezo mirror. Then press enter.')
    pos = np.array(nom(a.position))
    data.append(pos)
    print(*pos)
data = np.array(data)

center = data.mean(axis=0)

r2 = np.sum(np.square(data - center), axis=-1)
radius = np.sqrt(np.mean(r2))

print('Center:', center)
print('Radius:', radius)
print(np.sqrt(r2))

np.save('calibration/ablation_camera.npy', data)
