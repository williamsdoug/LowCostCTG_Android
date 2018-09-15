# -*- coding: utf-8 -*-

#
#  Copyright Douglas Williams, 2018
#  All Rights Reserved
#


from CONFIG import ZMQ_CLIENT_ADDRESS_SPEC

from ZMQ_Again_Exception import ZMQ_Again

try:
    from CONFIG import USE_JEROMQ
except Exception:
    USE_JEROMQ = False


if USE_JEROMQ:
    try:
        from CONFIG import DEFINE_JAVA_PATHS
    except Exception:
        DEFINE_JAVA_PATHS = False

    if DEFINE_JAVA_PATHS:    # Define paths prior to invocation of pyjnius
        import os
        from CONFIG import JAVA_HOME, CLASSPATH
        os.environ['JAVA_HOME'] = JAVA_HOME
        os.environ['CLASSPATH'] = CLASSPATH

    from jeromq_compat import ZeroMQ
else:
    from zeromq_compat import ZeroMQ


ZMQ_CLIENT = {}


#
# client code
#

def get_client(endpoint):
    global ZMQ_CLIENT, ZMQ_CLIENT_ADDRESS_SPEC
    if endpoint not in ZMQ_CLIENT:

        assert endpoint in ZMQ_CLIENT_ADDRESS_SPEC
        entry = ZMQ_CLIENT_ADDRESS_SPEC[endpoint]

        modes = {'req':ZeroMQ.REQ, 'rep':ZeroMQ.REP, 'pub':ZeroMQ.PUB, 'sub':ZeroMQ.SUB}
        assert entry['type'] in modes

        print 'Creating socket', endpoint,entry['addr'], modes[entry['type']]

        socket = ZeroMQ(entry['addr'], modes[entry['type']])
        print 'Socket Created'
        ZMQ_CLIENT[endpoint] = socket
    else:
        socket = ZMQ_CLIENT[endpoint]

    return socket


def client_common(fun_name, args, vargs, endpoint='libDecel'):
    socket = get_client(endpoint)
    socket.send_pyobj([fun_name, args, vargs])
    print 'client_common -- send function request', fun_name, endpoint
    success, ret = socket.recv_pyobj()
    print 'client_common -- received response'

    if success:
        return ret
    else:
        print 'client_common -- received exception'
        raise Exception(ret)

