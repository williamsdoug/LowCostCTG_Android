# -*- coding: utf-8 -*-

#
#  Copyright Douglas Williams, 2018
#  All Rights Reserved
#

from wrapTocopatchServer import TocoListener, ping_tocopatch

from CONFIG import ZMQ_TOCO_SERVER_ADDRESS_SPEC, ZMQ_TOCO_PUB_ADDRESS_SPEC
import zmq
from threading import Thread

PREFIX = 'libTocopatch__'
XMQ_SUB_POLLER_GENERATION = None
#
# Server Code
#

class TocoServer:

    def __init__(self, rpc_address_spec, server_pub_address_spec):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REP)
        self.socket.bind(rpc_address_spec)
        self.remote_object = None
        self.pub_socket = self.context.socket(zmq.PUB)
        self.pub_socket.bind(server_pub_address_spec)
        self.run = False
        self.t = None

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

    def _server(self):
        global PREFIX, XMQ_SUB_POLLER_GENERATION
        while self.run:
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

    def serve(self):
        """Synchronous Interface"""
        self.run = True
        self._server()

    def start(self):
        """Asynchronous Interface"""
        print 'start'
        self.run = True
        self.t = Thread(target=self._server)
        self.t.start()
        return

    def stop(self, wait=True):
        print 'stop'
        if not self.run or  self.t is None:
            return

        self.run = False
        if wait:
            self.t.join()
        return

    def wait(self):
        print 'wait'
        if not self.run or  self.t is None:
            return

        self.t.join()
        return


def getTocoServer():
     return TocoServer(ZMQ_TOCO_SERVER_ADDRESS_SPEC, ZMQ_TOCO_PUB_ADDRESS_SPEC)
