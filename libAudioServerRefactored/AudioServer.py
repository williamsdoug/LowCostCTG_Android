# -*- coding: utf-8 -*-

#
#  Copyright Douglas Williams, 2018
#  All Rights Reserved
#

from wrapLibAudioServer import audio_recorder
from libUltrasound import combineExtractionResults

from zeromq_compat import ZeroMQ, ZMQ_Again
from threading import Thread
import time

from CONFIG import ZMQ_AUDIO_SERVER_ADDRESS_SPEC, ZMQ_AUDIO_PUB_ADDRESS_SPEC
PREFIX = 'audio_recorder__'
XMQ_SUB_POLLER_GENERATION = None
#
# Server Code
#

class AudioServer:

    def __init__(self, rpc_address_spec, server_pub_address_spec):
        self.socket = ZeroMQ(rpc_address_spec, ZeroMQ.REP)
        self.remote_object = None
        self.pub_socket = ZeroMQ(server_pub_address_spec, ZeroMQ.PUB)
        self.run = False
        self.t = None

    def report_unknown(self, fun_name):
        msg = 'audio_recorder server -- Unknown function {}'.format(fun_name)
        print msg
        self.socket.send_pyobj([False, msg])

    # Convert callbacks to pub/sub message
    def update_callback(self, result):
        global XMQ_SUB_POLLER_GENERATION
        self.pub_socket.send_pyobj(('update', XMQ_SUB_POLLER_GENERATION, result))

    def completion_callback(self, result):
        global XMQ_SUB_POLLER_GENERATION
        self.pub_socket.send_pyobj(('completion', XMQ_SUB_POLLER_GENERATION, result))

    def _server(self):
        global PREFIX, XMQ_SUB_POLLER_GENERATION
        while self.run:
            try:
                fun_name, args, kwargs = self.socket.recv_pyobj(blocking=False)
            except ZMQ_Again:
                time.sleep(0.05)
                continue
            print 'audio_recorder server -- received {}'.format(fun_name)

            if fun_name == 'exit':
                # terminate gracefully
                self.socket.send_pyobj([True, 'byebye'])
                return
            elif fun_name == 'combineExtractionResults':
                try:
                    ret = combineExtractionResults(*args, **kwargs)
                    self.socket.send_pyobj([True, ret])
                except Exception, e:
                    print 'audio_recorder server -- combineExtractionResults exception {}'.format(e)
                    self.socket.send_pyobj([False, e])
            # process RPC called related to audio_recorder object
            elif not fun_name.startswith(PREFIX):
                self.report_unknown(fun_name)
            elif fun_name.endswith('__init'):
                # Create remote object
                XMQ_SUB_POLLER_GENERATION = kwargs['XMQ_SUB_POLLER_GENERATION']
                del kwargs['XMQ_SUB_POLLER_GENERATION']

                kwargs['update_callback'] = self.update_callback
                kwargs['completion_callback'] = self.completion_callback

                self.remote_object = audio_recorder(*args, **kwargs)
                self.socket.send_pyobj([True, 'initialized'])
            else:
                # invoke method on remote object
                method_name = fun_name[len(PREFIX):]
                try:
                    fun = getattr(self.remote_object, method_name)
                    ret = fun(*args, **kwargs)
                    print 'audio_recorder server -- returning response'
                    self.socket.send_pyobj([True, ret])
                except AttributeError:
                    self.report_unknown(fun_name)
                except Exception, e:
                    print 'audio_recorder server -- returning exception {}'.format(e)
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
        if self.run and  self.t is not None:
            self.run = False
            if wait:
                self.t.join()
        if self.socket and not self.socket.closed:
            self.socket.close()
        if self.pub_socket and not self.pub_socket.closed:
            self.pub_socket.close()


    def wait(self):
        print 'wait'
        if not self.run or  self.t is None:
            return

        self.t.join()
        return


def getAudioServer():
     return AudioServer(ZMQ_AUDIO_SERVER_ADDRESS_SPEC, ZMQ_AUDIO_PUB_ADDRESS_SPEC)
