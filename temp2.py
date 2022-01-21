import numpy as np
import matplotlib.pyplot as plt

ts, n, x, y, dip = np.loadtxt('ablation_progress.txt').T

plt.scatter(
    x, y,
#    s=4 * dip**2,
    s=10,
    alpha=dip/4
)
plt.xlim(600, 900)
plt.ylim(450, 700)
plt.show()
