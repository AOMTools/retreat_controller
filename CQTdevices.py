# -*- coding: utf-8 -*-
"""
Created on Wed Jun 10 15:13:21 2015

@author: nick
Chi Huan modified for personal funs and python3
v1.0
"""

import serial
import subprocess as sp
import json   




class WindFreakUsb2(object):
    """
    The first character of any communication to the SynthUSBii unit is the command.  (It is 
    case sensitive.)  What this character tells the unit to do is detailed below. Ideally a 
    “package” is sent all at once. For example a communication for programming the 
    frequency of the LO to 1GHz would be sent as “f1000.0” (without the quotes).  
    For commands that return information from the SynthUSBii unit, such as reading the 
    firmware version, it is advisable to send the command and then read the bytes returned 
    fairly quickly to get them out of the USB buffer in your PC.
    f) RF Frequency Now (MHz) 1000.000
    o) set RF On(1) or Off(0) 1
    h) set RF High(1) or Low(0) Power 1
    a) set RF Power (0=mimimum, 3=maximum) 3
    v) show firmware version
    e) write all settings to eeprom
    x) set internal reference (external=0 / internal=1)  1
    l) set lower frequency for sweep (MHz) 995.000
    u) set upper frequency for sweep (Mhz) 1005.000
    s) set step size for sweep (MHz) 2.500
    t) set step time is 0.300 ms
    g) run sweep (on=1 / off=0)  0
    c) set continuous sweep mode  0
    P) Pulse On time is 1 ms
    O) Pulse Off time is 1 ms
    j) continuous pulse mode  0
    p) get phase lock status (lock=1 / unlock=0)  1
    H0) PLL Register 0 3E80000
    H1) PLL Register 1 8008FA1
    H2) PLL Register 2 18015E42
    H3) PLL Register 3 4B3
    H4) PLL Register 4 A10424
    H5) PLL Register 5 400005
    +) Model Type
    -) Serial Number  2
    ?) help
    Please keep in mind that the device expects the format shown.  For example if you send 
    simply just an “f” the processor will sit there and wait for the rest of the data and may 
    appear locked up.  If you dont send the decimal point and at least one digit afterward, it 
    will have unexpected results. Also, please send data without hidden characters such as a 
    carriage return at the end.
    """
    baudrate = 115200
        
    def __init__(self, port):
        self.serial = self._open_port(port)
        self._serial_write(b'+\n')# flush io buffer
        print (self._serial_read()) #will read unknown command
        self.set_clock(1)
        
        
    def _open_port(self, port):
        ser = serial.Serial(port, self.baudrate, timeout=1)
        ser.readline()
        ser.timeout = 1
        return ser
        
    def _serial_write(self, string):
        self.serial.write(string + '\n')
        
    def _serial_read(self):
        msg_string = self.serial.readline()
        # Remove any linefeeds etc
        msg_string = msg_string.rstrip()
        return msg_string
        
    def get_freq(self):
        self._serial_write('f?')
        return self._serial_read()
    
    def rf_on(self):
        self._serial_write('o1')
        return self._serial_read()
    
    def rf_off(self):
        self._serial_write('o0')
        return self._serial_read()
    
    def rf_power_low(self):
        self._serial_write('h0')
    
    def rf_power_high(self):
        self._serial_write('h1')
    
    def set_pulse_mode(self,value):
        self._serial_write('j' + str(value))
    
    def get_pulse_mode(self):
        self._serial_write('j?')
        return self._serial_read()
        
    def get_power(self):
        self._serial_write('a?')
        return self._serial_read()
        
    def set_freq(self,value):
        self._serial_write('f' + str(value))
        return self._serial_read()
        
    def check_osci(self):
        self._serial_write('p')
        return self._serial_read()
    
    def set_clock(self,value):
        self._serial_write('x' + str(value))
        return self._serial_read()
    
    def get_clock(self):
        self._serial_write('x?')
        return self._serial_read()
    
    def set_power(self,value):
        self._serial_write('a' + str(value))
        return self._serial_read()
    
    def serial_number(self):
        self._serial_write('+')
        return self._serial_read()
        
    def close(self):
        self.serial.close()
        

        
