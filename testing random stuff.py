from CQTdevices import AnalogComm
analogpm_add='/dev/serial/by-id/usb-Centre_for_Quantum_Technologies_Analog_Mini_IO_Unit_MIO-QO13-if00'
apm=AnalogComm(analogpm_add)

import time
start_time = time.time()

i=0

average = 0
num_of_avgs = 50 

while i<100:
	now = float(apm.get_voltage(1))
	average = (num_of_avgs-1)*average/num_of_avgs + now/num_of_avgs
	print average
	i += 1

print("--- %s seconds ---" % (time.time() - start_time))

apm._serial_write("OFF")
apm.close()
print "Analog powermeter has turned off."