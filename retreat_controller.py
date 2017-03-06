'''
The cavity retreat strategy: voltage controller for the magnetic field and piezo
Author: Adrian Nugraha Utama
July 2016

Note: The program uses Multithread with Tkinter. See Python Cookbook: Combining Tkinter and Asynchronous I/O with Threads (Jacob Hallen).
'''


import Tkinter
import time
import threading
import random
import Queue
import subprocess as sp
import zmq
from CQTdevices import AnalogComm
from Counter import Countercomm

# BOUNDARIES
MIN_VALUE_VOLTAGE = -10
MAX_VALUE_VOLTAGE = 10
MAX_STEP_VOLTAGE = [0.1, 0.1, 0.1, 0.1, 0.05, 0.05, 0.05] # Max step voltage to increase every refresh rate (100 ms)
MAX_OFFSET_ADJ = 1
MIN_OFFSET_ADJ = -1
STEP_OFFSET_ADJ = 0.002
MAX_LOCKING_STEP = [50,100] #1 step roughly 100 ms. 
MAX_LOCKING_TRIES = 6

# SERIALS
#analogpm_add='/dev/serial/by-id/usb-Centre_for_Quantum_Technologies_Analog_Mini_IO_Unit_MIO-QO02-if00' # Channel 1
dac_add='/dev/ioboards/pattgen_serial_10'
usbdacprog = '~/programs/usbpatgendriver/testapps/usbdacset'
counter_add='/dev/serial/by-id/usb-Centre_for_Quantum_Technologies_USB_Counter_Ucnt-QO11-if00'

def insanity_check(number, min_value, max_value):
    ''' To check whether the value is out of given range'''
    if number > max_value:
        return max_value
    if number < min_value:
        return min_value
    else: 
        return number

