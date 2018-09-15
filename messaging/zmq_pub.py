# -*- coding: utf-8 -*-

#
#   Weather update server
#   Binds PUB socket to tcp://*:5556
#   Publishes random weather updates
#

ADDRESS_SPEC = "tcp://*:8888"


from common import  publisher
from zeromq_compat import ZeroMQ

socket = ZeroMQ(ADDRESS_SPEC, ZeroMQ.PUB)
publisher(socket)
