import cPickle as pickle
#import pickle

import zmq
ZMQ_NOBLOCK = zmq.NOBLOCK


def recv_pyobj(socket, blocking=True):
    if not blocking:
        msg = socket.recv_string(flags=ZMQ_NOBLOCK)
    else:
        msg = socket.recv_string()

    if isinstance(msg, unicode):
        # msg.encode('utf-8')
        msg = str(msg)
    message = pickle.loads(msg)
    return message


def send_pyobj(socket, message):
    msg = pickle.dumps(message)
    socket.send_string(msg)
