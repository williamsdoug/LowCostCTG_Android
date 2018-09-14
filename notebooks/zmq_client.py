# -*- coding: utf-8 -*-

#
#   Hello World client in Python
#   Connects REQ socket to tcp://localhost:5555
#   Sends "Hello" to server, expects "World" back
#

NONBLOCK_DELAY = 0.1
PRINT_INTERVAL = 10

ADDRESS_SPEC = "tcp://localhost:5555"
#ADDRESS_SPEC = "tcp://192.168.86.181:5555"
#ADDRESS_SPEC = "tcp://127.0.0.1:5678"

import zmq
import numpy as np
from zeromq_compat import recv_pyobj, send_pyobj

#  Socket to talk to server
context = zmq.Context()
socket = context.socket(zmq.REQ)
socket.connect(ADDRESS_SPEC)
print("Connected to hello world server…")

#  Do 10 requests, waiting each time for a response
data = np.arange(5)
for request in range(10):
    print "Sending request {} …".format(request)
    message = {'msg':"Hello", 'count':request, 'number':data}
    #socket.send_pyobj(message)
    send_pyobj(socket, message)

    #  Get the reply.
    try:
        #messageR = socket.recv_pyobj()
        messageR = recv_pyobj(socket)
    except KeyboardInterrupt:
        print("W: interrupt received, stopping…")
        break

    print "Received reply {}  {} {}".format(request, messageR['count'], messageR['msg'])

# clean up
socket.close()
context.term()