class AnalogComm(object):
# Module for communicating with the mini usb IO board
    """
    Mini analog IO unit.
    
    Usage: Send plaintext commands, separated by newline/cr or semicolon.
           An eventual reply comes terminated with cr+lf.
    
    Important commands:
    
    *IDN?     Returns device identifier
    *RST      Resets device, outputs are 0V.
    OUT  <channel> <value>
              Sets <channel> (ranging from 0 to 2) to
              the voltage <value>. Use 2.5 as value, not 2.5E0
    IN?  <channel>
              Returns voltage of input <channel> (ranging from 0 to 3).             
    ALLIN?    Returns all voltages                                                  
    HELP      Print this help text.                                                 
    ON /OFF   Switches the analog unit on/off.                                      
    DIGOUT <value>                                                                  
              Sets the digital outputs to the                                       
              binary value (ranging from 0..3).                                     
                                                                                    
    REMARK:                                                                         
    Output ranges from 0V to 4.095V. Input is capacitive and ranges                 
    from 0V to 4.095V.                                                              
    """
    baudrate = 115200
    def __init__(self, port):
        self.serial = self._open_port(port)
        self._serial_write('*IDN?')# flush io buffer
        print (self._serial_read()) #will read a command
        self.reset() #Resets device so correct voltages read
        
    
    def _open_port(self, port):
        ser = serial.Serial(port, timeout=0.5)
        ser.readline()
        ser.timeout = 0.5 
        return ser
    
    def _serial_write(self, string):
        self.serial.write((string + ';').encode('UTF-8'))
    
    def _serial_read(self):
        msg_string = self.serial.readline().decode()
        # Remove any linefeeds etc
        msg_string = msg_string.rstrip()
        return msg_string
    
    def reset(self):
        self._serial_write('*RST')
        return self._serial_read()
        
    def get_voltage(self,channel):
        self._serial_write('IN?' + str(channel))
        voltage = self._serial_read()
        return voltage
        
    def get_voltage_all(self):
        self._serial_write('ALLIN?')
        allin = self._serial_read()
        return allin
    
    
    def set_voltage(self,channel,value):
        self._serial_write('OUT'+ str(channel) + str(value))
        return 
    
    def set_digitout(self,value):
        self._serial_write('DIGOUT' + str(value))
        return
    
    def close(self): 
        self.serial.close()

    def serial_number(self):
        self._serial_write(b'*IDN?')
        return self._serial_read()

class PowerMeterComm(object):
# Module for communicating with the power meter 
    '''
    Simple optical power meter.                                                    
                                                                               
    Usage: Send plaintext commands, separated by newline/cr or semicolon.          
           An eventual reply comes terminated with cr+lf.                          
                                                                                   
    Important commands:                                                            
                                                                                   
    *IDN?     Returns device identifier                                            
    *RST      Resets device, outputs are 0V.                                       
    RANGE <value>                                                                  
              Chooses the shunt resistor index; <value> ranges from 1 to 5.        
    VOLT?     Returns the voltage across the sense resistor.                       
    RAW?      Returns the voltage across the sense resistor in raw units.          
    FLOW      starts acquisition every 1 ms and returns raw hex values                        
    STOP      resets the raw sample mode.                                                     
    ALLIN?    Returns all 8 input voltages and temperature.                                   
    HELP      Print this help text.   
    '''

    baudrate = 115200
    
    def __init__(self, port):
        self.serial = self._open_port(port)
        self.serial.write(b'*IDN?;')# flush io buffer
        print (self._serial_read()) #will read unknown command
        self.set_range(4)
        self.range = self.get_range
        self.data = self._read_cal_file()
        #self.set_range(4) #Sets bias resistor to 1k
        
    def _open_port(self, port):
        ser = serial.Serial(port, timeout=1)
        #ser.readline()
        #ser.timeout = 1 #causes problem with nexus 7
        return ser
        
    def close(self):
        self.serial.close()

        
    
    def _serial_write(self, string2):
        self.serial.write((string2+';').encode('UTF-8'))
    
    def _serial_read(self):
        msg_string = self.serial.readline().decode()
        # Remove any linefeeds etc
        msg_string = msg_string.rstrip()
        return msg_string
    
    def reset(self):
        self._serial_write('*RST')
        return self._serial_read()
        
    def get_voltage(self):
        self._serial_write('VOLT?')    
        voltage = self._serial_read()
        #print voltage
        return voltage
        
    def get_range(self):
        self._serial_write('RANGE?')
        pm_range = self._serial_read()
        #print pm_range
        return pm_range
    
    
    def set_range(self,value):
        self._serial_write('RANGE'+ str(value))
        self.pm_range = value -1
        return self.pm_range
    
    def serial_number(self):
        self.serial.write(b'*IDN?')
        return self.serial.read()
        
        """this section of the code deals with converting between the voltage value and the
    optical power at the wavelength of interest"""
    
    resistors = [1e6,110e3,10e3,1e3,20]    #sense resistors adjust to what is on the board
    
    file_name = 's5106_interpolated.cal'    #detector calibration file
    

    
    def _read_cal_file(self): # read in calibration file for sensor
        f = open(self.file_name,'r')
        x = json.load(f)
        f.close()
        return x
        

    def volt2amp(self,voltage,range_number):
        self.amp = voltage/self.resistors[range_number]
        return self.amp
                            
    
    def amp2power(self,voltage,wavelength,range_number):
        amp = self.volt2amp(voltage,range_number-1)
        xdata = self.data[0]
        ydata = self.data[1]
        i = xdata.index(int(wavelength))
        responsivity = ydata[i]
        power = amp/float(responsivity)
        
        return power
    
    def get_power(self,wavelength):
        
        self.power = self.amp2power(float(self.get_voltage()),wavelength,int(self.get_range()))
        return self.power


