# -*- coding: utf-8 -*-

#
#   Weather update client
#   Connects SUB socket to tcp://localhost:5556
#   Collects weather updates and finds avg temp in zipcode
#

ADDRESS_SPEC = "tcp://localhost:8888"


import sys
import os
from jeromq_compat import recv_pyobj, send_pyobj, jmqAgain

# export JAVA_HOME=`/usr/libexec/java_home`
# export CLASSPATH="/Users/doug/Documents/GitHub/LowCostCTG_Android/notebooks/jeromq-0.4.3.jar"

os.environ['JAVA_HOME'] = '/Library/Java/JavaVirtualMachines/jdk1.8.0_131.jdk/Contents/Home'
os.environ['CLASSPATH'] = "/Users/doug/Documents/GitHub/LowCostCTG_Android/java/jeromq-0.4.3.jar" \
                          + ":" + "/Users/doug/Documents/GitHub/LowCostCTG_Android/java/jeromqfixer.jar"

from jnius import autoclass
zmq = autoclass('org/zeromq/ZMQ')
ZContext = autoclass('org.zeromq.ZContext')
Subscriber = autoclass('com.ddw_gd.jeromqfixer.JeromqFixer')

context = ZContext()
socket = context.createSocket(zmq.SUB)
socket.connect(ADDRESS_SPEC)
Subscriber.subscribe(socket)

# Subscribe to zipcode, default is NYC, 10001
zip_filter = sys.argv[1] if len(sys.argv) > 1 else "10001"

# Process 5 updates
total_temp = 0
for update_nbr in range(5):
    zipcode, temperature, relhumidity = recv_pyobj(socket)

    print zipcode, temperature, relhumidity
    total_temp += int(temperature)

print "Average temperature for zipcode '{}' was {}".format(zip_filter, total_temp / (update_nbr+1))

# clean up
socket.close()
context.destroy()