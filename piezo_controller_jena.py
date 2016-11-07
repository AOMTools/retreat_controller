'''
Piezosystem jena class
Author: Adrian Utama
Aug 2016
'''

import subprocess as sp
import numpy as np
import time

# DO NOT CHANGE THIS IF YOU DON'T KNOW WHAT YOU ARE DOING
usbdacprog = '~/programs/usbpatgendriver/testapps/usbdacset'
dac_add='/dev/ioboards/pattgen_serial_10'
CHANNEL_X = 4
CHANNEL_Y = 7
CHANNEL_Z = 8

def insanity_check(number, min_value, max_value):
    ''' To check whether the value is out of given range'''
    if number > max_value:
        return max_value
    if number < min_value:
        return min_value
    else: 
        return number

class PiezoJena:
    def __init__(self):
        self.set_x(0)
        self.set_x(0)
        self.set_x(0)
        print "System Ready to go!"

    def set_x(self, value):
        value = insanity_check(value,0,10)
        print "Output Voltage ", CHANNEL_X, "(x)",
        self.set_dac(CHANNEL_X, value)

    def set_y(self, value):
        value = insanity_check(value,0,10)
        print "Output Voltage ", CHANNEL_Y, "(y)",
        self.set_dac(CHANNEL_Y, value)

    def set_z(self, value):
        value = insanity_check(value,0,10)
        print "Output Voltage ", CHANNEL_Z, "(z)",
        self.set_dac(CHANNEL_Z, value)

    def set_dac(self, channel, output_voltage):
        print "set to ", output_voltage
        sp.call([usbdacprog + " -d " + dac_add + " " + str(channel-1) + " " + '%.3f'%round(output_voltage,3)], shell=True)


if __name__ == '__main__':
    piezo = PiezoJena()
    
    testing = 1
    if testing == 0:
    #Testing
	    piezo.set_x(5)
	    piezo.set_y(8)
	    piezo.set_z(8)
    else:	    
	 
	    #Scanning procedure
	    x_coor = range(0,11,2)
	    y_coor = range(0,11,2)
	    z_coor = range(0,11,2)

	    x_coor = [5] #To fix one of the coor
	    
	    for x in x_coor:
		for y in y_coor:
		    for z in z_coor:
		        print 'Coordinate',x,y,z
		        piezo.set_x(x)
		        piezo.set_y(y)
		        piezo.set_z(z)
		        time.sleep(10)

	    piezo.set_x(5)
	    piezo.set_y(5)
	    piezo.set_z(5)
	    
    
