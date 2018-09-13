# coding: utf-8

#
#  Copyright Douglas Williams, 2018
#  All Rights Reserved
#

USE_ANDROID = False
#USE_ANDROID = True

if USE_ANDROID:
    from sample_resolver import resolve_sample_android as resolve
else:
    from sample_resolver import resolve_sample as resolve


ZMQ_TOCO_SERVER_ADDRESS_SPEC = "tcp://*:5558"
ZMQ_TOCO_PUB_ADDRESS_SPEC = "tcp://*:5559"

TOCO_ENABLE_EMULATE = True
TOCO_EMULATION_RECORDING = resolve('toco_sample.csv')

EMULATION_SPEEDUP = 1.0
TOCO_EMULATION_DELAY = (16.0/16.0)/EMULATION_SPEEDUP      # update interval/packets_per_sec
