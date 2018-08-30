from libAudio import audio_recorder as _audio_recorder

#
# TODO:
#
# 1) Refactor update_callback:
#    a)  avoid direct reference to extractor
#    b)  return both results
#    c)  integrate combineExtractionResults (libUltrasound  depends on scipy)
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


    def proxy_update_callback(self, *args, **kwargs):
        self.update_callback(*args, **kwargs)


    def proxy_completion_callback(self, *args, **kwargs):
        self.completion_callback(*args, **kwargs)


    def stop(self, isCancelled=False):
        return self.proxy_audio_recorder.stop(isCancelled)


    def wait(self):
        return self.proxy_audio_recorder.wait()


    def get_start_time(self):
        return self.proxy_audio_recorder.get_start_time()
