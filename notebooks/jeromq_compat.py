#import cPickle as pickle
import pickle

class jmqAgain(Exception):
    pass


ZMQ_NOBLOCK = 1


def recv_pyobj(socket, blocking=True):
    if not blocking:
        msg = socket.recvStr(ZMQ_NOBLOCK)
        if msg is None or len(msg) == 0:
            raise jmqAgain
    else:
        msg = socket.recvStr()
    message = pickle.loads(msg)
    return message


def send_pyobj(socket, message):
    msg = pickle.dumps(message)
    socket.send(msg)

