import cPickle as pickle
#import pickle
from ZMQ_Again_Exception import ZMQ_Again


from jnius import autoclass
zmq = autoclass('org/zeromq/ZMQ')
Context = autoclass('org.zeromq.ZContext')
Subscriber = autoclass('com.ddw_gd.jeromqfixer.JeromqFixer')


class ZeroMQ:
    REQ = zmq.REQ
    REP = zmq.REP
    PUB = zmq.PUB
    SUB = zmq.SUB

    def __init__(self, address, mode):
        self.context = Context()
        self.socket = self.context.createSocket(mode)

        if mode == self.REQ:
            self.socket.connect(address)
        elif mode == self.REP:
            self.socket.bind(address)
        elif mode == self.PUB:
            self.socket.bind(address)
        elif mode == self.SUB:
            self.socket.connect("tcp://localhost:8888")
            Subscriber.subscribe(self.socket)


    def close(self):
        self.socket.close()
        self.context.destroy()


    def recv_pyobj(self, blocking=True):
        if not blocking:
            msg = self.socket.recvStr(zmq.NOBLOCK)
            if msg is None or len(msg) == 0:
                raise ZMQ_Again
        else:
            msg = self.socket.recvStr()

        if isinstance(msg, unicode):
            msg = str(msg)
        message = pickle.loads(msg)
        return message


    def send_pyobj(self, message):
        msg = pickle.dumps(message)
        self.socket.send(msg)

