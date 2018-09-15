# -*- coding: utf-8 -*-

#
#   Hello World client in Python
#   Connects REQ socket to tcp://localhost:5555
#   Sends "Hello" to server, expects "World" back
#

ADDRESS_SPEC = "tcp://localhost:5555"
#ADDRESS_SPEC = "tcp://192.168.86.181:5555"
#ADDRESS_SPEC = "tcp://127.0.0.1:5678"


from common import client
from jeromq_compat import ZeroMQ

socket = ZeroMQ(ADDRESS_SPEC, ZeroMQ.REQ)
client(socket)
