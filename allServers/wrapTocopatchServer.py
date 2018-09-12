# coding: utf-8

#
#  Copyright Douglas Williams, 2018
#  All Rights Reserved
#

import numpy as np

from CONFIG import TOCO_ENABLE_EMULATE
from paramsUC import UC_DEFAULT_PARAMS

if TOCO_ENABLE_EMULATE:
    from libTocopatchDevice import HeartyPatch_Emulator as _HeartyPatch_Listener
else:
    from libTocopatchDevice import HeartyPatch_Listener as _HeartyPatch_Listener

from libTocopatchDevice import ping_tocopatch

from libTocopatchSignal import ProcessUC
from libTocopatchSignal import isolateUC       # currently unused


class TocoListener:

    def __init__(self, *args, **kwargs):
        self.processUC = ProcessUC(fs=128, **UC_DEFAULT_PARAMS)
        self.skew = 0
        self.min_samples=128*5

        if 'connection_callback' in kwargs:
            self.connection_callback = kwargs['connection_callback']
            kwargs['connection_callback'] = self.proxy_connection_callback
        else:
            self.connection_callback = None

        if 'update_callback' in kwargs:
            self.update_callback = kwargs['update_callback']
            kwargs['update_callback'] = self.proxy_update_callback
        else:
            self.update_callback = None

        if 'completion_callback' in kwargs:
            self.completion_callback = kwargs['completion_callback']
            kwargs['completion_callback'] = self.proxy_completion_callback
        else:
            self.completion_callback = None

        self.listener = _HeartyPatch_Listener(*args, **kwargs)
        print 'server TocoListener returning from init'


    def proxy_connection_callback(self, *args, **kwargs):
        self.connection_callback(*args, **kwargs)


    def proxy_update_callback(self, *args, **kwargs):
        ret = self.callback_common()
        self.update_callback(ret)


    def proxy_completion_callback(self, ignore, abort=False):
        if abort:
            self.completion_callback(None, abort=abort)
        else:
            ret = self.callback_common()
            self.completion_callback(ret)


    def update_skew(self, skew):
        self.skew = skew


    def go(self):
        return self.listener.go()


    def stop(self, isCancelled=False):
        return self.listener.stop(isCancelled)


    def wait(self):
        return self.listener.wait()


    def get_start_time(self):
        return self.listener.get_start_time()


    def get_sample_rate(self):
        return self.listener.get_sample_rate()


    def getData(self):
        return self.listener.getData()

    def teardown(self):
        pass


    def callback_common(self):
        try:
            sigIn, ts, seqID = self.listener.getData()
            sigIn = np.array(sigIn)
            print 'toco callback', len(sigIn), len(ts), len(seqID), 'sample rate:', self.listener.get_sample_rate()
            self.processUC.updateFS(self.listener.get_sample_rate())

            ts, sigD, sigRel, sigUC, sigAltUC = self.processUC.processData(sigIn, skew=self.skew)
            ret = {'posMin': ts/60.0, 'pos': ts,
                               'filtered': sigRel, 'raw':sigD, 'uc':sigUC, 'alt_uc':sigAltUC}
            return ret
        except Exception:
            print 'Exception -- callback_common'
            return None

