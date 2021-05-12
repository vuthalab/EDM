import serial
import numpy as np
import time

class FRG730:
    def __init__(self, address = '/dev/agilent_pressure_gauge'):
        self._gauge = serial.Serial(address,baudrate=9600,stopbits=1,parity='N',timeout=1)
        self._last_reading = (None, None)

    def read(self, Nbyte):
        return self._gauge.read(Nbyte) #Reads Nbyte bytes from values being streamed by ion gauge

    def write(self, command):
        self._gauge.write(command)

    @property
    def pressure(self):
        self.read(self._gauge.in_waiting - 16) #Clear buffer
        try:
            data = self._gauge.read(16) #Reading enough bytes to collect a full stream of data
        except:
            # Return last reading for minor blips
            if time.time() - self._last_reading[1] < 10: return self._last_reading[0]
            return None

        synchronization_byte = 7 # byte that denotes start of output string
        data_length = 9 # 9 bytes that are sent from the device every 6 ms
        output_string = []

        record_byte = False
        for byte in data:
            if byte == synchronization_byte:
                record_byte = True
            if record_byte and (len(output_string) < data_length): #Load list with one full output string
                output_string.append(byte)
        try:
            pressure = 10**((output_string[4]*256+output_string[5])/4000 - 12.625) #Conversion from manual
        except IndexError: return None

        # Avoid occasional bugs
        if pressure < 5e-12: return self._last_reading[0]

        self._last_reading = (pressure, time.time())
        return pressure

    def set_torr(self):
        #Sets units on gauge to torr
        command = bytes([3]) + bytes([16]) + bytes([142]) + bytes([1]) + bytes([159]) #From manual
        self._gauge.write(command)

    def set_mbar(self):
        #Sets units on gauge to mbar
        command = bytes([3]) + bytes([16]) + bytes([142]) + bytes([0]) + bytes([158]) #From manual
        self._gauge.write(command)

    def set_Pa(self):
        #Sets units on gauge to mbar
        command = bytes([3]) + bytes([16]) + bytes([142]) + bytes([1]) + bytes([159]) #From manual
        self._gauge.write(command)

    def degas_on(self):
        #Turns on degas minute for 3 minutes, should only be turned on for pressures below <3e-6 torr
        command = bytes([3]) + bytes([16]) + bytes([196]) + bytes([1]) + bytes([213]) #From manual
        self._gauge.write(command)

    def degas_off(self):
        #Spots degas before 3 minutes are up
        command = bytes([3]) + bytes([16]) + bytes([196]) + bytes([0]) + bytes([212]) #From manual
        self._gauge.write(command)
