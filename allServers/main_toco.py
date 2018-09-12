# -*- coding: utf-8 -*-

#
#  Copyright Douglas Williams, 2018
#  All Rights Reserved
#

from TocoServer import TocoServer

from CONFIG import ZMQ_TOCO_SERVER_ADDRESS_SPEC, ZMQ_TOCO_PUB_ADDRESS_SPEC

PREFIX = 'libTocopatch__'
XMQ_SUB_POLLER_GENERATION = None
#
# Server Code
#


# If called at top level, start server
if __name__ == '__main__':
    TocoServer(ZMQ_TOCO_SERVER_ADDRESS_SPEC, ZMQ_TOCO_PUB_ADDRESS_SPEC).serve()