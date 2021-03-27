'''
EDM labjack communication -- MFC
To set up MFC for different gases, see MKS MFC Web Browser Tutorial.
Initialization sometimes works, sometimes doesn't. Maybe reinstall labjack_ljm_software newer version.
'''

from Labjack import Labjack
from labjack import ljm

#%% SETUP MASS FLOW CONTROLLER 470021124

class MFC():
    def __init__(self, serial_number):
        self.handle = Labjack(serial_number)

    def get_flow_rate_cell(self):
        val = self.handle.read("AIN0")
        FlowRate = val*10.0/5.0
        return FlowRate

    def set_flow_rate_cell(self,flowrate):                              # 0.0 = flow is off; 5.0 = open valve
        ljm.eWriteName(self.handle, "DAC0", flowrate*5.0/10.0)   #MFC flow is off (0 to 5 VDC givs 0 to 10 sccm)
        val = self.get_flow_rate_cell()
        print ("Flow Set AIN0 = {:3f}, FlowRate = {:3f}".format(val,val*10.0/5.0)+'sccm')

    def get_flow_rate_neon_line(self):
        val = self.handle.read("AIN1")
        FlowRate = val*10.0/5.0
        return FlowRate

    def set_flow_rate_neon_line(self,flowrate):                              # 0.0 = flow is off; 5.0 = open valve
        ljm.eWriteName(self.handle, "DAC1", flowrate*5.0/10.0)   #MFC flow is off (0 to 5 VDC givs 0 to 10 sccm)
        val = self.get_flow_rate_neon_line()
        print ("Flow Set AIN1 = {:3f}, FlowRate = {:3f}".format(val,val*10.0/5.0)+'sccm')

    def close(self):
        self.set_flow_rate_neon_line(0.0)
        self.set_flow_rate_cell(0.0)
        ljm.close(self.handle)
        print('MFC LabJack Closed')

    def off():
        self.set_flow_rate_neon_line(0.0)
        self.set_flow_rate_cell(0.0)