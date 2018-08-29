# -*- coding: utf-8 -*-

#
#   Weather update server
#   Binds PUB socket to tcp://*:5556
#   Publishes random weather updates
#

import zmq
import time
from random import randrange

context = zmq.Context()
socket = context.socket(zmq.PUB)
socket.bind("tcp://*:5556")

# while True:
#     zipcode = randrange(1, 100000)
#     temperature = randrange(-80, 135)
#     relhumidity = randrange(10, 60)
#
#     socket.send_string("%i %i %i" % (zipcode, temperature, relhumidity))

for zipcode in range(100):
    #zipcode = randrange(1, 100000)
    temperature = randrange(-80, 135)
    relhumidity = randrange(10, 60)
    print 'zipcode:', zipcode

    #socket.send_string("%i %i %i" % (zipcode, temperature, relhumidity))
    socket.send_pyobj((zipcode, temperature, relhumidity))
    time.sleep(2)