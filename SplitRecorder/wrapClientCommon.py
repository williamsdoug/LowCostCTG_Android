# -*- coding: utf-8 -*-


import zmq


# Address for each RPC server
ZMQ_CLIENT_ADDRESS_SPEC = {
    'libDecel':"tcp://localhost:5555",
}

ZMQ_CLIENT = {}


#
# client code
#

def get_client(endpoint):
    global ZMQ_CLIENT, ZMQ_CLIENT_ADDRESS_SPEC
    if endpoint not in ZMQ_CLIENT:

        assert endpoint in ZMQ_CLIENT_ADDRESS_SPEC
        context = zmq.Context()
        socket = context.socket(zmq.REQ)
        socket.connect(ZMQ_CLIENT_ADDRESS_SPEC[endpoint])

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

