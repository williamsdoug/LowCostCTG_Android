# -*- coding: utf-8 -*-

#
#   Weather update client
#   Connects SUB socket to tcp://localhost:5556
#   Collects weather updates and finds avg temp in zipcode
#

ADDRESS_SPEC = "tcp://localhost:8888"


from common import subscriber
from jeromq_compat import ZeroMQ

socket = ZeroMQ(ADDRESS_SPEC, ZeroMQ.SUB)
subscriber(socket)
