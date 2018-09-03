
#
# Select RPC vs local by function
#

LIBAUDIO_USE_REMOTE = False
LIBDECEL_USE_REMOTE = False


#
# ZMQ Configuration
#

# Address for each RPC server
ZMQ_CLIENT_ADDRESS_SPEC = {
    'libDecel':{'addr':"tcp://localhost:5555", 'type':'req'},
    'libAudio':{'addr':"tcp://localhost:5556", 'type':'req'},
    'libAudioCallbacks':{'addr':"tcp://localhost:5557",'type':'sub'},
}


#
# libAudio Configuration
#

USE_LIB_AUDIO_EMULATE = True       # select audio library

ENABLE_EMULATE = True      # used by libAudio onlt

EMULATION_RECORDING = 'sample.wav'

#EMULATION_DELAY = 1.0/8       # Normal Speed
#EMULATION_DELAY = 1.0/8/4     # 4x speedup
EMULATION_DELAY = 1.0/8/2     # 4x speedup


