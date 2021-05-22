from simple_pyspin import Camera

import matplotlib.pyplot as plt

with Camera() as cam:
    cam.start()
    image = cam.get_array()
    cam.stop()

plt.imshow(image)
plt.show()
