# -*- coding: utf-8 -*-

#
#  Copyright Douglas Williams, 2018
#  All Rights Reserved
#

from BatchServer import BatchServer, getBatchServer

# start server
if __name__ == '__main__':
    #svr = BatchServer(ZMQ_BATCH_SERVER_ADDRESS_SPEC)
    svr = getBatchServer()
    if True:
        svr.serve()
    else:
        svr.start()
        svr.wait()
