# Labjack class that opens and closes the handle before and after every read/write. Will try max_attempts number of times in case the labjack is busy in another python shell.

from labjack import ljm
import time as time
import numpy as np
from datetime import datetime
import sys
import os
import threading

OFFSET = -0.018 #V, measured offset from zero volts

#os.chdir('/home/labuser/googledrive/Calcium/code/calcium_control')
#from zmq_publisher import zmqPublisher

class Labjack():
    def __init__(self,serial,max_attempts = 50):
        self.serial = serial
        self.max_attempts = max_attempts


    def write_voltage(self,pin,voltage):
        for i in range(self.max_attempts):
            try:
                handle = ljm.openS("T7", "USB", self.serial)
                ljm.eWriteName(handle, pin, voltage)
                ljm.close(handle)
                break
            except ljm.LJMError as e:
                if(e.errorCode == 1230):
                    pass
                else:
                    print(e)
                    pass
            if(i==self.max_attempts-1):
                print("Max attempts reached - Voltage not written")

    def read_voltage(self,pin):
        voltage_read = 99
        for i in range(self.max_attempts):
            try:
                handle = ljm.openS("T7", "USB", self.serial)
                voltage_read = ljm.eReadName(handle, pin)
                ljm.close(handle)
                break
            except ljm.LJMError as e:
                if(e.errorCode == 1230):
                    pass
                else:
                    print(e)
                    pass
            if(i==self.max_attempts-1):
                print("Max attempts reached - Voltage not read")
        return voltage_read-OFFSET
