import numpy as np

class FringeCounter:
    """Fringe counter based on hysterisis around 1."""

    def __init__(self, threshold=0.02, buffer_size=50):
        self.threshold = threshold
        self.buffer_size = buffer_size

        self._buffer = []
        self.reset()

        # Whether above or below threshold (with some hysteresis)
        self._state = True


    def update(self, value, grow=True):
        new_state = self._state

        self._buffer.append(np.square(value-1))
        self._buffer = self._buffer[-self.buffer_size:]
        self.amplitude = 100 * np.sqrt(2 * np.mean(self._buffer))

        if value < 1 - self.threshold:
            new_state = False

        if value > 1 + self.threshold:
            new_state = True

        if new_state != self._state:
            delta = 0.5 if grow else -0.5
            self.fringe_count += delta
        self._state = new_state

    def reset(self):
        self.fringe_count = 0
        self.amplitude = 0
        self._buffer = []

    @property
    def thickness(self):
        """Returns film thickness in microns."""
        return self.fringe_count * 0.407