class GuiPart:
    def __init__(self, master, queue, endCommand):
        self.queue = queue
        self.entry = [0,0,0,0,0,0,0]        # 0th item refers to set threshold
        self.set_value = [0,0,0,0,0,0,0]    # 0th item refers to set threshold

        self.label_output = [0,0,0,0,0,0,0]
        self.output_value = [0,0,0,0,0,0,0]

        # Some parameters for the GUI (Channel 0th: set threshold, 1-6th: set voltage)
        self.rough_step = [500, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3]       #500
        self.fine_step = [20, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01] #20
        self.display_apm = 0

        # Lock Status
        self.set_lock_status = 0
        self.lock_target = 0
        self.lock_process = 0 # 0: No lock, 1: Processing, 2: Locked, 3: ERROR, 4: Out of Lock  

        # Voltage Offset adjustment for the lock
        self.label_offset_adj = [0, 0]      # The label array for offset adjust
        self.display_offset_adj = [0, 0]    # 0th: Voltage 5, 1st: Voltage 6 

        # Set up the GUI

        # Voltages 1 to 6 adjustment
        for i in range(1,7):
            Tkinter.Label(master, text='Voltage '+str(i), font=("Helvetica", 16)).grid(row=i, padx=5, pady=5, column=1)
            
            Tkinter.Button(master, text='<<', font=("Helvetica", 12), command=lambda i=i:self.buttonPressed(i, 1)).grid(row=i, column=2)
            Tkinter.Button(master, text='<', font=("Helvetica", 12), command=lambda i=i:self.buttonPressed(i, 2)).grid(row=i, column=3)
            Tkinter.Button(master, text='>', font=("Helvetica", 12), command=lambda i=i:self.buttonPressed(i, 3)).grid(row=i, column=5)
            Tkinter.Button(master, text='>>', font=("Helvetica", 12), command=lambda i=i:self.buttonPressed(i, 4)).grid(row=i, column=6)

            self.entry[i] = Tkinter.Entry(master, width=10, font=("Helvetica", 16), justify=Tkinter.CENTER)
            self.entry[i].grid(row=i, column=4)
            self.entry[i].insert(0, '%.3f'%round(self.set_value[i],3))

            self.label_output[i] = Tkinter.Label(master, font=("Helvetica", 16), text='Output : '+ '%.3f'%round(self.output_value[i],3), width=12, anchor=Tkinter.W)
            self.label_output[i].grid(row=i, padx = 5, column=8)
      
        # Some labels for the slow locking            
        Tkinter.Label(master, text='V6 Slow Locking Module', font=("Helvetica", 16)).grid(row=7, padx=5, pady=5, column=1, columnspan=4, sticky=Tkinter.W)
        Tkinter.Label(master, text='Power :', font=("Helvetica", 16)).grid(row=7, column=5, columnspan=2, sticky=Tkinter.W)

        self.label_display_apm = Tkinter.Label(master, font=("Helvetica", 16), text='%.2f'%round(self.display_apm,2), width=12, bg="black", fg="white")
        self.label_display_apm.grid(row=7, column=8, padx=5, pady=5)

        # Set threshold
        Tkinter.Label(master, text='Threshold', font=("Helvetica", 16)).grid(row=8, padx=5, pady=5, column=1)
        
        Tkinter.Button(master, text='<<', font=("Helvetica", 12), command=lambda i=i:self.buttonPressed(0, 1)).grid(row=8, column=2)
        Tkinter.Button(master, text='<', font=("Helvetica", 12), command=lambda i=i:self.buttonPressed(0, 2)).grid(row=8, column=3)
        Tkinter.Button(master, text='>', font=("Helvetica", 12), command=lambda i=i:self.buttonPressed(0, 3)).grid(row=8, column=5)
        Tkinter.Button(master, text='>>', font=("Helvetica", 12), command=lambda i=i:self.buttonPressed(0, 4)).grid(row=8, column=6)

        self.entry[0] = Tkinter.Entry(master, width=10, font=("Helvetica", 16), justify=Tkinter.CENTER)
        self.entry[0].grid(row=8, column=4)
        self.entry[0].insert(0, '%.3f'%round(self.set_value[i],2))

        # Set locking checkbox
        self.set_lock = Tkinter.IntVar()
        self.chk_set = Tkinter.Checkbutton(root, text='Set Lock', font=("Helvetica", 16), variable=self.set_lock, command=lambda:self.setLockStatus(self.set_lock.get()))
        self.chk_set.grid(row=8, column=8, padx=5, pady=5)

        # Locking display parameters
        Tkinter.Label(master, text='Target :', font=("Helvetica", 16)).grid(row=9, padx=5, pady=5, column=4, sticky=Tkinter.E)
        self.label_lock_target = Tkinter.Label(master, font=("Helvetica", 16), text='%.1f'%round(self.lock_target,1))
        self.label_lock_target.grid(row=9, column=5, columnspan=2, padx=5, pady=5, sticky=Tkinter.W)

        Tkinter.Label(master, text='V5 Offset :', font=("Helvetica", 16)).grid(row=9, padx=5, pady=5, column=1, columnspan=3, sticky=Tkinter.W)
        self.label_offset_adj[0] = Tkinter.Label(master, font=("Helvetica", 16), text='%.3f'%round(self.display_offset_adj[0],3))
        self.label_offset_adj[0].grid(row=9, column=2, columnspan=2, padx=5, pady=5, sticky=Tkinter.W)        
        Tkinter.Label(master, text='V6 Offset :', font=("Helvetica", 16)).grid(row=10, padx=5, pady=5, column=1, columnspan=3, sticky=Tkinter.W)
        self.label_offset_adj[1] = Tkinter.Label(master, font=("Helvetica", 16), text='%.3f'%round(self.display_offset_adj[1],3))
        self.label_offset_adj[1].grid(row=10, column=2, columnspan=2, padx=5, pady=5, sticky=Tkinter.W)        

        # Lock Process Status
        self.label_lock_process = Tkinter.Label(master, font=("Helvetica", 16), text='Starting', width=12, bg="white", fg="black")
        self.label_lock_process.grid(row=9, column=8, padx=5, pady=5, sticky=Tkinter.W)                

        # Misc    
        Tkinter.Button(master, text='Shutdown', font=("Helvetica", 16), command=endCommand).grid(row=10, column=8, columnspan=2, padx=5, pady=5)

    def buttonPressed(self, channel, button_type):
        # Performing the stuffs for Channel 1 to 6 (Voltage)
        if button_type == 1:
            self.set_value[channel] -= self.rough_step[channel] 
        elif button_type == 2:
            self.set_value[channel] -= self.fine_step[channel]
        elif button_type == 3:
            self.set_value[channel] += self.fine_step[channel]
        elif button_type == 4:
            self.set_value[channel] += self.rough_step[channel]

        if (channel >= 1) and (channel <=6):
            self.set_value[channel] = insanity_check(self.set_value[channel], MIN_VALUE_VOLTAGE, MAX_VALUE_VOLTAGE)
        elif channel == 0:
            self.set_value[channel] = insanity_check(self.set_value[channel], 0, 10000)

        self.entry[channel].delete(0, Tkinter.END)
        self.entry[channel].insert(0, '%.3f'%round(self.set_value[channel],3))

    def setLockStatus(self, key):
        # Check whether it is okay to lock, if yes then set a target which is halfway between current reading and threshold
        if self.set_lock_status == 0:
            if self.set_value[0] < self.display_apm:
                self.set_lock_status = key
                print "Set Lock"
                self.lock_target = (self.set_value[0] + self.display_apm)/2
                print "Lock target set at ", self.lock_target
                self.label_lock_target['text'] = '%.1f'%round(self.lock_target,1)
            else: 
                print "Threshold too high, unable to lock"
        elif self.set_lock_status == 1:
            self.set_lock_status = key
            print "Unset Lock"
            self.lock_target = 0
            self.label_lock_target['text'] = '%.3f'%round(self.lock_target,3)
            # Change the value of the set voltage 6
            for i in range(2):
                self.set_value[i+5] = self.set_value[i+5] + self.display_offset_adj[i] 
                self.entry[i+5].delete(0, Tkinter.END)
                self.entry[i+5].insert(0, '%.3f'%round(self.set_value[i+5],3))

    def updateLockProcess(self):
        # Check lock process and modify the correct display status
        if self.lock_process == 0:
            self.label_lock_process['text'] = 'No lock'
            self.label_lock_process['bg'] = 'white'
        elif self.lock_process == 1:
            self.label_lock_process['text'] = 'Processing'
            self.label_lock_process['bg'] = 'yellow'
        elif self.lock_process == 2:
            self.label_lock_process['text'] = 'Locked'
            self.label_lock_process['bg'] = 'green'
        elif self.lock_process == 3:
            self.label_lock_process['text'] = 'ERROR'
            self.label_lock_process['bg'] = 'red'
        elif self.lock_process == 4:
            self.label_lock_process['text'] = 'OUT OF LOCK'
            self.label_lock_process['bg'] = 'red'

    def processIncoming(self):
        """Handle all messages currently in the queue, if any."""
        while self.queue.qsize(  ):
            try:
                msg = self.queue.get(0)
                # Check contents of message and do whatever is needed. As a
                # simple test, print it (in real life, you would
                # suitably update the GUI's display in a richer fashion).
                print msg
            except Queue.Empty:
                # just on general principles, although we don't
                # expect this branch to be taken in this case
                pass

