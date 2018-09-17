# coding: utf-8

#
#  Copyright Douglas Williams, 2018
#  All Rights Reserved
#

# Address for each RPC server
def set_address_spec(ip):
    global ZMQ_CLIENT_ADDRESS_SPEC
    ZMQ_CLIENT_ADDRESS_SPEC = {
        'libDecel':             {'addr':"tcp://" + ip + ":5555", 'type':'req'},
        'libAudio':             {'addr':"tcp://" + ip + ":5556", 'type':'req'},
        'libAudioCallbacks':    {'addr':"tcp://" + ip + ":5557",'type':'sub'},
        'libTocopatch':         {'addr':"tcp://" + ip + ":5558", 'type':'req'},
        'libTocopatchCallbacks':{'addr':"tcp://" + ip + ":5559",'type':'sub'},
    }


#
# ZMQ Configuration
#
USE_LOCALHOST = True

ANDROID_IP = "192.168.86.181"     # remote IP Address

if USE_LOCALHOST:
    ANDROID_IP = "localhost"


set_address_spec(ANDROID_IP)    # Define default address for each RPC server
                                # can override  by subsequent calls to set_address_spec

# Below parameters relate to use JeroMQ native java library

USE_JEROMQ = True          # Delectes between ZeroMQ and JeroMQ
DEFINE_JAVA_PATHS = True    # Define paths prior to invocation of pyjnius

JAVA_HOME = '/Library/Java/JavaVirtualMachines/jdk1.8.0_131.jdk/Contents/Home'
CLASSPATH = "/Users/doug/Documents/GitHub/LowCostCTG_Android/LowCostCTG_Client/jeromq-0.4.3.jar" \
            + ":" + "/Users/doug/Documents/GitHub/LowCostCTG_Android/LowCostCTG_Client/jeromqfixer.jar"