class CounterComm(object):
# Module for communicating with the mini usb counter board
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
    
    baudrate = 115200
    
    def __init__(self, port):
        self.serial = self._open_port(port)
        self._serial_write('*IDN?')# flush io buffer
        print (self._serial_read()) #will read unknown command

        
    def _open_port(self, port):
        ser = serial.Serial(port, timeout=1)
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
        
    def get_counts(self):
        self._serial_write('COUNTS?')
        counts = self._serial_read()
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
         
    def close(self): 
        self.serial.close()
        
    def serial_number(self):
        self._serial_write('*IDN?')
        return self._serial_read()

class DDSComm(object):
    """
    usage: dds_encode [-d device] [-E | -T ] [-R] [-i sourcefile] [-a refamp]
                     [-q] [-b basedivider]

   options:
   -d device :       Device node. If if device is "-", then stdout is used, 
                     and the EP1 option disabled. Otherwise, the
                     location /dev/ioboards/dds0 is used by default. If a file 
             is used instead, the control commands used to prepare
             a certain configuration can be stored, and piped to the
             DDS separately with a simple cat >device command later.

   -E                Allow the usage of the EP1 commands. This is the default.

   -T                Disallow the usage of EP1 commands, treat output device
                     as a plain stream only. Needs to be set when a file is
             used to store the commands.

   -R                Reset before loading. Perform a device reset before sending
                     the specified command. This, however, does only a master
             reset, not a sensible filling of the registers.

   -i sourcefile     Take the command data not from stdin, but from an input
                     file.
   -a refamp         defines reference amplitude in millivolt directly instead
                     of taking the default value of 480 mV. Reference amplitude
             is the peak amplitude the DDS/amplifier section can
             generate.
   -q                Quiet option. This is only useful for boards which use
                     the internal clock of the cypress chip and can keep the
             sync_out muted.
   -b basedivider    This value is the PLL divider and determines the master
                     clock. The value of <basedivider> is an integer with
             values between 1 and 10, corresponding to frequencies form
             50 MHz to 500 MHz.

   Commands can be separated either by semicolons or newlines. Not sure if
   this is universal, but it may work. Here is a list of commands with
   their parameters:
    """
    

    def __init__(self,port,channel):
        self.DDSDEV = port
        self.channel = channel

    
    ##default dds_encode function
    def mode(self,value):
        #set modulation mode: am fm pm
        self.call('mode '+value)
    
    def set_freq(self,value):
        #unit: hz mhz ghz etc
        self.call('frequency '+str(self.channel)+' '+str(value)+' '+'mhz')
        
    def set_power(self,value):
        #unit: ampunit
        self.call('amplitude '+str(self.channel)+' '+str(value)+' '+'ampunits')
    
    def amplitude(self,value,unit):
        #unit: ampunits dbm V mV
        self.call('amplitude '+str(self.channel)+' '+str(value)+' '+unit)
        
    def tuning(self,register,value,unit):
        #unit: ampunits dbm V mV
        self.call('tuning '+str(register)+' '+str(value)+' '+unit)
    
    ##extra preset function
    def start(self):
        #default assume no modulation
        self.reset()
        self.call('levels 2')
        self.call('mode singletone')
    
    def reset_freq(self,freq):
        #compact function assuming freq in MHz, amp to max (1023)
        self.off()
        self.set_freq(freq)
        self.on()
        
    def on(self):
        self.amplitude(100,'ampunits')
    
    def off(self):
        self.amplitude(0,'ampunits')    
    
    def call(self,command):
        #interface function to dds_encode
        #DDSPROG = "/home/qitlab/programs/usbdds/apps/dds_encode"
        DDSPROG = "/home/qitlab/programs/usbdds/apps/dds_encode"
        sp.call(['echo '+command+' \;. |'+DDSPROG+' -T -d '+self.DDSDEV],shell=True)
    
    def reset(self):
        #dds full reset / switch off
        #DDSRESET = "/home/qitlab/programs/usbdds/apps/reset_dds"
        DDSRESET = "/home/qitlab/programs/usbdds/apps/reset_dds"
        sp.call(DDSRESET)
if __name__=='__main__':
    Power_meter_address = '/dev/serial/by-id/usb-Centre_for_Quantum_Technologies_Optical_Power_Meter_OPM-QO04-if00'
    #ser=serial.Serial(Power_meter_address)
    #ser.write(b'VOLT?')
    #print(ser.read(100))
    #msg_string = ser.readline()
        # Remove any linefeeds etc
    #msg_string = msg_string.rstrip()
    #print(msg_string)
    w=780
    pm=PowerMeterComm(Power_meter_address)
    pm.get_voltage()
    print(pm.get_power(w)*1000)