class ThreadedClient:
    """
    Launch the main part of the GUI and the worker thread. periodicCall and
    endApplication could reside in the GUI part, but putting them here
    means that you have all the thread controls in a single place.
    """
    def __init__(self, master):
        """
        Start the GUI and the asynchronous threads. We are in the main
        (original) thread of the application, which will later be used by
        the GUI as well. We spawn a new thread for the worker (I/O).
        """
        self.master = master

        # Create the queue
        self.queue = Queue.Queue(  )

        # Set up the GUI part
        self.gui = GuiPart(master, self.queue, self.endApplication)
        master.protocol("WM_DELETE_WINDOW", self.endApplication)   # About the silly exit button

        # Start the procedure regarding the initialisation of experimental parameters and objects
        self.initialiseParameters()

        # Initialising the zmq server
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REP)
        self.socket.bind("tcp://127.0.0.1:5556")
        print "The server is up. Ready to receive messages"

        # Set up the thread to do asynchronous I/O
        # More threads can also be created and used, if necessary
        self.running = 1
        self.thread1 = threading.Thread(target=self.workerThread1_APM)
        self.thread1.start(  )
        self.thread2 = threading.Thread(target=self.workerThread2_zmq)
        self.thread2.start(  )

        # Start the periodic call in the GUI to check if the queue contains
        # anything
        self.periodicCall(  )

    def initialiseParameters(self):
        # Communiate with the analog powermeter
        # self.apm = AnalogComm(analogpm_add)
        # self.APM_CHANNEL = 1
        
        # # Communicate with the usb counter
        self.counter = Countercomm(counter_add)
        self.counter.set_gate_time(30)
        
        # Create a variable to store the average value & number of averages of the analog powermeter
        self.average_apm = 0
        self.NUM_OF_AVG = 20 

        # Creating the objects voltage_handler
        self.voltage_handler = [0,0,0,0,0,0,0]
        for i in range(1,7):
            self.voltage_handler[i] = VoltageHandler(MAX_STEP_VOLTAGE[i], i)

        # Initialise the variable set_voltage: These are the values that we want to set the DAC to.
        # Note: In voltage 6, it is the set_value (from GUI) + the fine adjustment for locking 
        self.set_voltage = [0,0,0,0,0,0,0]

        # Initialise the offset adj voltage & correction direction 
        self.offset_adj_voltage = [0, 0]
        self.offset_adj_direction = 1 #1 for positive, -1 for negative direction
        self.count_adj_steps = 0

        # Lock request variable (1: asking for lock, 0: nothing)
        self.lock_request = 0

        # Create the locking delay variable & locking mode
        self.LOCKING_DELAY = 5
        self.lock_delay_counter = 0
        self.locking_mode = 1   # Starts locking from voltage 6
        self.locking_mode_max = self.locking_mode + MAX_LOCKING_TRIES

    def periodicCall(self):
        """
        Check every 100 ms if there is something new in the queue.
        """
        self.gui.processIncoming(  )

        # Setting a refresh rate for periodic call
        self.master.after(100, self.periodicCall)
        
        # Check the lock status and perform locking/unlocking if necessary
        if self.gui.set_lock_status == 0:
            self.gui.lock_process = 0
            self.offset_adj_voltage[0] = 0
            self.offset_adj_voltage[1] = 0
        elif self.gui.set_lock_status == 1 and self.lock_request == 0:
            if self.average_apm < self.gui.set_value[0]:
                self.gui.lock_process = 4
        elif self.gui.set_lock_status == 1 and self.lock_request == 1:
            # Check for whether display APM is in locked condition
            if self.gui.lock_process == 4:
                self.gui.lock_process = 1
            if self.average_apm > self.gui.lock_target:
                self.gui.lock_process = 2

        # Simple slow locking mechanism. Note: the value of display_apm in GUI is delayed by 100ms from average_apm
        if self.gui.lock_process == 1:
            self.lock_delay_counter +=1
            self.try_mode = self.locking_mode % 2          
            if self.lock_delay_counter >= self.LOCKING_DELAY: #Delay for the correction to set in
                if self.average_apm < self.gui.display_apm:
                    self.offset_adj_direction = -1 * self.offset_adj_direction      # Reverse the process if the correction does not become better
                self.offset_adj_voltage[self.try_mode] += STEP_OFFSET_ADJ * self.offset_adj_direction
                self.lock_delay_counter = 0
            self.count_adj_steps += 1
            if self.count_adj_steps >= MAX_LOCKING_STEP[self.try_mode]:
                self.locking_mode +=1
                self.count_adj_steps = 0
                print "Trying locking in other direction"
        if self.locking_mode >= self.locking_mode_max:
            self.gui.lock_process = 3 

        # Update the display status of the lock
        self.gui.updateLockProcess()

        # Check the insanity of the offset adj voltage and refresh periodically the offset_adj_voltage display
        for i in range(2):
            self.offset_adj_voltage[i] = insanity_check(self.offset_adj_voltage[i], MIN_OFFSET_ADJ, MAX_OFFSET_ADJ)
            self.gui.display_offset_adj[i] = self.offset_adj_voltage[i]
            self.gui.label_offset_adj[i]['text'] = '%.3f'%round(self.gui.display_offset_adj[i],3)

        # Updating the set voltage based on the gui set value. For voltage 5 and 6, need to add the offset adj.
        for i in range(1,5):
            self.set_voltage[i] = self.gui.set_value[i]
        for i in range(2):
            self.set_voltage[i+5] = self.gui.set_value[i+5] + self.offset_adj_voltage[i]

        # Voltage "insanity check" for the final time before being processed by the program
        for i in range(1,7):
            self.set_voltage[i] = insanity_check(self.set_voltage[i], MIN_VALUE_VOLTAGE, MAX_VALUE_VOLTAGE)
        
        # Updating the voltage handler objects & GUI
        for i in range(1,7):
            self.voltage_handler[i].change_set_voltage(self.set_voltage[i])
            output = self.voltage_handler[i].update()
            self.gui.output_value[i] = output
            self.gui.label_output[i]['text'] = 'Output : '+ '%.3f'%round(self.gui.output_value[i],3)

        # Updating the display value of analog powermeter
        self.gui.display_apm = self.average_apm
        self.gui.label_display_apm['text'] = '%.2f'%round(self.gui.display_apm,2)

        # Shutting down the program
        if not self.running:
            # Check whether the voltages has been switched off
            for i in range(1,7):
                if self.gui.output_value[i] == 0:
                    pass
                else:
                    return 0
            print "Shutting Down"
            import sys
            sys.exit()


    def workerThread1_APM(self):
        """
        This is where we handle the asynchronous I/O. For example, it may be
        a 'select(  )'. One important thing to remember is that the thread has
        to yield control pretty regularly, by select or otherwise.
        """
        while self.running:
            # To simulate asynchronous I/O, we create a random number at
            # random intervals. Replace the following two lines with the real
            # thing.
            try:
                # Analog Powermeter
                # now = float(self.apm.get_voltage(self.APM_CHANNEL))
                # Usb Counter
                now = float(self.counter.get_counts(0))
            
                self.average_apm = (self.NUM_OF_AVG-1)*self.average_apm/self.NUM_OF_AVG + now/self.NUM_OF_AVG
            except:
                pass
    
    def workerThread2_zmq(self):
        """
        This is where we handle the asynchronous I/O. For example, it may be
        a 'select(  )'. One important thing to remember is that the thread has
        to yield control pretty regularly, by select or otherwise.
        """
        while self.running:
            try:
                self.message = self.socket.recv()
                print "Received message from the other side :", self.message      

                try:
                    self.message_a, self.message_b = self.message.split(" ")
                except:
                    print "MESSAGE ILL DEFINED"
                    # Tell Boss the message is ill defined
                    self.socket.send("Speak Properly")

                # The reply if it does not satisfy anything below
                self.message_back = "Whatdahell Boss"

                try:
                # A big try

                    if self.message_a == "Please":
                        # Dealing with lock
                        if self.message_b == "Lock":
                            self.lock_request = 1
                            self.locking_mode = 1   # Start locking from V6 again
                            self.count_adj_steps = 0
                            self.message_back = "Okay Boss"
                            if self.gui.lock_process == 3:
                                print "Trying to lock again"
                                self.gui.lock_process = 1
                            # Check whether the lock is set
                            if self.gui.set_lock_status == 0:
                                print "Lock is not set. Tell the other side"
                                self.message_back ="Lock Nonexistent"
                                self.lock_request = 0
                        # Dealing with shutdown
                        if self.message_b == "Annihilate":
                            self.message_back = "Okay Boss"
                            self.endApplication()

                    if self.message_a == "Check":
                        if self.message_b == "Lock":
                            # ----- DEALING WITH LOCK ----- #
                            # Check if the lock is obtained (or error)
                            if self.gui.lock_process == 2:
                                print "Locked successful, tell the good news to the other side"
                                self.message_back = "Lock Successful"
                                self.lock_request = 0
                            elif self.gui.lock_process == 3:
                                print "Locked not successful, tell the bad news to the other side"
                                self.message_back = "Lock Unsuccessful"
                            # Misc
                            elif self.gui.lock_process == 1:
                                print "Still Locking"
                                self.message_back = "Still Locking"
                            else:
                                print "Request for check lock is probably not at the correct moment"
                                self.message_back = "Something Wrong"
                            # ----- END ----- #

                    if self.message_a == "CheckVolt":
                        # Check voltage for a specific channel
                        channel = int(float(self.message_b))
                        if channel > 0 and channel < 7:
                            value = '%.3f'%round(self.gui.output_value[channel],3)
                            self.message_back = "Volt" + str(channel) + " " + value
                        else:
                            self.message_back = "Volt" + str(channel) + " " + "Undefined"

                    if self.message_a[:-1] == "SetVolt":
                        channel = int(self.message_a[-1])
                        if channel > 0 and channel < 7:
                            value = round(float(self.message_b),3)
                            value = insanity_check(value, MIN_VALUE_VOLTAGE, MAX_VALUE_VOLTAGE)
                            self.gui.set_value[channel] = value
                            self.message_back = "SetVolt" + str(channel) + " " + str(value)
                        else:
                            self.message_back = "SetVolt" + str(channel) + " " + "Undefined"                
                
                    if self.message_a[:-1] == "ShiftVolt":
                        channel = int(self.message_a[-1])
                        if channel > 0 and channel < 7:
                            if self.message_b == "Up":
                                self.gui.set_value[channel] += self.gui.fine_step[channel]
                                self.message_back = "ShiftVolt" + str(channel) + " " + "Up"
                            if self.message_b == "Down":
                                self.gui.set_value[channel] -= self.gui.fine_step[channel]
                                self.message_back = "ShiftVolt" + str(channel) + " " + "Down"
                        else:
                            self.message_back = "ShiftVolt" + str(channel) + " " + "Undefined"    

                except:
                # The message is ill defined
                    self.message_back = "Speak Properly"

                # Finally send the message back
                self.socket.send(self.message_back)

            except:
                pass



    def endApplication(self):
        # Cleaning up before shutting down
        for i in range(1,7):
            self.gui.set_value[i] = 0

        # Kill and wait for the processes to be killed
        self.running = 0
        time.sleep(0.1)

        # Turning the analog powermeter device and serial off
        # self.apm._serial_write("OFF")
        # print "Analog powermeter has turned off."


