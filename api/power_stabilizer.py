import time

class PowerStabilizer:
    def __init__(
            self,
            pump_laser,

            setpoint = 2, # mW
            sensitivity = 1, # mW/V

#            setpoint = 3, # mW
#            sensitivity = 1.5, # mW/V

#            setpoint = 15, # mW
#            sensitivity = 10, # mW/V

#            setpoint = 30, # mW
#            sensitivity = 15, # mW/V

            P = 0.1,
            I = 0.3,
        ):
        self.pump = pump_laser
        self.setpoint = setpoint
        self.sensitivity = sensitivity
        self.P = P
        self.I = I

        self.reset()


    def reset(self, reset_accumulator=True):
        self.last_update = time.monotonic()
        if reset_accumulator:
            self.accumulator = 0


    def update(self):
        dt = time.monotonic() - self.last_update
        self.last_update = time.monotonic()

        power = self.pump.power
        error = power - self.setpoint
        if dt < 5: self.accumulator += dt * error

        correction = self.P * error + self.I * self.accumulator
        gain = 4-correction/self.sensitivity
        gain = max(0, min(gain, 5))
        self.pump.eom.gain = gain

        return (power, error, gain)
