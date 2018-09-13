# -*- coding: utf-8 -*-

#
#  Copyright Douglas Williams, 2018
#  All Rights Reserved
#

from TocoServer import TocoServer, getTocoServer

# start server
if __name__ == '__main__':
    #svr = TocoServer(ZMQ_TOCO_SERVER_ADDRESS_SPEC, ZMQ_TOCO_PUB_ADDRESS_SPEC)
    svr = getTocoServer()
    if True:
        svr.serve()
    else:
        svr.start()
        svr.wait()
