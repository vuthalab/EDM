'''
EDM labjack communication -- MFC
To set up MFC for different gases, see MKS MFC Web Browser Tutorial.
Initialization sometimes works, sometimes doesn't. Maybe reinstall labjack_ljm_software newer version.
'''

import time

from headers.usbtmc import USBTMCDevice

from uncertainties import ufloat

#%% SETUP MASS FLOW CONTROLLER 470021124

class MFC(USBTMCDevice):
    def __init__(self, multiplexer_port):
        super().__init__(multiplexer_port, mode='multiplexed', name='MFC')
        self._calibration = [
            30.0,
            14.6,
            20.0,
        ] # How many sccm on each channel when fully open?

    def _get_flow_rate(self, channel):
        val = self.query(f'AIN{channel}')
        if val is None: return None
        val = ufloat(*map(float, val.split()))
        return val/5 * self._calibration[channel]

    def _set_flow_rate(self, flowrate, channel): #0.0V = flow is off; 5.0V = open valve
        self.send_command(f'DAC{channel} {5 * flowrate/self._calibration[channel]:.8f}')
        time.sleep(1.0) #Takes about 1s to ramp up the flow.
        val = self._get_flow_rate(channel)
        current = f'{val:.3f}' if val is not None else None
        print(f'Flow setpoint = {flowrate:.3f}, Current flow rate = {current} sccm.')


    @property
    def flow_rate_cell(self):
        return self.flow_rate_cell_1 + self.flow_rate_cell_2

    @flow_rate_cell.setter
    def flow_rate_cell(self, flowrate):
        self._set_flow_rate(flowrate, 0)

    @property
    def flow_rate_cell_1(self):
        # Temporary hack while MFCs are parallel
        return self._get_flow_rate(0)/3

    @property
    def flow_rate_cell_2(self):
        return self._get_flow_rate(2)

    
    @property
    def flow_rate_neon_line(self): return self._get_flow_rate(1)

    @flow_rate_neon_line.setter
    def flow_rate_neon_line(self, flowrate): self._set_flow_rate(flowrate, 1)


    def off(self):
        self.flow_rate_neon_line = 0
        self.flow_rate_cell = 0
