# -*- coding: utf-8 -*-

#
#   Hello World client in Python
#   Connects REQ socket to tcp://localhost:5555
#   Sends "Hello" to server, expects "World" back
#

import numpy as np
import time
import sys
from random import randrange
from ZMQ_Again_Exception import ZMQ_Again

NONBLOCK_DELAY = 0.1
PRINT_INTERVAL = 10



def client(socket):
    #  Do 10 requests, waiting each time for a response
    data = np.arange(5)
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


def server(socket):
    wait_count = 1
    while True:
        #  Wait for next request from client
        try:
            message = socket.recv_pyobj(blocking=False)
            wait_count = 1
        except ZMQ_Again:      #zmq.error.Again:
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
        socket.send_pyobj(messageR)

    # clean up
    socket.close()


def publisher(socket):

    for zipcode in range(100):
        print 'zipcode:', zipcode
        temperature = randrange(-80, 135)
        relhumidity = randrange(10, 60)
        message = (zipcode, temperature, relhumidity)
        socket.send_pyobj(message)
        time.sleep(2)

    # clean up
    socket.close()

def subscriber(socket):
    zip_filter =  "10001"   # Subscribe to zipcode, default is NYC, 10001

    # Process 5 updates
    total_temp = 0
    for update_nbr in range(5):
        zipcode, temperature, relhumidity = socket.recv_pyobj()

        print zipcode, temperature, relhumidity
        total_temp += int(temperature)

    print "Average temperature for zipcode '{}' was {}".format(zip_filter, total_temp / (update_nbr+1))
    socket.close()
