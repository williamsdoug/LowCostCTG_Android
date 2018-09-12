# coding: utf-8

#
#  Copyright Douglas Williams, 2018
#  All Rights Reserved
#

ZMQ_BATCH_SERVER_ADDRESS_SPEC = "tcp://*:5555"

ZMQ_AUDIO_SERVER_ADDRESS_SPEC = "tcp://*:5556"
ZMQ_AUDIO_PUB_ADDRESS_SPEC = "tcp://*:5557"

ZMQ_TOCO_SERVER_ADDRESS_SPEC = "tcp://*:5558"
ZMQ_TOCO_PUB_ADDRESS_SPEC = "tcp://*:5559"

#
# Emulation Common
#

EMULATION_SPEEDUP = 1.0

#
# Audio Server
#

USE_LIB_AUDIO_EMULATE = True       # select audio library
ENABLE_EMULATE = True      # used by libAudio only
EMULATION_RECORDING = 'sample.wav'
EMULATION_DELAY = 1.0/8/EMULATION_SPEEDUP

#
# Toco Server
#

TOCO_ENABLE_EMULATE = True
TOCO_EMULATION_RECORDING = 'toco_sample.csv'
TOCO_EMULATION_DELAY = (16.0/16.0)/EMULATION_SPEEDUP      # update interval/packets_per_sec
