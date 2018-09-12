# coding: utf-8

#
#  Copyright Douglas Williams, 2018
#  All Rights Reserved
#

# # Instantaneous HR Extraction from 8K Recording
#
#  Note:  Code performs time.sleep(0) ahead of each autocorrelation in order to ensure realtime responsiveness
# 
# Example recording using PyAudio Library
# 
# source: http://people.csail.mit.edu/hubert/pyaudio/
#         
# Installation:
# - OSX:
#   - brew install portaudio 
#   - pip install pyaudio
# - Windows:
#   - python -m pip install pyaudio

import numpy as np
import scipy
import scipy.signal
import copy

NoneType = type(None)



def derivFilter(sig, dthresh=10, maxFHR=200, showStats=False):
    """Filter out signal points with high derivitive"""
    mask = np.logical_and(sig > 0, sig < maxFHR)

    deriv = np.diff(sig)
    dMask = np.logical_and(mask[:-1], mask[1:])  # ignore deriv for invalid samples
    dMask = np.logical_and(dMask, np.abs(deriv) < dthresh)  # discard excessive deriv

    # recompute mask keeping only points with at least one normal deriv
    newMask = np.logical_or(np.pad(dMask, (1, 0), 'constant', constant_values=0),
                            np.pad(dMask, (0, 1), 'constant', constant_values=0))
    newMask = np.logical_and(mask, newMask)

    if showStats:
        mad = np.median(np.abs(deriv[dMask]))
        pctValid = np.mean(newMask)
        print 'pctValid: {:0.2f}%.  MAD: {:0.2f}'.format(pctValid * 100.0, mad)

    return newMask


def combineExtractionResults(sig1, sig2, **kwargs):
    """Combines two signals"""

    mask1 = derivFilter(sig1, **kwargs)
    mask2 = derivFilter(sig2, **kwargs)
    pctValid1 = np.mean(sig1)
    pctValid2 = np.mean(sig2)

    if pctValid1 >= pctValid2:
        sigOrig = sig1
        maskOrig = mask1
        sig = np.copy(sig1)
        mask = np.copy(mask1)
        sigOther = sig2
        maskOther = mask2
    else:
        sigOrig = sig2
        maskOrig = mask2
        sig = np.copy(sig2)
        mask = np.copy(mask2)
        sigOther = sig1
        maskOther = mask1

    subset = np.logical_and(~mask, maskOther)
    mask = np.logical_or(mask, subset)
    sig[subset] = sigOther[subset]
    sig[~mask] = 0

    maskFinal = derivFilter(sig, **kwargs)
    return sig, maskFinal


class SignalTransformer:
    # Abstract class for RMSTransformer, ZCTransformer and HilbertDataTransformer

    def __init__(self, ms_per_sample=1):
        self.ms_per_sample = ms_per_sample   # Used by consuming extractor classes
        self.rawData = np.array([])
        self.xformData = np.array([])

    def addData(self, newData):
        self.rawData = np.append(self.rawData, newData)

    def getSegment(self, idx, width):
        """Gets segment of transformed data.  Perform lazy transformation if needed
        Params:
            idx   - starting offset of data segment in samples
            width - width of segment in samples
        """

        if (idx + width) > len(self.xformData):  # insufficient data to satisfy request
            self._transform()

        if idx + width > len(self.xformData):
            return None

        x = self.xformData[idx:idx + width]
        return self._postprocessSegment(x)

    def _postprocessSegment(self, x):
        #override with extractor-specific post processing
        return x

    def _transform(self):
        # override with extractor-specific post processing
        raise Exception('abstract method _transformSegment not implemented')

    def getAll(self):
        self._transform()
        return self.xformData



