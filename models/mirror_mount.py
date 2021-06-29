import numpy as np

# Keeps track of a local gradient estimate for dip size vs mirror displacement.

class MirrorModel:
    def __init__(self, buffer_size=16):
        self._dI_dr = []
        self.buffer_size = buffer_size

    def update(self, dx, dy, dI):
        self._dI_dr.append((dx, dy, dI))
        self._dI_dr = self._dI_dr[-self.buffer_size:]

    @property
    def gradient(self):
        if len(self._dI_dr) < 3: return [0, 0]

        # Fit linear model
        data = np.array(self._dI_dr).T

        # 1D
        X, Y = data[1:2], data[-1]
        return [0, np.linalg.inv(X @ X.T) @ X @ Y]

        # 2D
#        X, Y = data[:2], data[-1]
#        return np.linalg.inv(X @ X.T) @ X @ Y

