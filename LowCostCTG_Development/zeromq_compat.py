
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
        self.closed = False

        if mode == self.REQ:
            self.socket.connect(address)
        elif mode == self.REP:
            self.socket.bind(address)
        elif mode == self.PUB:
            self.socket.bind(address)
        elif mode == self.SUB:
            self.socket.connect(address)
            self.socket.setsockopt(zmq.SUBSCRIBE, b"")


    def close(self):
        if not self.closed:
            self.closed = True
            self.socket.close()
            self.context.term()


    def recv_pyobj(self, blocking=True):
        try:
            if not blocking:
                message = self.socket.recv_pyobj(flags=zmq.NOBLOCK)
            else:
                message = self.socket.recv_pyobj()
        except zmq.Again, e:
            raise ZMQ_Again(e)
        return message


    def send_pyobj(self, message):
        self.socket.send_pyobj(message)
