# coding: utf-8

#
#  Copyright Douglas Williams, 2018
#  All Rights Reserved
#

# Developer feature:  Support emulation using existing .wav file recording
from CONFIG import ENABLE_EMULATE, EMULATION_RECORDING, EMULATION_DELAY


import threading
try:
    import pyaudio
except Exception, e:
    print e
import wave
import numpy as np
import struct
import time
import Queue

from libAudioSupport import AudioSupport

class audio_recorder:
    enabled = threading.Event()
    stopped = threading.Event()

    def __init__(self, infile, outfile=None,
                 chunk_size=1000, frame_rate=8000, enable_playback=True,
                 update_callback=None,
                 completion_callback=None,
                 audio_in_chan=None, audio_out_chan= None):

        if ENABLE_EMULATE:
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
        self.recording_queue = None
        self.enabled.set()
        self.stopped.clear()
        self.isCancelled = False
        self.thread = threading.Thread(target=self.processRecording)
        self.thread.daemon = True
        self.thread.start()


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

            p_temp = pyaudio.PyAudio()
            self.format = p_temp.get_format_from_width(self.sampwidth)
            p_temp.terminate()
            #p_temp.close()

            self.scaled_chunk_size = self.chunk_size * self.channels

            print 'Sample Width: {} Format: {}  Framerate: {}  Channels: {}'.format(
                self.sampwidth,self.format,self.framerate, self.channels)

            assert self.framerate == 8000
            # TODO:  Add code for framerates other than 8000   frame_rate_actual
        else:
            self.recording_queue = Queue.Queue()
            self.p_mic = pyaudio.PyAudio()

            self.stream_mic =  self.p_mic.open(format=pyaudio.paInt16,
                                               channels=1, rate=self.frame_rate, input=True,
                                               frames_per_buffer=self.chunk_size,
                                               input_device_index=self.audio_in_chan,
                                               stream_callback=self.recording_callback)
            self.stream_mic.start_stream()



    def recording_callback(self, in_data, frame_count, time_info, status):
        self.recording_queue.put(in_data)
        if status != 0:
            print '** recording error', status, time_info
        #return (None, pyaudio.paContinue if q.qsize() < 40 else pyaudio.paComplete)
        return (None, pyaudio.paContinue)


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
        else:
            #data = self.stream_mic.read(self.chunk_size)
            while self.stream_mic.is_active() and self.recording_queue.qsize() == 0:
                time.sleep(0.1)
            if self.recording_queue.qsize() > 0:
                data = self.recording_queue.get()
                self.raw_audio = data
                segment = np.fromstring(data, '<h')
                return segment
            else:
                self.raw_audio = None
                return []


    def close_audio_input(self):
        """close audio input source"""
        if self.infile is not None:
            self.wf_in.close()
        else:
            self.stream_mic.stop_stream()
            self.stream_mic.close()
            self.p_mic.terminate()


    def open_output(self):
        # open stream based on the wave object which has been input.
        if self.enable_playback:
            self.p_speaker = pyaudio.PyAudio()
            try:  # hack
                self.stream_speaker = self.p_speaker.open(format=self.format, channels=1,
                                                          output_device_index=self.audio_out_chan,
                                                          rate=self.framerate, output=True)
            except Exception:
                self.stream_speaker = self.p_speaker.open(format=pyaudio.paInt16, channels=1,
                                                          output_device_index=self.audio_out_chan,
                                                          rate=8000, output=True)
        if self.outfile is not None:
            self.wf_out = wave.open(self.outfile, 'wb')
            self.wf_out.setnchannels(1)

            p_temp = pyaudio.PyAudio()
            self.wf_out.setsampwidth(p_temp.get_sample_size(pyaudio.paInt16))
            p_temp.terminate()
            #p_temp.close()

            self.wf_out.setframerate(self.frame_rate)
            pass


    def output_data(self, segment):
        if not self.enable_playback and self.outfile is None:
            return

        if self.raw_audio:     # try to use existing raw format data, if available
            data = self.raw_audio
        else:                  # otherwise convert to packed short int array format
            data = ''.join([struct.pack('<h', x) for x in segment.tolist()])

        if self.enable_playback:
            self.stream_speaker.write(data)

        if self.outfile is not  None:
            self.wf_out.writeframes(data)


    def close_output(self):
        if self.enable_playback:
            self.stream_speaker.close()
            self.p_speaker.terminate()

        if self.outfile is not None:
            self.wf_out.close()


    def processRecording(self):
        """Process individual recording, either from microphone or from file"""
        print 'subprocess started'
        self.open_audio_input()
        self.open_output()

        # Loop through audio data
        segment = self.get_audio_data()                                # prime the pump
        self.audioSupport.set_start_time()
        while self.enabled.is_set() and len(segment) > 0:
            self.audioSupport.process_segment(segment)
            self.output_data(segment)

            # Get Next Data
            if not self.enabled.is_set():
                print 'breaking'
                break
            segment = self.get_audio_data()                            # get data for next iteration

        # cleanup stuff.
        self.close_audio_input()
        self.close_output()
        if not self.isCancelled:
            self.audioSupport.finish_processing()
        self.stopped.set()
        print 'subprocess finished'
        return

