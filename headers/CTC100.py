import re
import telnetlib
import time

class CTC100:
    """
    An extremely simple class to read values from the CTC100
    Prorammable Temperature Controller. Use ethernet rather 
    than a serial port.

    How to use::

        >>> import CTC100
        >>> c = CTC100.CTC100("/dev/ttyACM0")
        >>> c.read(1)
        300.841

    Author: Wesley Cassidy
    Date: 26 April 2018
    
    Modified by: Rhys Anderson
    Date: February 25, 2020
    """

    def __init__(self, ip_address):
        """
        Pass the USB Serial port the CTC100 is attached to (usually of
        the form /dev/ttyACM*).
        """

        self.device = telnetlib.Telnet(ip_address, port = 23, timeout = 2)
        self.thermometer_names = []
        self.heater_names = []

    def write(self, command):
        """
        Write a command to the CTC100 over serial, then wait for the
        response.
        """
        self.device.write((command+"\n").encode()) # \n terminates commands

        # The response to a command is always terminated by a
        # \r\n, so keep polling the input buffer until we read
        # one.
        response = self.device.read_until(b"\r\n",0.5)
        return response
        
    def get_variable(self, var):
        """
        Read a parameter of the CTC100. This function is mostly for
        convenience, but does include some input formatting to prevent
        simple bugs.
        """
        
        var = var.replace(" ", "") # Remove spaces from the variable name. They're optional and can potentially cause problems
        return self.write("{}?".format(var))
        
    def set_variable(self, var, val):
        """
        Set a parameter of the CTC100. This function is mostly for
        convenience, but does include some input formatting to prevent
        simple bugs.
        """
        
        var = var.replace(" ", "") # Remove spaces from the variable name. They're optional and can potentially cause problems
        val = "({})".format(val) # Wrap argument in parentheses, just in case. This prevents an argument containing a space from causing unexpected issues
        return self.write("{} = {}".format(var, val))
        
    def increment_variable(self, var, val):
        """
        Add an amount to a parameter of the CTC100. This function is
        mostly for convenience, but does include some input formatting
        to prevent simple bugs.
        """
        
        var = var.replace(" ", "") # Remove spaces from the variable name. They're optional and can potentially cause problems
        val = "({})".format(val) # Wrap argument in parentheses, just in case. This prevents an argument containing a space from causing unexpected issues
        return self.write("{} += {}".format(var, val))

    def setAlarm(self, channel, Tmin, Tmax):
        
        #Enables alarm with 4 beeps on a channel for a given range
        
        if not isinstance(channel, str): #Sets string for channel
            channel = "In{}".format(channel)
            
        self.set_variable("{}.alarm.sound".format(channel),  "4 beeps") #Sets alarm to 4 beeps
        
        self.set_variable("{}.alarm.min".format(channel), str(Tmin)) #Sets minimum Temperature
        self.set_variable("{}.alarm.max".format(channel), str(Tmax)) #Set maximum Temperature
        
        response = self.set_variable("{}.alarm.mode".format(channel), "Level") # Turns alarm on
        
        return response
        
    def disableAlarm(self, channel):
        
        if not isinstance(channel, str): #Sets string for channel
            channel = "In{}".format(channel)
        
        repsonse = self.set_variable("{}.alarm.mode".format(channel), "Off") # Turns alarm off
    
    def read(self, channel):
        """
        Read the value of one of the input channels. If the channel's
        name has been changed from the default or you wish to read the
        value of an output channel, the full name must be passed as a
        string. Otherwise, an integer will work.
        """

        if not isinstance(channel, str): #Sets string for channel
            channel = "In{}".format(channel)
            
        response = self.get_variable("{}.value".format(channel))
   
        # Extract the response using a regex in case verbose mode is on
        match = re.search(r"[-+]?\d*\.\d+", response.decode("utf-8"))
        
        if match is not None:
            return float(match.group())
        else:
            raise RuntimeError("Unable to read from channel {}".format(channel))
        
    def ramp_temperature(self, channel, temp=0.0, rate=0.1):

        self.set_variable("{}.PID.mode".format(channel), "off") #This should reset the ramp temperature to the current temperature.
        self.set_variable("{}.PID.Ramp".format(channel), str(rate))
        self.set_variable("{}.PID.setpoint".format(channel), str(temp))
        self.set_variable("{}.PID.mode".format(channel), "on") 
        
    def disable_PID(self, channel):
        
        self.set_variable("{}.PID.mode".format(channel), "off")
        self.set_variable("{}.value".format(channel),"0")
        self.write("{}.Off".format(channel))
        
    def enable_output(self):
        
        self.set_variable("outputEnable", "on")
        
    def disable_output(self):
        
        self.set_variable("outputEnable", "off")