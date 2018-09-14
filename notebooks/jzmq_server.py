# -*- coding: utf-8 -*-

#
#   Hello World server in Python
#   Binds REP socket to tcp://*:5555
#   Expects b"Hello" from client, replies with b"World"
#

ADDRESS_SPEC = "tcp://*:5555"
NONBLOCK_DELAY = 0.1
PRINT_INTERVAL = 10

import sys
import time
import os
from jeromq_compat import recv_pyobj, send_pyobj, jmqAgain

# export JAVA_HOME=`/usr/libexec/java_home`
# export CLASSPATH="/Users/doug/Documents/GitHub/LowCostCTG_Android/notebooks/jeromq-0.4.3.jar"

os.environ['JAVA_HOME'] = '/Library/Java/JavaVirtualMachines/jdk1.8.0_131.jdk/Contents/Home'
os.environ['CLASSPATH'] = "/Users/doug/Documents/GitHub/LowCostCTG_Android/java/jeromq-0.4.3.jar"

from jnius import autoclass
ZMQ = autoclass('org/zeromq/ZMQ')
ZContext = autoclass('org.zeromq.ZContext')

context = ZContext()
socket = context.createSocket(ZMQ.REP)
socket.bind(ADDRESS_SPEC)

wait_count = 1
while True:
    #  Wait for next request from client
    try:
        message = recv_pyobj(socket, blocking=False)
        wait_count = 1
    except jmqAgain:      #zmq.error.Again:
        wait_count += 1
        if wait_count % PRINT_INTERVAL == 0:
            print wait_count,
            sys.stdout.flush()
        time.sleep(NONBLOCK_DELAY)
        continue
    except KeyboardInterrupt:
        print("W: interrupt received, stopping…")
        break

    print "Received request: {} {}".format(message['count'],  message['msg'])
    print 'data', type(message['number']), type(message['number'][0]), message['number']
    count = message['count']

    time.sleep(1)    #  Do some 'work'

    #  Send reply back to client
    messageR = {'msg':"World", 'count':count}
    send_pyobj(socket, messageR)

# clean up
socket.close()
context.destroy()