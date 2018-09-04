# coding: utf-8

#
#  Copyright Douglas Williams, 2018
#  All Rights Reserved
#

from wrapLibAudioServer import audio_recorder as _audio_recorder
from libUltrasound import combineExtractionResults

#
# Non RPC Debug Versions
#

class audio_recorder:

    def __init__(self, *args,
                 **kwargs
                 ):

        if 'update_callback' in kwargs:
            self.update_callback = kwargs['update_callback']
            kwargs['update_callback'] = self.proxy_update_callback
        else:
            self.update_callback = None

        if 'completion_callback' in kwargs:
            self.completion_callback = kwargs['completion_callback']
            kwargs['completion_callback'] = self.proxy_completion_callback
        else:
            self.update_callback = None

        self.proxy_audio_recorder = _audio_recorder(*args, **kwargs)


    # audio_recording_update(self, extractor_instance, extractor_name, current_pos):
    def proxy_update_callback(self, results):
        self.update_callback(results)

    # audio_recording_finished(self, results):
    def proxy_completion_callback(self, results):
        self.completion_callback(results)


    def stop(self, isCancelled=False):
        return self.proxy_audio_recorder.stop(isCancelled)


    def wait(self):
        return self.proxy_audio_recorder.wait()


    def get_start_time(self):
        return self.proxy_audio_recorder.get_start_time()


    def teardown(self):
        pass
