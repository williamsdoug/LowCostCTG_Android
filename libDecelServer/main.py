# -*- coding: utf-8 -*-

from libDecel import extractAllDecels, summarizeDecels
from paramsDecel import FEATURE_EXTRACT_PARAMS

import zmq


ZMQ_SERVER_ADDRESS_SPEC = "tcp://*:5555"


#
# Server Code
#

SERVED_FUNCTIONS = {
    'summarizeDecels':summarizeDecels,
    'extractAllDecels':extractAllDecels,
}


def server():
    global SERVED_FUNCTIONS, ZMQ_SERVER_ADDRESS_SPEC
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind(ZMQ_SERVER_ADDRESS_SPEC)

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


# If called at top level, start server
if __name__ == '__main__':
    server()