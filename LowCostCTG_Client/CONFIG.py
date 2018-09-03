
#
# ZMQ Configuration
#

# Address for each RPC server
ZMQ_CLIENT_ADDRESS_SPEC = {
    'libDecel':{'addr':"tcp://localhost:5555", 'type':'req'},
    'libAudio':{'addr':"tcp://localhost:5556", 'type':'req'},
    'libAudioCallbacks':{'addr':"tcp://localhost:5557",'type':'sub'},
}

