# -*- coding: utf-8 -*-

#
#   Weather update server
#   Binds PUB socket to tcp://*:5556
#   Publishes random weather updates
#

ADDRESS_SPEC = "tcp://*:8888"

from set_java_environment import set_java_home_and_classpath
# must be executed before import from jeromq_compat
set_java_home_and_classpath()

from common import  publisher
from jeromq_compat import ZeroMQ

socket = ZeroMQ(ADDRESS_SPEC, ZeroMQ.PUB)
publisher(socket)
