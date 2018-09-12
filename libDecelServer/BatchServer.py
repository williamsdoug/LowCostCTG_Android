# -*- coding: utf-8 -*-

#
#  Copyright Douglas Williams, 2018
#  All Rights Reserved
#

from libDecel import extractAllDecels, summarizeDecels
from paramsDecel import FEATURE_EXTRACT_PARAMS
from libUC import findUC

import zmq

#
# Server Code
#

SERVED_FUNCTIONS = {
    'summarizeDecels':summarizeDecels,
    'extractAllDecels':extractAllDecels,
    'findUC':findUC,
}


def batchServer(rpc_address_spec):
    global SERVED_FUNCTIONS
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind(rpc_address_spec)

    run = True
    while run:
        fun_name, args, vargs = socket.recv_pyobj()
        'wrapLibDecel server -- received {}'.format(fun_name)

        if fun_name == 'exit':
            # terminate gracefully
            socket.send_pyobj([True, 'byebye'])
            run = False

        elif fun_name in SERVED_FUNCTIONS:
            # special case handling for
            if fun_name == 'extractAllDecels':
                vargs['allExtractorParams'] = FEATURE_EXTRACT_PARAMS

            # execute function call locally
            try:
                ret = SERVED_FUNCTIONS[fun_name](*args, **vargs)

                print 'wrapLibDecel server -- returning response'
                socket.send_pyobj([True, ret])
            except Exception, e:
                print 'wrapLibDecel server -- returning exception {}'.format(e)
                socket.send_pyobj([False, e])
        else:
            # unknown function
            msg = 'wrapLibDecel server -- Unknown function {}'.format(fun_name)
            print msg
            socket.send_pyobj([False, msg])
