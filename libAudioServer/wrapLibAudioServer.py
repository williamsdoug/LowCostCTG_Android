#from libAudio import audio_recorder as _audio_recorder
from libAudioEmulate import audio_recorder as _audio_recorder

from libUltrasound import combineExtractionResults
import numpy as np

import sys
import traceback


#
# TODO:
#
# 1) Refactor update_callback:
#    a)  avoid direct reference to extractor
#    b)  return both results
#    c)  integrate combineExtractionResults (libUltrasound  depends on scipy)
#

class audio_recorder:

    def __init__(self, *args, **kwargs):

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

        self.proxy_audio_recorder = _audio_recorder(*args, **kwargs)

        print 'server proxy_audio_recorder returning from init'


    def recording_callback_common(self, results):

        try:
            if 'hr' in results['envelope'] and 'hr' in results['pitch']:
                N = min(len(results['envelope']['hr']), len(results['pitch']['hr']))
                combinedHR, combinedMask = combineExtractionResults(np.array(results['envelope']['hr'][:N]),
                                                                    np.array(results['pitch']['hr'][:N]))
                pos = results['envelope']['pos'][:len(combinedHR)]
                results['combined'] = {'hr': combinedHR, 'valid': combinedMask, 'pos':pos}
            elif 'hr' in results['envelope']:
                results['combined'] = results['envelope']
            else:
                results['combined'] = results['pitch']

        except Exception, e:
            print 'Exception during combineExtractionResults', e

            print '-' * 60
            traceback.print_exc(file=sys.stdout)
            print '-' * 60

        return results


    def proxy_update_callback(self, results):
        results = self.recording_callback_common(results)
        self.update_callback(results)


    # audio_recording_finished(self, results):
    def proxy_completion_callback(self, results):
        results = self.recording_callback_common(results)
        self.completion_callback(results)


    def stop(self, isCancelled=False):
        return self.proxy_audio_recorder.stop(isCancelled)


    def wait(self):
        return self.proxy_audio_recorder.wait()


    def get_start_time(self):
        return self.proxy_audio_recorder.get_start_time()

    def teardown(self):
        pass