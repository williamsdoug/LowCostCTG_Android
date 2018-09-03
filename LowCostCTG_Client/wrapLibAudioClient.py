
from wrapClientCommon import client_common, get_client

import threading
import sys
import random



XMQ_SUB_POLLER = None
XMQ_SUB_POLLER_MAP = None
XMQ_SUB_POLLER_GENERATION = None


def message_poller(*args, **kwards):
    global XMQ_SUB_POLLER_MAP, XMQ_SUB_POLLER_GENERATION
    context, socket = get_client('libAudioCallbacks')
    while True:
        msg = socket.recv_pyobj()
        tag = msg[0]
        gen = msg[1]
        print 'Incoming message for {}'.format(tag)
        sys.stdout.flush()

        if gen != XMQ_SUB_POLLER_GENERATION:
            print 'message_poller: Stale message -- {}'.format(tag)
            sys.stdout.flush()
        elif XMQ_SUB_POLLER_MAP and tag in XMQ_SUB_POLLER_MAP:
            try:
                XMQ_SUB_POLLER_MAP[tag](*msg[2:])
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

        global XMQ_SUB_POLLER_MAP, XMQ_SUB_POLLER_GENERATION

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
        XMQ_SUB_POLLER_GENERATION = random.randint(1, 2**31)
        XMQ_SUB_POLLER_MAP = {
            'update':self.proxy_update_callback,
            'completion':self.proxy_completion_callback}
        start_message_poller()

        kwargs['XMQ_SUB_POLLER_GENERATION'] = XMQ_SUB_POLLER_GENERATION

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


    def teardown(self):
        global XMQ_SUB_POLLER_MAP, XMQ_SUB_POLLER_GENERATION
        print 'calling teardown'
        XMQ_SUB_POLLER_MAP = None
        XMQ_SUB_POLLER_GENERATION = None

