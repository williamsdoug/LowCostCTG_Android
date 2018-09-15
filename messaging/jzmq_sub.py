# -*- coding: utf-8 -*-

#
#   Weather update client
#   Connects SUB socket to tcp://localhost:5556
#   Collects weather updates and finds avg temp in zipcode
#

ADDRESS_SPEC = "tcp://localhost:8888"

from set_java_environment import set_java_home_and_classpath
# must be executed before import from jeromq_compat
set_java_home_and_classpath()

from common import subscriber
from jeromq_compat import ZeroMQ

socket = ZeroMQ(ADDRESS_SPEC, ZeroMQ.SUB)
subscriber(socket)
