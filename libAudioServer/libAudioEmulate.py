# coding: utf-8

#
#  Copyright Douglas Williams, 2018
#  All Rights Reserved
#


# Emulate libAudio using existing .wav file recording
# Removes dependency on pyaudio
#
# API compatible with libAudio

EMULATION_RECORDING = 'sample.wav'
#EMULATION_DELAY = 1.0/8       # Normal Speed
#EMULATION_DELAY = 1.0/8/4     # 4x speedup
EMULATION_DELAY = 1.0/8/2     # 4x speedup


#
# Note:  File currently uses pyaudio to read recording file.
#        Alternative is to use scipy.io.wavfile.read(fname)
#        see: self.getSampleData

import threading
import wave
import numpy as np
import scipy
import scipy.signal
import struct
import time
import Queue

from libUltrasound import HibertDataTransformer, ZCTransformer, StaticExtractor
from libQuality import ErrorDetector

from paramsUltrasound import EXTRACTOR_ARGS, HD_TRANSFORMER_ARGS, ZC_TRANSFORMER_ARGS, ERROR_DETECTOR_ARGS

THRESH_FETAL_BRADYCARDIA = 120
THRESH_FETAL_TACHYCARDIA = 160

class audio_recorder:
    enabled = threading.Event()
    stopped = threading.Event()

    def __init__(self, infile, outfile=None,
                 chunk_size=1000, frame_rate=8000, enable_playback=True,
                 update_callback=None,
                 completion_callback=None,
                 audio_in_chan=None, audio_out_chan= None,
                 extractor_params={},
                 tachycardia=THRESH_FETAL_TACHYCARDIA,
                 bradycardia=THRESH_FETAL_BRADYCARDIA,
                 ):

        infile = EMULATION_RECORDING

        # copy params
        self.infile = infile
        self.outfile = outfile
        self.chunk_size = chunk_size
        self.frame_rate = frame_rate
        self.enable_playback = enable_playback
        self.update_callback = update_callback
        self.completion_callback = completion_callback

        self.audio_in_chan = audio_in_chan
        self.audio_out_chan = audio_out_chan

        self.extractor_params = extractor_params
        self.tachycardia = tachycardia
        self.bradycardia = bradycardia

        print 'tachycardia/bradycardia:', self.tachycardia, self.bradycardia
        print 'extractor_params', self.extractor_params

        # other initialization
        self.start_time = None
        self.raw_audio = None
        self.wf_in = None
        self.wf_out = None
        self.p_mic = None
        self.recording_queue = None
        self.stream_mic = None
        self.p_speaker = None
        self.stream_speaker = None
        self.enabled.set()
        self.stopped.clear()
        self.isCancelled = False
        self.thread = threading.Thread(target=self.processRecording)
        self.thread.daemon = True
        self.thread.start()

        print 'audio_recorder returning from init'


    # alternative to using python wave library
    # def getSampleData(self, fname=EMULATION_RECORDING):
    #     from scipy.io import wavfile
    #     self.framerate, self.sample_data = scipy.io.wavfile.read(fname)
    #     self.sample_data_ptr = 0
    #     self.sample_data_len = len(self.sample_data)
    #
    #     print 'Sample data {} -- rate: {}  shape: {}'.format(
    #         fname, self.framerate, self.sample_data.shape)
    #     assert self.framerate == 8000


    def stop(self, isCancelled=False):
        self.isCancelled = isCancelled
        self.enabled.clear()
        print 'called stopped'


    def wait(self):
        print 'called wait'
        self.stopped.wait()


    def get_start_time(self):
        return self.start_time


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
            self.start_time = time.time()
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
        hd = HibertDataTransformer(**HD_TRANSFORMER_ARGS)
        zc = ZCTransformer(**ZC_TRANSFORMER_ARGS)

        hd_err = ErrorDetector(**ERROR_DETECTOR_ARGS)
        zc_err = ErrorDetector(**ERROR_DETECTOR_ARGS)

        extractor = StaticExtractor(transformer=hd, errorDetector=hd_err, name='envelope',
                                    **EXTRACTOR_ARGS)
        zc_extractor = StaticExtractor(transformer=zc, errorDetector=zc_err, name='pitch',
                                       **EXTRACTOR_ARGS)

        self.open_audio_input()

        # Loop through audio data
        segment = self.get_audio_data()                                # prime the pump
        while self.enabled.is_set() and len(segment) > 0:
            # Process data through Hilbert Transformer
            prior_count = extractor.get_results_count()
            sigD = scipy.signal.decimate(segment, 8, zero_phase=True)  # Downsample to 1K samples/second
            hd.addData(sigD)                                           # compute envelope using hilbert
            extractor.extract_incremental()                            # now compute instantaneous HR
            delta_hd = extractor.get_results_count() - prior_count

            # Process data through ZC transformer
            prior_count = zc_extractor.get_results_count()
            zc.addData(segment)                                         # compute pitch
            zc_extractor.extract_incremental()                          # now compute instantaneous HR
            delta_zc =  zc_extractor.get_results_count() - prior_count

            # perform callback if new data
            if self.update_callback and delta_hd > 0 or delta_zc > 0:
                if extractor.get_results_count() == zc_extractor.get_results_count():
                    results = {'envelope': extractor.get_results(),
                               'pitch': zc_extractor.get_results()}
                    self.update_callback(results)

            # Get Next Data
            if not self.enabled.is_set():
                print 'breaking'
                break
            segment = self.get_audio_data()                            # get data for next iteration

        # cleanup stuff.
        if not self.isCancelled:
            results = {'envelope':extractor.get_results(),
                       'pitch':zc_extractor.get_results()}
            if self.completion_callback is not None:
                self.completion_callback(results)
        self.stopped.set()
        print 'subprocess finished'
        return

