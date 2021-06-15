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
        self._calibration = 10.0/5.0 #How many sccm per volt?

    def _get_flow_rate(self, channel):
        val = self.query(f'AIN{channel}')
        if val is None: return None
        val = ufloat(*map(float, val.split()))
        return val * self._calibration

    async def _async_get_flow_rate(self, channel):
        val = await self.async_query(f'AIN{channel}')
        if val is None: return None
        val = ufloat(*map(float, val.split()))
        return val * self._calibration

    def _set_flow_rate(self, flowrate, channel): #0.0V = flow is off; 5.0V = open valve
        self.send_command(f'DAC{channel} {flowrate/self._calibration:.8f}')   #MFC flow is off (0 to 5 VDC givs 0 to 10 sccm)
        time.sleep(1.0) #Takes about 1s to ramp up the flow.
        val = self._get_flow_rate(channel)
        current = f'{val:.3f}' if val is not None else None
        print(f'Flow setpoint = {flowrate:3f}, Current flow rate = {current} sccm.')


    @property
    def flow_rate_cell(self): return self._get_flow_rate(0)

    @flow_rate_cell.setter
    def flow_rate_cell(self, flowrate): self._set_flow_rate(flowrate, 0)
    
    @property
    def flow_rate_neon_line(self): return self._get_flow_rate(1)

    @flow_rate_neon_line.setter
    def flow_rate_neon_line(self, flowrate): self._set_flow_rate(flowrate, 1)

    async def async_get_flow_rate_cell(self):
        return await self._async_get_flow_rate(0)

    async def async_get_flow_rate_neon_line(self):
        return await self._async_get_flow_rate(1)

    def off(self):
        self.flow_rate_neon_line = 0
        self.flow_rate_cell = 0
