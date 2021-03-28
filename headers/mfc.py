'''
EDM labjack communication -- MFC
To set up MFC for different gases, see MKS MFC Web Browser Tutorial.
Initialization sometimes works, sometimes doesn't. Maybe reinstall labjack_ljm_software newer version.
'''

from Labjack import Labjack
import time

#%% SETUP MASS FLOW CONTROLLER 470021124

class MFC():
    def __init__(self, serial_number):
        self.handle = Labjack(serial_number)
        self.calibration = 10.0/5.0 #How many sccm per volt?

    def get_flow_rate_cell(self):
        val = self.handle.read("AIN0")
        FlowRate = val*self.calibration
        return FlowRate

    def set_flow_rate_cell(self,flowrate):             #0.0V = flow is off; 5.0V = open valve
        self.handle.write("DAC0", flowrate/self.calibration)   #MFC flow is off (0 to 5 VDC givs 0 to 10 sccm)
        time.sleep(0.5) #Takes about 0.5s to ramp up the flow.
        val = self.get_flow_rate_cell()
        print ("Flow setpoint = {:3f}, Current flow rate = {:3f}".format(flowrate,val)+'sccm.\n')

    def get_flow_rate_neon_line(self):
        val = self.handle.read("AIN1")
        FlowRate = val*self.calibration
        return FlowRate

    def set_flow_rate_neon_line(self,flowrate):        #0.0V = flow is off; 5.0V = open valve
        self.handle.write("DAC1", flowrate/self.calibration)   #MFC flow is off (0 to 5 VDC givs 0 to 10 sccm)
        time.sleep(0.5) #Takes about 0.5s to ramp up the flow.
        val = self.get_flow_rate_neon_line()
        print ("Flow setpoint = {:3f}, Current flow rate = {:3f}".format(flowrate,val)+'sccm.\n')

    def close(self):
        self.set_flow_rate_neon_line(0.0)
        self.set_flow_rate_cell(0.0)
        self.handle.close()
        print('MFC LabJack Closed.\n')

    def off(self):
        self.set_flow_rate_neon_line(0.0)
        self.set_flow_rate_cell(0.0)