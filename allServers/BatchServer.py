# -*- coding: utf-8 -*-

#
#  Copyright Douglas Williams, 2018
#  All Rights Reserved
#

from libDecel import extractAllDecels, summarizeDecels
from paramsDecel import FEATURE_EXTRACT_PARAMS
from libUC import findUC

from zeromq_compat import ZeroMQ, ZMQ_Again
from threading import Thread
import time

#
# Server Code
#
from CONFIG import ZMQ_BATCH_SERVER_ADDRESS_SPEC
SERVED_FUNCTIONS = {
    'summarizeDecels':summarizeDecels,
    'extractAllDecels':extractAllDecels,
    'findUC':findUC,
}


class BatchServer:

    def __init__(self, rpc_address_spec):
        self.socket = ZeroMQ(rpc_address_spec, ZeroMQ.REP)
        self.run = False
        self.t = None

    def _server(self):
        global SERVED_FUNCTIONS
        while self.run:
            try:
                fun_name, args, kwargs = self.socket.recv_pyobj(blocking=False)
            except ZMQ_Again:
                time.sleep(0.05)
                continue
            print 'wrapLibDecel server -- received {}'.format(fun_name)

            if fun_name == 'exit':
                # terminate gracefully
                self.socket.send_pyobj([True, 'byebye'])
                self.run = False

            elif fun_name in SERVED_FUNCTIONS:
                # special case handling for
                if fun_name == 'extractAllDecels':
                    kwargs['allExtractorParams'] = FEATURE_EXTRACT_PARAMS

                # execute function call locally
                try:
                    ret = SERVED_FUNCTIONS[fun_name](*args, **kwargs)

                    print 'wrapLibDecel server -- returning response'
                    self.socket.send_pyobj([True, ret])
                except Exception, e:
                    print 'wrapLibDecel server -- returning exception {}'.format(e)
                    self.socket.send_pyobj([False, e])
            else:
                # unknown function
                msg = 'wrapLibDecel server -- Unknown function {}'.format(fun_name)
                print msg
                self.socket.send_pyobj([False, msg])

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


    def wait(self):
        print 'wait'
        if not self.run or  self.t is None:
            return

        self.t.join()
        return


def getBatchServer():
     return BatchServer(ZMQ_BATCH_SERVER_ADDRESS_SPEC)
