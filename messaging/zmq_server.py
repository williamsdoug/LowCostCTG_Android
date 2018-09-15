# -*- coding: utf-8 -*-

#
#   Hello World client in Python
#   Connects REQ socket to tcp://localhost:5555
#   Sends "Hello" to server, expects "World" back
#

ADDRESS_SPEC = "tcp://*:5555"

from common import server
from zeromq_compat import ZeroMQ

socket = ZeroMQ(ADDRESS_SPEC, ZeroMQ.REP)
server(socket)
