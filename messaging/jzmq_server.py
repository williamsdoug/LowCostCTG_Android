# -*- coding: utf-8 -*-

#
#   Hello World server in Python
#   Binds REP socket to tcp://*:5555
#   Expects b"Hello" from client, replies with b"World"
#

ADDRESS_SPEC = "tcp://*:6666"

from set_java_environment import set_java_home_and_classpath
# must be executed before import from jeromq_compat
set_java_home_and_classpath()

from common import server
from jeromq_compat import ZeroMQ

socket = ZeroMQ(ADDRESS_SPEC, ZeroMQ.REP)
server(socket)