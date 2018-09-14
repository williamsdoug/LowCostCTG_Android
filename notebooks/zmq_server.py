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
import zmq
from zeromq_compat import recv_pyobj, send_pyobj

context = zmq.Context()
socket = context.socket(zmq.REP)
socket.bind(ADDRESS_SPEC)

wait_count = 1

while True:
    #  Wait for next request from client
    try:
        #message = socket.recv_pyobj(flags=zmq.NOBLOCK)
        message = recv_pyobj(socket, blocking=False)
        wait_count = 1
    except zmq.Again: #zmq.error.Again:
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
    #socket.send_pyobj(messageR)
    send_pyobj(socket, messageR)


# clean up
socket.close()
context.term()