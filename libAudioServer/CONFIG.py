# coding: utf-8

#
#  Copyright Douglas Williams, 2018
#  All Rights Reserved
#


ZMQ_AUDIO_SERVER_ADDRESS_SPEC = "tcp://*:5556"
ZMQ_AUDIO_PUB_ADDRESS_SPEC = "tcp://*:5557"

USE_LIB_AUDIO_EMULATE = True       # select audio library

ENABLE_EMULATE = True      # used by libAudio onlt

EMULATION_RECORDING = 'sample.wav'

EMULATION_SPEEDUP = 1.0
EMULATION_DELAY = 1.0/8/EMULATION_SPEEDUP