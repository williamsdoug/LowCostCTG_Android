# coding: utf-8

#
#  Copyright Douglas Williams, 2018
#  All Rights Reserved
#

USE_ANDROID = False
#USE_ANDROID = True



ZMQ_BATCH_SERVER_ADDRESS_SPEC = "tcp://*:5555"

ZMQ_AUDIO_SERVER_ADDRESS_SPEC = "tcp://*:5556"
ZMQ_AUDIO_PUB_ADDRESS_SPEC = "tcp://*:5557"

ZMQ_TOCO_SERVER_ADDRESS_SPEC = "tcp://*:5558"
ZMQ_TOCO_PUB_ADDRESS_SPEC = "tcp://*:5559"


if USE_ANDROID:
    from sample_resolver import resolve_sample_android as resolve
else:
    from sample_resolver import resolve_sample as resolve



#
# Emulation Common
#

EMULATION_SPEEDUP = 1.0

#
# Audio Server
#

USE_LIB_AUDIO_EMULATE = True       # select audio library
ENABLE_EMULATE = True      # used by libAudio only
EMULATION_RECORDING = resolve('sample.wav')
EMULATION_DELAY = 1.0/8/EMULATION_SPEEDUP

#
# Toco Server
#

TOCO_ENABLE_EMULATE = True
TOCO_EMULATION_RECORDING = resolve('toco_sample.csv')
TOCO_EMULATION_DELAY = (16.0/16.0)/EMULATION_SPEEDUP      # update interval/packets_per_sec
