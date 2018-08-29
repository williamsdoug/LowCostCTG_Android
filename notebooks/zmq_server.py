# -*- coding: utf-8 -*-

#
#   Hello World server in Python
#   Binds REP socket to tcp://*:5555
#   Expects b"Hello" from client, replies with b"World"
#

import sys
import time
import zmq

context = zmq.Context()
socket = context.socket(zmq.REP)
socket.bind("tcp://*:5555")

NONBLOCK_DELAY = 0.1
PRINT_INTERVAL = 10

wait_count = 1

while True:
    #  Wait for next request from client
    try:
        message = socket.recv_pyobj(flags=zmq.NOBLOCK)
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

    #  Do some 'work'
    time.sleep(1)

    #  Send reply back to client
    messageR = {'msg':"World", 'count':count}
    socket.send_pyobj(messageR)


# clean up
socket.close()
context.term()