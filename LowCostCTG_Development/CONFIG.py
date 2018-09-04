
#
# Select RPC vs local by function
#

LIBAUDIO_USE_REMOTE = False
LIBDECEL_USE_REMOTE = False
LIBTOCOPATCH_USE_REMOTE = True


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


#
# libAudio Configuration
#

USE_LIB_AUDIO_EMULATE = True       # select audio library
ENABLE_EMULATE = True      # used by libAudio onlt
EMULATION_RECORDING = 'sample.wav'
EMULATION_SPEEDUP = 1.0
EMULATION_DELAY = 1.0/8/EMULATION_SPEEDUP


#
# libTocopatchDevice
#

TOCO_ENABLE_EMULATE = True
TOCO_EMULATION_RECORDING = 'toco_sample.csv'
TOCO_EMULATION_DELAY = (16.0/16.0)/EMULATION_SPEEDUP      # update interval/packets_per_sec


