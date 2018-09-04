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

from libTocopatchSignal import ProcessUC as ProcessUC
from libTocopatchSignal import isolateUC       # currently unused


class TocoListener:

    def __init__(self, *args, **kwargs):
        self.listener = _HeartyPatch_Listener(*args, **kwargs)
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

        self.proxy_listener = _HeartyPatch_Listener(*args, **kwargs)

        print 'server _HeartyPatch_Listener returning from init'


    def proxy_connection_callback(self, *args, **kwargs):
        self.connection_callback(*args, **kwargs)


    def proxy_update_callback(self, *args, **kwargs):
        self.update_callback(*args, **kwargs)
        # ret = self.callback_common(is_update=True)
        # self.update_callback(ret)


    # audio_recording_finished(self, results):
    def proxy_completion_callback(self, *args, **kwargs):
        self.completion_callback(*args, **kwargs)
        # ret = self.callback_common()
        # self.completion_callback(ret)


    def update_skew(self, skew):
        self.skew = skew


    def go(self):
        return self.proxy_listener.go()


    def stop(self, isCancelled=False):
        return self.proxy_listener.stop(isCancelled)


    def wait(self):
        return self.proxy_listener.wait()


    def get_start_time(self):
        return self.proxy_listener.get_start_time()


    def get_sample_rate(self):
        return self.proxy_listener.get_sample_rate()


    def getData(self):
        return self.proxy_listener.getData()

    def teardown(self):
        pass


    def callback_common(self, is_update=False):
        try:
            sigIn, ts, seqID = self.listener.getData()
            sigIn = np.array(sigIn)
            print 'toco callbacl', len(sigIn), len(ts), len(seqID), 'sample rate:', self.listener.get_sample_rate()
            self.processUC.updateFS(self.listener.get_sample_rate())

            ts, sigD, sigRel, sigUC, sigAltUC = self.processUC.processData(sigIn, skew=self.skew)
            ret = {'posMin': ts/60.0, 'pos': ts,
                               'filtered': sigRel, 'raw':sigD, 'uc':sigUC, 'alt_uc':sigAltUC}
            print ret
            return ret
        except Exception:
            print 'Exception -- callback_common'
            return None
        return ret


# class xxProcessUC:
#     def __init__(self, *args, **kwargs):
#
#         self.proxy = ProcessUC(*args, **kwargs)
#
#         print 'server _ProcessUC returning from init'
#
#     def updateFS(self, *args, **kwargs):
#         return self.proxy.updateFS(*args, **kwargs)
#
#     def processData(self, *args, **kwargs):
#         return self.proxy.processData(*args, **kwargs)