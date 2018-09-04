# coding: utf-8

#
#  Copyright Douglas Williams, 2018
#  All Rights Reserved
#

#
# ZMQ Configuration
#

# Address for each RPC server
ZMQ_CLIENT_ADDRESS_SPEC = {
    'libDecel':{'addr':"tcp://localhost:5555", 'type':'req'},
    'libAudio':{'addr':"tcp://localhost:5556", 'type':'req'},
    'libAudioCallbacks':{'addr':"tcp://localhost:5557",'type':'sub'},
    'libTocopatch':{'addr':"tcp://localhost:5558", 'type':'req'},
    'libTocopatchCallbacks':{'addr':"tcp://localhost:5559",'type':'sub'},
}

