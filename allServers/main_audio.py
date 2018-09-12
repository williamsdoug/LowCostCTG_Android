# -*- coding: utf-8 -*-

#
#  Copyright Douglas Williams, 2018
#  All Rights Reserved
#

from AudioServer import AudioServer

from CONFIG import ZMQ_AUDIO_SERVER_ADDRESS_SPEC, ZMQ_AUDIO_PUB_ADDRESS_SPEC

PREFIX = 'audio_recorder__'
XMQ_SUB_POLLER_GENERATION = None
#
# Server Code
#


# If called at top level, start server
if __name__ == '__main__':
    AudioServer(ZMQ_AUDIO_SERVER_ADDRESS_SPEC, ZMQ_AUDIO_PUB_ADDRESS_SPEC).serve()