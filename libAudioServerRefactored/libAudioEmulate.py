# coding: utf-8

#
#  Copyright Douglas Williams, 2018
#  All Rights Reserved
#


# Emulate libAudio using existing .wav file recording
# Removes dependency on pyaudio
#
# API compatible with libAudio

from CONFIG import EMULATION_RECORDING, EMULATION_DELAY


#
# Note:  File currently uses pyaudio to read recording file.
#        Alternative is to use scipy.io.wavfile.read(fname)
#        see: self.getSampleData

import threading
import wave
import numpy as np
import time
from libAudioSupport import AudioSupport

class audio_recorder:
    enabled = threading.Event()
    stopped = threading.Event()

    def __init__(self, infile, outfile=None,
                 chunk_size=1000, frame_rate=8000, enable_playback=True,
                 update_callback=None,
                 completion_callback=None,
                 audio_in_chan=None, audio_out_chan= None, **kwargs
                 ):

        infile = EMULATION_RECORDING

        # copy params
        self.infile = infile
        self.outfile = outfile
        self.chunk_size = chunk_size
        self.frame_rate = frame_rate
        self.enable_playback = enable_playback

        self.audio_in_chan = audio_in_chan
        self.audio_out_chan = audio_out_chan


        # audio initialization
        self.raw_audio = None
        self.wf_in = None
        self.wf_out = None
        self.p_mic = None
        self.stream_mic = None
        self.p_speaker = None
        self.stream_speaker = None


        # Signal Processing Code
        self.audioSupport = AudioSupport(update_callback=update_callback,
                                         completion_callback=completion_callback)
        # Threading related code
        self.enabled.set()
        self.stopped.clear()
        self.isCancelled = False
        self.thread = threading.Thread(target=self.processRecording)
        self.thread.daemon = True
        self.thread.start()

        print 'audio_recorder returning from init'


    def stop(self, isCancelled=False):
        self.isCancelled = isCancelled
        self.enabled.clear()
        print 'called stopped'


    def wait(self):
        print 'called wait'
        self.stopped.wait()


    def get_start_time(self):
        return self.audioSupport.get_start_time()


    def open_audio_input(self):
        """open audio input source"""
        if self.infile is not None:
            self.wf_in = wave.open(self.infile, 'rb')
            self.channels = self.wf_in.getnchannels()
            self.sampwidth = self.wf_in.getsampwidth()
            self.framerate = self.wf_in.getframerate()    # get actual frame rate

            self.scaled_chunk_size = self.chunk_size * self.channels

            print 'Sample Width: {}   Framerate: {}  Channels: {}'.format(
                self.sampwidth, self.framerate, self.channels)

            assert self.framerate == 8000
            # TODO:  Add code for framerates other than 8000   frame_rate_actual


    def get_audio_data(self):
        """Get data from audio input source"""
        if self.infile is not None:
            data = self.wf_in.readframes(self.scaled_chunk_size)
            segment = np.fromstring(data, '<h')
            if self.channels > 1:
                segment = segment[::self.channels]
                self.raw_audio = None
            else:
                self.raw_audio = data

            if self.infile == EMULATION_RECORDING:
                time.sleep(EMULATION_DELAY)

            return segment


    def processRecording(self):
        """Process individual recording, either from microphone or from file"""
        print 'subprocess started'
        self.open_audio_input()

        # Loop through audio data
        segment = self.get_audio_data()                                # prime the pump
        self.audioSupport.set_start_time()
        while self.enabled.is_set() and len(segment) > 0:
            self.audioSupport.process_segment(segment)

            # Get Next Data
            if not self.enabled.is_set():
                print 'breaking'
                break
            segment = self.get_audio_data()                            # get data for next iteration

        # cleanup stuff.
        if not self.isCancelled:
            self.audioSupport.finish_processing()
        self.stopped.set()
        print 'subprocess finished'
        return
