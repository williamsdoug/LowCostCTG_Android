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

import numpy as np
import os
from jeromq_compat import recv_pyobj, send_pyobj, jmqAgain

# export JAVA_HOME=`/usr/libexec/java_home`
# export CLASSPATH="/Users/doug/Documents/GitHub/LowCostCTG_Android/notebooks/jeromq-0.4.3.jar"

os.environ['JAVA_HOME'] = '/Library/Java/JavaVirtualMachines/jdk1.8.0_131.jdk/Contents/Home'
os.environ['CLASSPATH'] = "/Users/doug/Documents/GitHub/LowCostCTG_Android/notebooks/jeromq-0.4.3.jar"

from jnius import autoclass
zmq = autoclass('org/zeromq/ZMQ')
ZContext = autoclass('org.zeromq.ZContext')

#  Socket to talk to server
context = ZContext()
socket = context.createSocket(zmq.REQ)
socket.connect(ADDRESS_SPEC)
print("Connected to hello world server…")

#  Do 10 requests, waiting each time for a response
data = np.arange(5)
for request in range(10):
    print "Sending request {} …".format(request)
    message = {'msg':"Hello", 'count':request, 'number':data}
    send_pyobj(socket, message)

    #  Get the reply.
    try:
        messageR = recv_pyobj(socket)
    except KeyboardInterrupt:
        print("W: interrupt received, stopping…")
        break

    print "Received reply {}  {} {}".format(request, messageR['count'], messageR['msg'])

# clean up
socket.close()
context.destroy()