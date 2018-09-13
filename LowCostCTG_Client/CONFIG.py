# coding: utf-8

#
#  Copyright Douglas Williams, 2018
#  All Rights Reserved
#

#
# ZMQ Configuration
#
USE_LOCALHOST = False

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

