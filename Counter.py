# -*- coding: utf-8 -*-
"""
Simple USB counter.

Usage: Send plaintext commands, separated by newline/cr or semicolon.
       An eventual reply comes terminated with cr+lf.

Important commands:

*IDN?     Returns device identifier
*RST      Resets device
TIME     <value>
          Set the gate time to <value> in msec.
          Default is 1000, minimum is 1, max 65535.
TIME?     Returns the current gate time.
COUNTS?   Triggers a counting window, and replies with the number of
          detected events as a list of space-separated integers.                
TTL       Switches to TTL input levels.                                         
NIM       Switches input to negative NIM levels.                                
LEVEL?    Returns the input level (NIM or TTL).                                 
HELP      Print this help text.         

"""

import serial


class Countercomm(object):
# Module for communicating with the mini usb IO board
    baudrate = 115200
    
    def __init__(self, port):
        self.serial = self._open_port(port)
        print self._serial_read() #will read unknown command
        self._serial_write('a')# flush io buffer
        print self._serial_read() #will read unknown command

        
    def _open_port(self, port):
        ser = serial.Serial(port, timeout=1)
        #ser.readline()
        #ser.timeout = 1 #causes problem with nexus 7
        return ser
    
    def _serial_write(self, string):
        self.serial.write(string + '\n')
    
    def _serial_read(self):
        msg_string = self.serial.readline()
        # Remove any linefeeds etc
        msg_string = msg_string.rstrip()
        return msg_string
    
    def reset(self):
        self._serial_write('*RST')
        return self._serial_read()
        
    def get_counts(self,channel):
        self._serial_write('COUNTS?')
        counts = (self._serial_read()).split()[channel]
        
        return counts
        
    def get_gate_time(self):
        self._serial_write('TIME?')
        out = self._serial_read()
        return out 

    def get_digital(self):
        self._serial_write('LEVEL?')
        level = self._serial_read()
        return level
    
    
    def set_gate_time(self,value):
        self._serial_write('TIME'+ str(int(value)))
        return 
    

    def set_TTL(self):
         self._serial_write('TTL')
         return
         
    def set_NIM(self):
         self._serial_write('NIM')
         return
         
         
    
    def serial_number(self):
        self._serial_write('*IDN?')
        return self._serial_read()