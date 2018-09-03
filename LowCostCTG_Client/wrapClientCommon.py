# -*- coding: utf-8 -*-


import zmq

from CONFIG import ZMQ_CLIENT_ADDRESS_SPEC


ZMQ_CLIENT = {}


#
# client code
#

def get_client(endpoint):
    global ZMQ_CLIENT, ZMQ_CLIENT_ADDRESS_SPEC
    if endpoint not in ZMQ_CLIENT:

        assert endpoint in ZMQ_CLIENT_ADDRESS_SPEC
        entry = ZMQ_CLIENT_ADDRESS_SPEC[endpoint]
        context = zmq.Context()
        if entry['type'] == 'req':
            socket = context.socket(zmq.REQ)
        elif entry['type'] == 'sub':
            socket = context.socket(zmq.SUB)

        socket.connect(entry['addr'])
        if entry['type'] == 'sub':
            socket.setsockopt(zmq.SUBSCRIBE, b"")

        ZMQ_CLIENT[endpoint] = {'context':context, 'socket':socket}
    else:
        context = ZMQ_CLIENT[endpoint]['context']
        socket = ZMQ_CLIENT[endpoint]['socket']

    return context, socket


def client_common(fun_name, args, vargs, endpoint='libDecel'):
    context, socket = get_client(endpoint)
    socket.send_pyobj([fun_name, args, vargs])
    print 'client_common -- send function request'
    success, ret = socket.recv_pyobj()
    print 'client_common -- received response'

    if success:
        return ret
    else:
        print 'client_common -- received exception'
        raise Exception(ret)