class RMSTransformer(SignalTransformer):
    """Object used to transform audio signal to extract signal envelope based on RMS energy
    """

    def __init__(self, lpfAC=None, hpfAC=None, orderAC=7, lpfDC=None, hpfDC=None, orderDC=7, downsample=8,
                 normalize=True, samplerate=8000):
        """Initialization

        Parameters:
            lpfAC, hpfAC, orderAC - bandpass filter params prior to rms stage
            lpfDC, hpfDC, orderDC -  bandpass filter params after rms stage
            downsample - downsample factor.  If input is 8K sps, use 8 for 1K output sps
            normalize - clip, tage sqrt and recenter signal around menan
        """

        SignalTransformer.__init__(self)

        downsample = 8
        self.downsample = downsample
        self.normalize = normalize
        fNyquist = samplerate / 2.0

        if hpfAC and lpfAC:
            self.filtAC = scipy.signal.butter(orderAC, (hpfAC / fNyquist, lpfAC / fNyquist), btype='bandpass')
        elif hpfAC:
            self.filtAC = scipy.signal.butter(orderAC, hpfAC / fNyquist, btype='highpass')
        elif lpfAC:
            self.filtAC = scipy.signal.butter(orderAC, lpfAC / fNyquist, btype='lowpass')
        else:
            raise Exception('missing AC filter params')
        self.ziAC = scipy.signal.lfilter_zi(*self.filtAC)

        if hpfDC and lpfDC:
            self.filtDC = scipy.signal.butter(orderDC, (hpfDC / fNyquist, lpfDC / fNyquist), btype='bandpass')
        elif hpfDC:
            self.filtDC = scipy.signal.butter(orderDC, hpfDC / fNyquist, btype='highpass')
        elif lpfDC:
            self.filtDC = scipy.signal.butter(orderDC, lpfDC / fNyquist, btype='lowpass')
        else:
            raise Exception('missing DC filter params')
        self.ziDC = scipy.signal.lfilter_zi(*self.filtDC)

        fNyquist = samplerate / 2.0
        fNyquistD = fNyquist / downsample


    def addData(self, newData):
        self.rawData = np.append(self.rawData, newData)


    def _postprocessSegment(self, x):
        if self.normalize:
            t = np.percentile(x, 90)
            x[x > t] = t
            x = x - np.percentile(x, 10)
            x[x < 0] = 0
            x = x ** 0.5
            x = x - np.mean(x)

        return x


    def _transform(self):
        """Internal function to apply Hilbert transform and smoothing to segment of data"""

        # select data as multiple of downsample
        N = (len(self.rawData) // self.downsample) * self.downsample
        if N == 0:
            return
        sig = self.rawData[:N]

        sig, self.ziAC = scipy.signal.lfilter(self.filtAC[0], self.filtAC[1], sig, zi=self.ziAC)
        sig = sig ** 2  # rectify
        sig, self.ziDC = scipy.signal.lfilter(self.filtDC[0], self.filtDC[1], sig, zi=self.ziDC)
        sig = sig[::self.downsample]  # downsample

        self.xformData = np.append(self.xformData, sig)
        self.rawData = self.rawData[N:]  # discard processed data


class ZCTransformer(SignalTransformer):
    """Object used to transform audio signal to extract pitch using zero crossing rate
    """

    def __init__(self, zc_interval=320, downsample=16, # downsample=8,
                 raw_samples_per_ms=8,
                 useLog=False, normalize=True, useReciprocal=True,
                 clip=False, clipUpperPct=80, clipLowerPct=20):
        """Initialization

        Parameters:
            zc_interval - sample period for XC measurement
            downsample - dopwnsample factor.  If input is 8K sps, use 8 for 1K output sps
            raw_samples_per_ms - input sample rate normalized to 1K sps
            useLog - apply log to output
            normalize - recenter output around mean
            useReciprocal - return return 1/zc rate
            useClip - apply clipping to output
            clipUpperPct = upper threshold for clipping
            clipLowerPct = lower threshold for clipping
        """
        SignalTransformer.__init__(self)

        # save config parameters
        self.zc_interval = zc_interval
        self.downsample = downsample
        self.zc_interval_in_samples = zc_interval / downsample
        self.ms_per_sample = downsample / raw_samples_per_ms

        self.useLog = useLog
        self.clip = clip
        self.clipUpperPct = clipUpperPct
        self.clipLowerPct = clipLowerPct
        self.normalize = normalize
        self.useReciprocal = useReciprocal
        self.hann = scipy.signal.hann(zc_interval)

        # create reuseable window function
        self.hann = scipy.signal.hann(self.zc_interval_in_samples)


    def _postprocessSegment(self, x):

        if self.useLog:
            x = np.log(x)

        if self.clip:
            u = np.percentile(x, self.clipUpperPct)
            l = np.percentile(x, self.clipLowerPct)
            x[x > u] = u
            x[x < l] = l

        if self.normalize:
            if self.clip:
                x = x - (u + l) / 2.0
            else:
                x = x - np.mean(x)

        return x


    def _transform(self):
        """Internal function to apply Hilbert transform and smoothing to segment of data"""
        if len(self.rawData) <= self.zc_interval:
            return

        # find zero prossings (rising edge)
        zc = np.logical_and(self.rawData[:-1] < 0, self.rawData[1:] >= 0)

        # compute aggregated zero crossings
        M = len(zc) // self.downsample
        N = M * self.downsample
        zc = zc[:N]    # Align bitmask
        zc = zc.reshape((M, self.downsample))
        zc = np.sum(zc, axis=1)

        # compute rate over interval
        zcr = np.array([np.sum(zc[i:i + self.zc_interval_in_samples] * self.hann)
                        for i in range(0, len(zc) - self.zc_interval_in_samples)])
        zcr[zcr < 1] = 1
        if self.useReciprocal:
            self.xformData = np.append(self.xformData, 1.0 / zcr)
        else:
            self.xformData = np.append(self.xformData, zcr)

        N = len(zcr) * self.downsample  # discard processed raw data
        self.rawData = self.rawData[N:]


class HibertDataTransformer(SignalTransformer):
    """Object used to transform audio signal to extract envelope of
    AC modulated signal using using Hilbert Transform, with output
    smoothing.

    Applies Hilbert Transform incremental, and is modeled for use in phone
    application where rawData is replaced by decimated output from
    microphone.  Overlapping Hilbert transforms used to minimized discontinuities at
    segment boundaries.  While minimial discontinuities in magnitude, this approach
    is insufficient for any analysis of instantaneous frequencies using
    imaginary components of Hilbert transform.

    Note:  Implementation is hard coded to assuming roughly 1K sampling rate
           (44x decimation of input signal for 44100 rate signal)

    """

    def __init__(self, nFFT=2 ** 8, overlapFactor=8, smoothingWidth=13, ms_per_sample=2):
        """Initialization

        Parameters:
            nFFT - FFT size used by Hilbert Transform
            overlapFactor - fractional overlap of adjacent segments
            smoothingWidth - width of smoothing filter to be applied to
                             envelope signal
        """
        SignalTransformer.__init__(self, ms_per_sample)
        self.rawOffset = 0
        self.nFFT = nFFT
        self.overlap = nFFT / overlapFactor
        self.halfOverlap = self.overlap / 2
        self.smoothingWidth = smoothingWidth
        self.data_per_FFT = self.nFFT- self.overlap       # samples computed per pass

        if self.ms_per_sample:
            assert(self.data_per_FFT % ms_per_sample == 0)


    def _transform(self):
        while self.nFFT <= len(self.rawData):  # remaining data to preprocess
            self._transformSegment()


    def _transformSegment(self):
        """Internal function to apply Hilbert transform and smoothing to segment of data"""
        seg = self.rawData[:self.nFFT]
        temp = scipy.signal.hilbert(seg, self.nFFT)
        self.rawData = self.rawData[self.data_per_FFT:]

        if not self.smoothingWidth:
            newData = np.abs(temp[self.halfOverlap:-self.halfOverlap])
        else:
            # apply smoothing filter
            csum = np.cumsum(np.abs(temp))
            newData = csum[self.smoothingWidth:] - csum[:-self.smoothingWidth]
            extraPts = len(newData) - (self.nFFT - self.overlap)
            assert extraPts >= 0
            idxLeft = int(extraPts // 2)
            newData = newData[idxLeft:idxLeft + self.data_per_FFT]

        if self.ms_per_sample > 1:     # decimate output signal
            newData = newData[::self.ms_per_sample]
        self.xformData = np.hstack([self.xformData, newData])


def performSegmentAcorr(sig, corrWidth=2000, minIBI=250, maxIBI=600, ms_per_sample=1,
                        useSQRT=True, useNorm=True,
                        useTriangleWeights=True, resolveHarmonics=True,
                        showPlot=False):
    """Performs autocorrelation on limitted segment size

    Params:
        sig - segment of signal to be analyzed
        corrWidth - window size used for autocorrelation (in samples)
        ms_per_sample - sample rate expr4ssed in milliseconds per sample (must be integer)
        minIBI, maxIBI - range of autocorrenation shift values (in samples)
        useSQRT - Compress output range using square root
        useNorm - Apply normalization to input signal (mean == 0)
        useTriangleWeights - Weight values relatibe to mid-point of signal segment
        resolveHarmonics - If subharmonics exist with similar correlation, pick lowest frequency subharmonic
        showPlot - optional show correlation values

    Returns:
        idxMax - Offset (IBI) with highest correlation result
        corrMax - Correlation coefficient at maxima, can be used to assess
                  coherency of result
        relCorrMax - Correlation coefficient at maxima relative to 80th percentile value.
                     Can also be used to assess quality of result.
    """

    if len(sig) < maxIBI + corrWidth:  # Detect insufficient data
        return -1, None, None

    # Scale and normalize input values
    if useSQRT:
        sig = sig - np.min(sig)
        sig = sig ** 0.5
    if useNorm:
        sig = sig - np.mean(sig)

    # Compute autocorrelation values for specified shift values
    corr = np.zeros(maxIBI + 1)
    if useTriangleWeights:
        leftLen = corrWidth // 2
        rightLen = corrWidth - leftLen
        weights = np.hstack([np.linspace(0.0, 1.0, leftLen + 2)[1:-1], np.linspace(1.0, 0.0, rightLen + 1)[:-1]])
        firstSeg = weights * sig[:corrWidth]
    else:
        firstSeg = sig[:corrWidth]
    corr[0] = np.mean(firstSeg[:corrWidth] * sig[:corrWidth])
    for i in range(minIBI, maxIBI + 1):
        corr[i] = np.mean(firstSeg * sig[i:i + corrWidth])
    corr = corr / corr[0]

    # Identify maxima
    idxMax = np.argmax(corr[minIBI:]) + minIBI
    if resolveHarmonics:
        idxMax, corrMax = selectLowestSubharmonic(corr, idxMax, minIBI, delta=250/ms_per_sample)
    else:
        corrMax = corr[idxMax]
    relCorrMax = corrMax / np.percentile(corr[minIBI: maxIBI + 1], 80)

    resultIBI = idxMax * ms_per_sample

    return resultIBI, corrMax, relCorrMax


def selectLowestSubharmonic(corr, idxSelectedPeak, minIBI, delta=250, harm_weight=1.0, proximity=0.1):
    """Look for lowest subharmonic above minIBI within tolerant of maximum correlation value

    Params:
        corr - all autocorrelation values
        idxSelectedPeak - default IBI (index of global corr maxima)
        minIBI - minimum allowable IBI
        delta - scan window used to identify local minima
        harm_weight - autocorrelation boost given when subharmonic felationship identified
        proximity - closeness of harmonic to actual peat to be considered match
    """
    selectedCorr = corr[idxSelectedPeak]
    selectedOrig = idxSelectedPeak

    # find all local minima
    allMax = []
    for iStart in range(minIBI, len(corr), delta - 1):
        iEnd = min(iStart + delta, len(corr))
        ibi = np.argmax(corr[iStart:iEnd]) + iStart
        if len(allMax) == 0 or allMax[-1][0] != ibi:
            allMax.append([ibi, corr[ibi]])
            # sort, largest correlation first

    # remove minima in close proximity
    newMax = [allMax[0]]
    for x in allMax[1:]:
        if x[0] - newMax[-1][0] < delta - 1:
            if x[1] > newMax[-1][1]:
                # replace
                newMax[-1] = x
        else:
            newMax.append(x)
    allMax = newMax

    # allMax = [x for x in allMax if x[1] > 0 and x[1] > selectedCorr/2.0]
    allMax = [x for x in allMax if x[1] > 0]

    # weight correlation based on harmomnic
    candidates = copy.copy(allMax)
    for peak in allMax:
        for harm in [2.0, 3.0]:
            harmIBI = int(peak[0] / harm)
            for entry in candidates:
                if abs(entry[0] - harmIBI) < proximity * entry[0]:
                    entry[1] = entry[1] + harm_weight * peak[1]

    allMax = sorted(candidates, key=lambda x: -x[1])

    if allMax:
        idxSelectedPeak = allMax[0][0]
        selectedCorr = allMax[0][1]
    else:
        return 0, 0

    if idxSelectedPeak == minIBI or idxSelectedPeak == len(corr):
        return 0, 0
    else:
        return idxSelectedPeak, selectedCorr


class Extractor:
    """Abstract class - general framework for autocorrelation extractor"""

    def __init__(self,
                 transformer,  # Hilbert Data Object
                 errorDetector=None,   # Error detection instance
                 corrWidth=5000,  # Window in samples used to compute initial HR estiate
                 minIBI=250,  # minimum heartbeat period in samples (nominally ms)
                 maxIBI=1000,  # maximum heartbeat period in samples (nominally ms)
                 shift=250,  # shift factor when computing successive segemt autocorrelations (in ms)
                 minCorr=0.4,  # Minimum valid autocorrelation
                 minRelCorr=None,  # Minimum relative autocorrelation
                 relAcorrWindow=1.5,  # segment size relative to instantaneous heartbeat used
                 # for incremental autocorrelations
                 relRangeIBI=0.9,  # scale factor relative to mose recent instaneous IBI
                 # controlling range used for next incremental autocorrelation
                 useTriangleWeights=True,  # Weight values relatibe to mid-point of signal segment
                 update_callback=None,  # Callback for processing of intermediate results
                 name='',   # extractor instance name
                 ):

        self.transformer = transformer
        self.errorDetector = errorDetector
        self.corrWidth = corrWidth
        self.minIBI = minIBI
        self.maxIBI = maxIBI
        self.shift = shift
        self.minCorr = minCorr
        self.minRelCorr = minRelCorr
        self.relAcorrWindow = relAcorrWindow
        self.relRangeIBI = relRangeIBI
        self.useTriangleWeights = useTriangleWeights
        self.update_callback = update_callback
        self.name = name


        # normalize values in samples
        self.ms_per_sample = transformer.ms_per_sample      # get sample rate from data transformer
        self.corrWidth_in_samples = corrWidth // self.ms_per_sample
        self.minIBI_in_samples = minIBI // self.ms_per_sample
        self.maxIBI_in_samples = maxIBI // self.ms_per_sample
        self.shift_in_samples = shift // self.ms_per_sample

        self.currentIBI = None
        self.offset = 0
        self.results = []
        self.seg_size = 256

        self.results_pos = []
        self.results_ibi = []
        self.results_raw = []
        self.results_hr = []
        self.results_cor = []
        self.results_rel = []
        self.results_valid = []


    def extract_incremental(self):
        raise Exception('Abstract method extract_incremental not implemented')

    def get_results_count(self):
        return len(self.results_pos)

    def get_results(self, asNumpy=True):

        if self.errorDetector:
            valid = self.errorDetector.applyLocalErrorDetection(np.array(self.results_valid),
                                                                np.array(self.results_raw))
            hr = np.array(self.results_hr) * valid

        if asNumpy:
            if not self.errorDetector:
                valid = np.array(self.results_valid)
                hr = np.array(self.results_hr)

            results = {'pos': np.array(self.results_pos),
                      'ibi':  np.array(self.results_ibi),
                      'raw':  np.array(self.results_raw),
                      'hr':   hr,
                      'cor':  np.array(self.results_cor),
                      'rel':  np.array(self.results_rel),
                      'valid': valid}
        else:
            if self.errorDetector:
                valid = valid.tolist()
                hr = hr.tolist()
            else:
                valid = self.results_valid
                hr = self.results_hr

            results = {'pos':   self.results_pos,
                       'ibi':   self.results_ibi,
                       'raw':   self.results_raw,
                       'hr':    hr,
                       'cor':   self.results_cor,
                       'rel':   self.results_rel,
                       'valid': valid}
        return results

    def validate(self, ibi, corr, relCorr):
        """Confirm that correlation result is within allowable range"""
        if ibi < self.minIBI or ibi > self.maxIBI:
            return False

        if self.minCorr is not None and corr < self.minCorr:
            return False

        if self.minRelCorr is not None and relCorr < self.minRelCorr:
            return False
        return True


class StaticExtractor(Extractor):
    """Autocorrelation extractor using fixed-duration window"""

    def extract_incremental(self):

        # Perform incremental correlations
        while True:
            seg = self.transformer.getSegment(self.offset,
                                              self.corrWidth_in_samples + self.maxIBI_in_samples)
            if isinstance(seg, NoneType):
                return False
            currentIBI, corrMax, relCorrMax = performSegmentAcorr(seg,
                                                                  corrWidth=self.corrWidth_in_samples,
                                                                  ms_per_sample=self.ms_per_sample,
                                                                  minIBI=self.minIBI_in_samples,
                                                                  maxIBI=self.maxIBI_in_samples,
                                                                  useTriangleWeights=self.useTriangleWeights,
                                                                  resolveHarmonics=True)
            self.currentIBI = currentIBI
            valid = self.validate(currentIBI, corrMax, relCorrMax)

            self.results_pos.append((self.offset * self.ms_per_sample) / 1000.0)
            self.results_ibi.append(currentIBI)
            self.results_raw.append(60000.0 / currentIBI if currentIBI != 0 else 0)
            self.results_hr.append(60000.0 / currentIBI if (currentIBI != 0) and valid else 0)
            self.results_cor.append(corrMax)
            self.results_rel.append(relCorrMax)
            self.results_valid.append(valid)

            self.offset += int(self.shift_in_samples)
            if self.update_callback:
                self.update_callback(self, self.name, self.results_pos[-1])
