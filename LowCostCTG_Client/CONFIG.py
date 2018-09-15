# coding: utf-8

#
#  Copyright Douglas Williams, 2018
#  All Rights Reserved
#

#
# ZMQ Configuration
#
USE_LOCALHOST = True

ANDROID_IP = "192.168.86.181"

# Address for each RPC server
if USE_LOCALHOST:
    ZMQ_CLIENT_ADDRESS_SPEC = {
        'libDecel':{'addr':"tcp://localhost:5555", 'type':'req'},
        'libAudio':{'addr':"tcp://localhost:5556", 'type':'req'},
        'libAudioCallbacks':{'addr':"tcp://localhost:5557",'type':'sub'},
        'libTocopatch':{'addr':"tcp://localhost:5558", 'type':'req'},
        'libTocopatchCallbacks':{'addr':"tcp://localhost:5559",'type':'sub'},
    }
else:
    ZMQ_CLIENT_ADDRESS_SPEC = {
        'libDecel':             {'addr':"tcp://" + ANDROID_IP + ":5555", 'type':'req'},
        'libAudio':             {'addr':"tcp://" + ANDROID_IP + ":5556", 'type':'req'},
        'libAudioCallbacks':    {'addr':"tcp://" + ANDROID_IP + ":5557",'type':'sub'},
        'libTocopatch':         {'addr':"tcp://" + ANDROID_IP + ":5558", 'type':'req'},
        'libTocopatchCallbacks':{'addr':"tcp://" + ANDROID_IP + ":5559",'type':'sub'},
    }

# Below parameters relate to use JeroMQ native java library

USE_JEROMQ = True          # Delectes between ZeroMQ and JeroMQ
DEFINE_JAVA_PATHS = True    # Define paths prior to invocation of pyjnius

JAVA_HOME = '/Library/Java/JavaVirtualMachines/jdk1.8.0_131.jdk/Contents/Home'
CLASSPATH = "/Users/doug/Documents/GitHub/LowCostCTG_Android/LowCostCTG_Client/jeromq-0.4.3.jar" \
            + ":" + "/Users/doug/Documents/GitHub/LowCostCTG_Android/LowCostCTG_Client/jeromqfixer.jar"



