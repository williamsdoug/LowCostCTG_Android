# -*- coding: utf-8 -*-

#
#   Weather update server
#   Binds PUB socket to tcp://*:5556
#   Publishes random weather updates
#

import zmq
import time
from random import randrange
from zeromq_compat import recv_pyobj, send_pyobj

context = zmq.Context()
socket = context.socket(zmq.PUB)
socket.bind("tcp://*:8888")

for zipcode in range(100):
    print 'zipcode:', zipcode
    temperature = randrange(-80, 135)
    relhumidity = randrange(10, 60)
    send_pyobj(socket, (zipcode, temperature, relhumidity))
    time.sleep(2)