import serial

class FilterWheel:
    def __init__(self, path='/dev/filter_wheel'):
        self._conn = serial.Serial(path, 115200, timeout=0.1)

    def _query(self, command):
        self._conn.write(command.encode('utf-8') + b'\r')
        return self._conn.readline() + self._conn.readline()

    @property
    def position(self):
        return int(self._query('pos?').split(b'\r')[-2])

    @position.setter
    def position(self, pos: int):
        assert 1 <= pos <= 6
        self._query(f'pos={pos:.0f}')


if __name__ == '__main__':
    wheel = FilterWheel()
