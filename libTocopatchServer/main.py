# -*- coding: utf-8 -*-

#
#  Copyright Douglas Williams, 2018
#  All Rights Reserved
#

from wrapTocopatchServer import TocoListener, ping_tocopatch

import zmq

from CONFIG import ZMQ_SERVER_ADDRESS_SPEC, ZMQ_PUB_ADDRESS_SPEC

PREFIX = 'libTocopatch__'
XMQ_SUB_POLLER_GENERATION = None
#
# Server Code
#

class Server:

    def __init__(self):
        global  ZMQ_SERVER_ADDRESS_SPEC, ZMQ_PUB_ADDRESS_SPEC
        print  ZMQ_SERVER_ADDRESS_SPEC, ZMQ_PUB_ADDRESS_SPEC

        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REP)
        self.socket.bind(ZMQ_SERVER_ADDRESS_SPEC)
        self.remote_object = None

        self.pub_socket = self.context.socket(zmq.PUB)
        self.pub_socket.bind(ZMQ_PUB_ADDRESS_SPEC)


    def report_unknown(self, fun_name):
        msg = 'audio_recorder server -- Unknown function {}'.format(fun_name)
        print msg
        self.socket.send_pyobj([False, msg])


    # Convert callbacks to pub/sub message
    def connection_callback(self, *args, **kwargs):
        global XMQ_SUB_POLLER_GENERATION
        self.pub_socket.send_pyobj(('connection', XMQ_SUB_POLLER_GENERATION, args, kwargs))

    def update_callback(self, result):
        global XMQ_SUB_POLLER_GENERATION
        self.pub_socket.send_pyobj(('update', XMQ_SUB_POLLER_GENERATION, result))


    def completion_callback(self, result):
        global XMQ_SUB_POLLER_GENERATION
        self.pub_socket.send_pyobj(('completion', XMQ_SUB_POLLER_GENERATION, result))


    def serve(self):
        global PREFIX, XMQ_SUB_POLLER_GENERATION
        while True:
            fun_name, args, kwargs = self.socket.recv_pyobj()
            print 'TocoListener server -- received {}'.format(fun_name)

            if fun_name == 'exit':
                # terminate gracefully
                self.socket.send_pyobj([True, 'byebye'])
                return
            elif fun_name == '__ping_tocopatch':
                try:
                    ret = ping_tocopatch(*args, **kwargs)
                    self.socket.send_pyobj([True, ret])
                except Exception, e:
                    print 'TocoListener server -- ping_tocopatch returned exception {}'.format(e)
                    self.socket.send_pyobj([False, e])

            elif not fun_name.startswith(PREFIX):
                self.report_unknown(fun_name)
            elif fun_name.endswith('__init'):
                # Create remote object
                XMQ_SUB_POLLER_GENERATION = kwargs['XMQ_SUB_POLLER_GENERATION']
                del kwargs['XMQ_SUB_POLLER_GENERATION']

                kwargs['connection_callback'] = self.connection_callback
                kwargs['update_callback'] = self.update_callback
                kwargs['completion_callback'] = self.completion_callback

                self.remote_object = TocoListener(*args, **kwargs)
                self.socket.send_pyobj([True, 'initialized'])
            else:
                # invoke method on remote object
                method_name = fun_name[len(PREFIX):]
                try:
                    fun = getattr(self.remote_object, method_name)
                    ret = fun(*args, **kwargs)
                    print 'TocoListener server -- returning response'
                    self.socket.send_pyobj([True, ret])
                except AttributeError:
                    self.report_unknown(fun_name)
                except Exception, e:
                    print 'TocoListener server -- returning exception {}'.format(e)
                    self.socket.send_pyobj([False, e])



# If called at top level, start server
if __name__ == '__main__':
    Server().serve()