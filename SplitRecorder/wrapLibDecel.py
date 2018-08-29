# -*- coding: utf-8 -*-

from libDecel import extractAllDecels as _extractAllDecels
from libDecel import summarizeDecels as _summarizeDecels
from paramsDecel import FEATURE_EXTRACT_PARAMS

import cPickle as pickle
import zmq

ZMQ_CLIENT = None


#
# Non RPC Debug Versions
#

def dummy_extractAllDecels(*args, **vargs):
    debug = True
    if debug:
        print 'extractAllDecels'

    # allExtractorParams contains functions, so won't properly  serialize
    if 'allExtractorParams' in vargs:
        assert vargs['allExtractorParams'] == FEATURE_EXTRACT_PARAMS
        del vargs['allExtractorParams']

    if debug:
        print 'args:'
        for i,v in enumerate(args):
            print 'arg: {}'.format(i)
            pickle.dumps(v)

        print 'vargs'
        for k, v in vargs.items():
            print 'arg: {}'.format(k)
            pickle.dumps(v)
        print

    message = pickle.dumps(['extractAllDecels', args, vargs])
    _, args1, vargs1 = pickle.loads(message)
    vargs['allExtractorParams'] = FEATURE_EXTRACT_PARAMS
    return _extractAllDecels(*args, **vargs)


def dummy_summarizeDecels(*args, **vargs):
    debug = True
    if debug:
        print 'summarizeDecels'
        print 'args:'
        for i,v in enumerate(args):
            print 'arg: {}'.format(i)
            pickle.dumps(v)

        print 'vargs'
        for k, v in vargs.items():
            print 'arg: {}'.format(k)
            pickle.dumps(v)
        print
    message = pickle.dumps(['summarizeDecels', args, vargs])
    _, args1, vargs1 = pickle.loads(message)
    return _summarizeDecels(*args, **vargs)


#
# client code
#

def get_client():
    global ZMQ_CLIENT
    if ZMQ_CLIENT is None:
        context = zmq.Context()
        socket = context.socket(zmq.REQ)
        socket.connect("tcp://localhost:5555")

        ZMQ_CLIENT = {'context':context, 'socket':socket}
    else:
        context = ZMQ_CLIENT['context']
        socket = ZMQ_CLIENT['socket']

    return context, socket


def extractAllDecels(*args, **vargs):
    print 'called extractAllDecels'

    # allExtractorParams contains functions, so won't properly  serialize
    if 'allExtractorParams' in vargs:
        assert vargs['allExtractorParams'] == FEATURE_EXTRACT_PARAMS
        del vargs['allExtractorParams']

    return client_common('extractAllDecels', args, vargs)


def summarizeDecels(*args, **vargs):
    print 'called summarizeDecels'
    return client_common('summarizeDecels', args, vargs)


def client_common(fun_name, args, vargs):
    context, socket = get_client()
    socket.send_pyobj([fun_name, args, vargs])
    print 'client_common -- send function request'
    success, ret = socket.recv_pyobj()
    print 'client_common -- received response'

    if success:
        return ret
    else:
        print 'client_common -- received exception'
        raise Exception(ret)


#
# Server Code
#

SERVED_FUNCTIONS = {
    'summarizeDecels':_summarizeDecels,
    'extractAllDecels':_extractAllDecels,
}


def server():
    global SERVED_FUNCTIONS
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind("tcp://*:5555")

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