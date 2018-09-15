import cPickle as pickle
#import pickle

import zmq
from ZMQ_Again_Exception import ZMQ_Again


class ZeroMQ:
    REQ = zmq.REQ
    REP = zmq.REP
    PUB = zmq.PUB
    SUB = zmq.SUB

    def __init__(self, address, mode):
        self.context = zmq.Context()
        self.socket = self.context.socket(mode)

        if mode == self.REQ:
            self.socket.connect(address)
        elif mode == self.REP:
            self.socket.bind(address)
        elif mode == self.PUB:
            self.socket.bind(address)
        elif mode == self.SUB:
            self.socket.connect("tcp://localhost:8888")
            self.socket.setsockopt(zmq.SUBSCRIBE, b"")


    def close(self):
        self.socket.close()
        self.context.term()


    def recv_pyobj(self, blocking=True):
        try:
            if not blocking:
                msg = self.socket.recv_string(flags=zmq.NOBLOCK)
            else:
                msg = self.socket.recv_string()
        except zmq.Again, e:
            raise ZMQ_Again(e)

        if isinstance(msg, unicode):
            msg = str(msg)
        message = pickle.loads(msg)
        return message


    def send_pyobj(self, message):
        msg = pickle.dumps(message)
        self.socket.send_string(msg)
