# -*- coding: utf-8 -*-

#
#   Weather update server
#   Binds PUB socket to tcp://*:5556
#   Publishes random weather updates
#

ADDRESS_SPEC = "tcp://*:8888"

import time
from random import randrange
import os
from jeromq_compat import recv_pyobj, send_pyobj, jmqAgain

# export JAVA_HOME=`/usr/libexec/java_home`
# export CLASSPATH="/Users/doug/Documents/GitHub/LowCostCTG_Android/notebooks/jeromq-0.4.3.jar"

os.environ['JAVA_HOME'] = '/Library/Java/JavaVirtualMachines/jdk1.8.0_131.jdk/Contents/Home'
os.environ['CLASSPATH'] = "/Users/doug/Documents/GitHub/LowCostCTG_Android/java/jeromq-0.4.3.jar"

from jnius import autoclass
zmq = autoclass('org/zeromq/ZMQ')
ZContext = autoclass('org.zeromq.ZContext')

context = ZContext()
socket = context.createSocket(zmq.PUB)
socket.bind(ADDRESS_SPEC)

for zipcode in range(100):
    print 'zipcode:', zipcode
    temperature = randrange(-80, 135)
    relhumidity = randrange(10, 60)
    message = (zipcode, temperature, relhumidity)
    send_pyobj(socket, message)
    time.sleep(2)

# clean up
socket.close()
context.destroy()