# -*- coding: utf-8 -*-

#
#   Hello World client in Python
#   Connects REQ socket to tcp://localhost:5555
#   Sends "Hello" to server, expects "World" back
#

import zmq
import time
import sys
import numpy as np

NONBLOCK_DELAY = 0.1
PRINT_INTERVAL = 10

context = zmq.Context()


#  Socket to talk to server
print("Connecting to hello world server…")
socket = context.socket(zmq.REQ)
socket.connect("tcp://localhost:5555")

data = np.arange(5)

#  Do 10 requests, waiting each time for a response
for request in range(10):
    print "Sending request {} …".format(request)

    message = {'msg':"Hello", 'count':request, 'number':data}
    socket.send_pyobj(message)

    #  Get the reply.
    try:
        messageR = socket.recv_pyobj()
    except KeyboardInterrupt:
        print("W: interrupt received, stopping…")
        break

    print "Received reply {}  {} {}".format(request, messageR['count'], messageR['msg'])

# clean up
socket.close()
context.term()