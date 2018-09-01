#from libAudio import audio_recorder as _audio_recorder
# from libAudioEmulate import audio_recorder as _audio_recorder
from wrapLibAudioServer import audio_recorder as _audio_recorder
from wrapClientCommon import client_common, get_client
import cPickle as pickle
import threading
import sys
#
# Non RPC Debug Versions
#

class dummy_audio_recorder:

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


XMQ_SUB_POLLER = None
XMQ_SUB_POLLER_MAP = None


def message_poller(*args, **kwards):
    global XMQ_SUB_POLLER_MAP
    context, socket = get_client('libAudioCallbacks')
    while True:
        msg = socket.recv_pyobj()
        tag = msg[0]
        print 'Incoming message for {}'.format(tag)
        sys.stdout.flush()

        if tag in XMQ_SUB_POLLER_MAP:
            try:
                XMQ_SUB_POLLER_MAP[tag](*msg[1:])
            except Exception, e:
                print 'Exception -- message_poller -- {}'.format(e)
                sys.stdout.flush()
        else:
            print 'message_poller: Unknown tag -- {}'.format(tag)
            sys.stdout.flush()


def start_message_poller():
    global XMQ_SUB_POLLER
    if XMQ_SUB_POLLER is not None:
        return

    print 'starting backgrount thread'
    XMQ_SUB_POLLER = threading.Thread(target=message_poller)
    XMQ_SUB_POLLER.daemon = True
    XMQ_SUB_POLLER.start()
    print 'callback listener started'




class audio_recorder:

    def __init__(self, *args, **kwargs):

        global XMQ_SUB_POLLER_MAP

        if 'update_callback' in kwargs:
            self.update_callback = kwargs['update_callback']
            kwargs['update_callback'] = None
        else:
            self.update_callback = None

        if 'completion_callback' in kwargs:
            self.completion_callback = kwargs['completion_callback']
            kwargs['completion_callback'] = None
        else:
            self.update_callback = None

        # subscribe to callback messages
        XMQ_SUB_POLLER_MAP = {
            'update':self.proxy_update_callback,
            'completion':self.proxy_completion_callback}
        start_message_poller()

        client_common('audio_recorder__init', args, kwargs, endpoint='libAudio')


    # audio_recording_update(self, extractor_instance, extractor_name, current_pos):
    def proxy_update_callback(self, results):
        self.update_callback(results)


    # audio_recording_finished(self, results):
    def proxy_completion_callback(self, results):
        global XMQ_SUB_POLLER_MAP
        ret = self.completion_callback(results)
        XMQ_SUB_POLLER_MAP = None
        return ret


    def stop(self, isCancelled=False):
        global XMQ_SUB_POLLER_MAP
        ret = client_common('audio_recorder__stop', [isCancelled], {}, endpoint='libAudio')
        if isCancelled:
            XMQ_SUB_POLLER_MAP = None
        return ret


    def wait(self):
        global XMQ_SUB_POLLER_MAP
        client_common('audio_recorder__wait', [], {}, endpoint='libAudio')
        XMQ_SUB_POLLER_MAP = None
        return


    def get_start_time(self):
        return client_common('audio_recorder__get_start_time', [], {}, endpoint='libAudio')
