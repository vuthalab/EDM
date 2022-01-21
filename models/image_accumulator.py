import numpy as np


class ImageAccumulator:
    """
    Allows computation of the mean and standard deviation
    of many arrays without storing any of the arrays.

    Call update(arr) once for each array arr.
    """

    def __init__(self):
        self._n = 0 # Number of images
        self._mean = None # Number of images
        self._M2 = None # Number of images

    def __len__(self): return self._n

    def update(self, arr):
        """Uses Welford's online algorithm to perform an update pass."""
        self._n += 1
        if len(self) == 1:
            self._mean = 1. * arr
            self._M2 = 0. * arr
            return

        delta = arr - self._mean
        self._mean += delta/self._n
        delta2 = arr - self._mean
        self._M2 += delta * delta2

    @property
    def mean(self): return self._mean

    @property
    def variance(self): return self._M2/self._n

    @property
    def std(self): return np.sqrt(self.variance)

    @property
    def stderr(self): return self.std / np.sqrt(len(self))

    @property
    def meanstderr(self): return np.array([self.mean, self.stderr])
