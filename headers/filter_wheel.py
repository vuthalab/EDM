import serial

class FilterWheel:
    def __init__(self, path='/dev/filter_wheel'):
        self._conn = serial.Serial(path, 115200, timeout=0.1)
        self._position = None

    def _query(self, command):
        self._conn.write(command.encode('utf-8') + b'\r')
        return self._conn.readline() + self._conn.readline()

    @property
    def position(self):
        if self._position is not None: return self._position
        pos = int(self._query('pos?').split(b'\r')[-2])
        self._position = pos
        return pos


    @position.setter
    def position(self, pos: int):
        assert 1 <= pos <= 6
        self._query(f'pos={pos:.0f}')
        self._position = pos


if __name__ == '__main__':
    wheel = FilterWheel()
