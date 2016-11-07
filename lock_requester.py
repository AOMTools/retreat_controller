#   Hello World client in Python
#   Connects REQ socket to tcp://localhost:5555
#   Sends "Hello" to server, expects "World" back

''' 
PROTOCOL TO COMMUNICATE WITH THE RETREAT CONTROLLER
The command is given in two words, and the reply is also given in two words.
You need to send a command and receive a reply. It needs to be a 1 send 1 receive for every time.
Please respect this convention, as ill-defined messages will get burned into hell.

List of commands:
- Please Lock 
	List of reply: "Okay Boss", "Lock Nonexistent" 
- Please Annihilate
	List of reply: "Okay Boss"
- Check Lock
	List of reply: "Lock Successful", "Lock Unsuccessful", "Still Locking", "Something Wrong"
- CheckVolt X
	List of reply: "VoltX Y", "VoltX Undefined"
- SetVoltX Y
	List of reply: "SetVoltX Y", "SetVoltX Undefined"
- ShiftVoltX Up/Down
	List of reply: "ShiftVoltX Up", "ShiftVoltX Down", "ShiftVoltX Undefined"
'''


import zmq
import time

context = zmq.Context()

#  Socket to talk to server
print "Connecting to the retreat controller server"
socket = context.socket(zmq.REQ)
socket.connect("tcp://localhost:5556")

while True:
    print "Sending request to lock"
    socket.send("Please Lock")

    #  Get the reply.
    message = socket.recv()
    print "Received reply : ", message
    time.sleep(5)
