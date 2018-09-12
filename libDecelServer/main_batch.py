# -*- coding: utf-8 -*-

#
#  Copyright Douglas Williams, 2018
#  All Rights Reserved
#

from BatchServer import batchServer

from CONFIG import ZMQ_BATCH_SERVER_ADDRESS_SPEC

# If called at top level, start server
if __name__ == '__main__':
    batchServer(ZMQ_BATCH_SERVER_ADDRESS_SPEC)