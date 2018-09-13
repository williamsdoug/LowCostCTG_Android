# coding: utf-8

#
#  Copyright Douglas Williams, 2018
#  All Rights Reserved
#


import numpy as np
import scipy
import scipy.signal
import time

from libUltrasound import HibertDataTransformer, ZCTransformer, StaticExtractor
from libQuality import ErrorDetector

from paramsUltrasound import EXTRACTOR_ARGS, HD_TRANSFORMER_ARGS, ZC_TRANSFORMER_ARGS, ERROR_DETECTOR_ARGS


class AudioSupport:
    def __init__(self, update_callback=None, completion_callback=None):

        # copy params
        self.update_callback = update_callback
        self.completion_callback = completion_callback

        # initialize signal processsing objects
        self.hd = HibertDataTransformer(**HD_TRANSFORMER_ARGS)
        self.zc = ZCTransformer(**ZC_TRANSFORMER_ARGS)
        hd_err = ErrorDetector(**ERROR_DETECTOR_ARGS)
        zc_err = ErrorDetector(**ERROR_DETECTOR_ARGS)

        self.extractor = StaticExtractor(transformer=self.hd, errorDetector=hd_err, name='envelope',
                                         **EXTRACTOR_ARGS)
        self.zc_extractor = StaticExtractor(transformer=self.zc, errorDetector=zc_err, name='pitch',
                                            **EXTRACTOR_ARGS)
        # other initialization
        self.start_time = time.time()


    def set_start_time(self, val=None):
        if val is not None:
            self.start_time = val
        else:
            self.start_time = time.time()


    def get_start_time(self):
        return self.start_time


    def process_segment(self, segment):
        # Process data through Hilbert Transformer
        prior_count = self.extractor.get_results_count()
        sigD = scipy.signal.decimate(segment, 8, zero_phase=True)  # Downsample to 1K samples/second
        self.hd.addData(sigD)                                           # compute envelope using hilbert
        self.extractor.extract_incremental()                            # now compute instantaneous HR
        delta_hd = self.extractor.get_results_count() - prior_count

        # Process data through ZC transformer
        prior_count = self.zc_extractor.get_results_count()
        self.zc.addData(segment)                                         # compute pitch
        self.zc_extractor.extract_incremental()                          # now compute instantaneous HR
        delta_zc =  self.zc_extractor.get_results_count() - prior_count

        # perform callback if new data
        if self.update_callback and delta_hd > 0 or delta_zc > 0:
            if self.extractor.get_results_count() == self.zc_extractor.get_results_count():
                results = {'envelope': self.extractor.get_results(),
                           'pitch': self.zc_extractor.get_results()}
                self.update_callback(results)


    def finish_processing(self):
        results = {'envelope':self.extractor.get_results(),
                   'pitch':self.zc_extractor.get_results()}
        if self.completion_callback is not None:
            self.completion_callback(results)
