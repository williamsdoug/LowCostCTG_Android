# -*- coding: utf-8 -*-

#
#   Weather update client
#   Connects SUB socket to tcp://localhost:5556
#   Collects weather updates and finds avg temp in zipcode
#

import sys
import zmq
from zeromq_compat import recv_pyobj, send_pyobj

#  Socket to talk to server
context = zmq.Context()
socket = context.socket(zmq.SUB)
socket.connect("tcp://localhost:8888")
socket.setsockopt(zmq.SUBSCRIBE, b"")

# Subscribe to zipcode, default is NYC, 10001
zip_filter = sys.argv[1] if len(sys.argv) > 1 else "10001"

# Process 5 updates
total_temp = 0
for update_nbr in range(5):
    zipcode, temperature, relhumidity = recv_pyobj(socket)
    print zipcode, temperature, relhumidity
    total_temp += int(temperature)

print "Average temperature for zipcode '{}' was {}".format(zip_filter, total_temp / (update_nbr+1))
