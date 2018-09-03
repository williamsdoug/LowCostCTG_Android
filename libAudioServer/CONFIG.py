ZMQ_SERVER_ADDRESS_SPEC = "tcp://*:5556"
ZMQ_PUB_ADDRESS_SPEC = "tcp://*:5557"

USE_LIB_AUDIO_EMULATE = True       # select audio library

ENABLE_EMULATE = True      # used by libAudio onlt

EMULATION_RECORDING = 'sample.wav'

#EMULATION_DELAY = 1.0/8       # Normal Speed
#EMULATION_DELAY = 1.0/8/4     # 4x speedup
EMULATION_DELAY = 1.0/8/2     # 4x speedup