class VoltageHandler:
    """
    Handles the set voltage and give appropriate commands 
    """
    def __init__(self, arg_max_step, arg_channel):
        """
        Initialise the object and giving it initial value
        """
        self.set_voltage = 0
        self.output_voltage = 0
        self.max_step = arg_max_step
        self.channel = arg_channel
        print "Created Object Voltage Handler No. ", self.channel

    def change_set_voltage(self, arg_set_voltage):
        self.set_voltage = arg_set_voltage

    def update(self):
        if self.output_voltage != self.set_voltage:
            if self.output_voltage > self.set_voltage:
                step_down = min((self.output_voltage-self.set_voltage), self.max_step)
                self.output_voltage -= step_down
            elif self.output_voltage < self.set_voltage:
                step_up = min((self.set_voltage-self.output_voltage), self.max_step)
                self.output_voltage += step_up
            ''' Here is where the command line to change the voltage goes '''
            print "Output Voltage ", self.channel, " set to ", self.output_voltage
            sp.call([usbdacprog + " -d " + dac_add + " " + str(self.channel-1) + " " + '%.3f'%round(self.output_voltage,3)], shell=True)
        # Return output_voltage to be displayed on the GUI
        return self.output_voltage

''' Main program goes here '''

rand = random.Random(  )
root = Tkinter.Tk(  )
root.title("Cavity Retreat Version 1.03")

img = Tkinter.PhotoImage(file='icon.png')
root.tk.call('wm', 'iconphoto', root._w, img)

client = ThreadedClient(root)
root.mainloop(  )
