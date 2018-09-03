# coding: utf-8

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
import time
import copy

NoneType = type(None)


# 
# Code
# 

class RMSTransformer:
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

        self.rawData = np.array([])
        self.envelope = np.array([])

        fNyquist = samplerate / 2.0
        fNyquistD = fNyquist / downsample

    def addData(self, newData):
        self.rawData = np.append(self.rawData, newData)

    def getSegment(self, idx, width):
        """Gets segment of transformed data.  Perform lazy transformation if needed
        Params:
            idx   - starting offset of data segment in samples
            width - width of segment in samples
        """

        if isinstance(self.rawData, type(None)):
            return None

        if (idx + width) > len(self.envelope):  # insufficient data to satisfy request
            self._transformSegment()

        if idx + width > len(self.envelope):
            return None

        x = self.envelope[idx:idx + width]

        if self.normalize:
            t = np.percentile(x, 90)
            x[x > t] = t
            x = x - np.percentile(x, 10)
            x[x < 0] = 0
            x = x ** 0.5
            x = x - np.mean(x)

        return x

    def _transformSegment(self):
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

        self.envelope = np.append(self.envelope, sig)
        self.rawData = self.rawData[N:]  # discard processed data


class ZCTransformer:
    """Object used to transform audio signal to extract pitch using zero crossing rate
    """

    def __init__(self, zc_interval=320, downsample=8, useLog=False, normalize=False, useReciprocal=True,
                 clip=False, clipUpperPct=80, clipLowerPct=20):
        """Initialization

        Parameters:
            zc_interval - sample period for XC measurement
            downsample - dopwnsample factor.  If input is 8K sps, use 8 for 1K output sps
            useLog - apply log to output
            normalize - recenter output around mean
            useReciprocal - return return 1/zc rate
            useClip - apply clipping to output
            clipUpperPct = upper threshold for clipping
            clipLowerPct = lower threshold for clipping
        """

        self.zc_interval = zc_interval
        self.downsample = downsample
        self.useLog = useLog
        self.clip = clip
        self.clipUpperPct = clipUpperPct
        self.clipLowerPct = clipLowerPct
        self.normalize = normalize
        self.useReciprocal = useReciprocal

        self.rawData = np.array([])
        self.hann = scipy.signal.hann(zc_interval)
        self.pitch = np.array([])

    def addData(self, newData):
        self.rawData = np.append(self.rawData, newData)

    def getSegment(self, idx, width):
        """Gets segment of transformed data.  Perform lazy transformation if needed
        Params:
            idx   - starting offset of data segment in samples
            width - width of segment in samples
        """

        if isinstance(self.rawData, type(None)):
            return None

        if (idx + width) > len(self.pitch):  # insufficient data to satisfy request
            self._transformSegment()

        if idx + width > len(self.pitch):
            return None

        x = self.pitch[idx:idx + width]

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

    def _transformSegment(self):
        """Internal function to apply Hilbert transform and smoothing to segment of data"""
        if len(self.rawData) <= self.zc_interval:
            return

        # find zero prossings (rising edge)
        zc = np.logical_and(self.rawData[:-1] < 0, self.rawData[1:] >= 0)
        # compute rate over interval
        zcr = np.array([np.sum(zc[i:i + self.zc_interval] * self.hann)
                        for i in range(0, len(zc) - self.zc_interval, self.downsample)])
        zcr[zcr < 1] = 1
        if self.useReciprocal:
            self.pitch = np.append(self.pitch, 1.0 / zcr)
        else:
            self.pitch = np.append(self.pitch, zcr)

        N = len(zcr) * self.downsample  # discard processed raw data
        self.rawData = self.rawData[N:]


class HibertDataTransformer:
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

    def __init__(self, nFFT=2 ** 10, overlapFactor=8, smoothingWidth=43):
        """Initialization

        Parameters:
            nFFT - FFT size used by Hilbert Transform
            overlapFactor - fractional overlap of adjacent segments
            smoothingWidth - width of smoothing filter to be applied to
                             envelope signal
        """
        self.rawData = None
        self.rawOffset = 0
        self.nFFT = nFFT
        self.overlap = nFFT / overlapFactor
        self.halfOverlap = self.overlap / 2
        self.smoothingWidth = smoothingWidth
        self.envelope = np.zeros(0)
        self.cumsum = np.zeros(0)

    def addData(self, newData):
        if isinstance(self.rawData, type(None)):
            self.rawData = np.copy(newData)
        else:
            self.rawData = np.append(self.rawData, newData)

    def getSegment(self, idx, width):
        """Gets segment of transformed data.  Perform lazy transformation if needed
        Params:
            idx   - starting offset of data segment in samples
            width - width of segment in samples
        """

        if isinstance(self.rawData, type(None)):
            return None

        while (idx + width > len(self.envelope)  # insufficient data to satisfy request
               and self.rawOffset + self.nFFT <= len(self.rawData)):  # remaining data to preprocess
            self._transformSegment()

        if idx + width <= len(self.envelope):
            return self.envelope[idx:idx + width]
        else:
            return None

    def _transformSegment(self):
        """Internal function to apply Hilbert transform and smoothing to segment of data"""
        seg = self.rawData[self.rawOffset:self.rawOffset + self.nFFT]
        temp = scipy.signal.hilbert(seg, self.nFFT)
        self.rawOffset = self.rawOffset + self.nFFT - self.overlap
        if not self.smoothingWidth:
            self.envelope = np.hstack([self.envelope,
                                       np.abs(temp[self.halfOverlap:-self.halfOverlap])])
        else:
            # apply smoothing filter
            csum = np.cumsum(np.abs(temp))
            filteredData = csum[self.smoothingWidth:] - csum[:-self.smoothingWidth]
            extraPts = len(filteredData) - (self.nFFT - self.overlap)
            assert extraPts >= 0
            idxLeft = int(extraPts // 2)
            filteredData = filteredData[idxLeft:idxLeft + self.nFFT - self.overlap]
            self.envelope = np.hstack([self.envelope, filteredData])


def performSegmentAcorr(sig, corrWidth=2000, minIBI=250, maxIBI=600,
                        useSQRT=True, useNorm=True,
                        useTriangleWeights=True, resolveHarmonics=True,
                        showPlot=False):
    """Performs autocorrelation on limitted segment size

    Params:
        sig - segment of signal to be analyzed
        corrWidth - window size used for autocorrelation
        minIBI, maxIBI - range of autocorrenation shift values
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
        idxMax, corrMax = selectLowestSubharmonic(corr, idxMax, minIBI)
    else:
        corrMax = corr[idxMax]
    relCorrMax = corrMax / np.percentile(corr[minIBI: maxIBI + 1], 80)

    return idxMax, corrMax, relCorrMax


def OLDselectLowestSubharmonic(corr, idxSelectedPeak, minIBI, tol=0.8, maxSubharmonic=6, pctJitter=0.05):
    """Look for lowest subharmonic above minIBI within tolerant of maximum correlation value

    Params:
        corr - all autocorrelation values
        idxSelectedPeak - default IBI (index of global corr maxima)
        minIBI - minimum allowable IBI
        tolerace = minimum relative acorr relative to global maxima to be considered valid subharmonic
        maxSubharmonic - maximum subharmonic to be considers for analysis
        pctJitter - allowable IBI jitter relative to subharmonic mid-point to be considered when
                    computing local maxima
    """
    selectedCorr = corr[idxSelectedPeak]
    for i in range(maxSubharmonic, 1, -1):
        idxCandidate = idxSelectedPeak // i
        # print 'checking', idxCandidate
        if idxCandidate < minIBI:  # skip is subharmonic is out of range
            # print'outside range -- below:', minIBI
            continue
        # compute local maxima
        idxDelta = int(idxCandidate * pctJitter)
        idxStart = max(minIBI, int(idxCandidate - idxDelta))
        idxLocalMax = np.argmax(corr[idxStart:idxCandidate + idxDelta]) + idxStart
        if corr[idxLocalMax] > corr[idxSelectedPeak]:
            # print 'selecting subharmonic'
            return idxLocalMax
    # print 'keeping', idxSelectedPeak
    return idxSelectedPeak


def OLD2selectLowestSubharmonic(corr, idxSelectedPeak, minIBI, tol=0.7, delta=250):
    """Look for lowest subharmonic above minIBI within tolerant of maximum correlation value

    Params:
        corr - all autocorrelation values
        idxSelectedPeak - default IBI (index of global corr maxima)
        minIBI - minimum allowable IBI
        tolerace = minimum relative acorr relative to global maxima to be considered valid subharmonic
        maxSubharmonic - maximum subharmonic to be considers for analysis
        pctJitter - allowable IBI jitter relative to subharmonic mid-point to be considered when
                    computing local maxima
    """
    selectedCorr = corr[idxSelectedPeak]
    # find all local minima
    allMax = []
    for iStart in range(minIBI, len(corr), delta - 1):
        iEnd = min(iStart + delta, len(corr))
        ibi = np.argmax(corr[iStart:iEnd]) + iStart
        if len(allMax) == 0 or allMax[-1][0] != ibi:
            allMax.append((ibi, corr[ibi]))
            # sort, largest correlation first
    allMax = sorted(allMax, key=lambda x: -x[1])

    # find smallest IBI with correlation above tolerance
    threshold = selectedCorr * tol
    for ibi, this_cor in allMax:
        if this_cor < threshold:
            break
        if ibi < idxSelectedPeak:
            idxSelectedPeak = ibi
    return idxSelectedPeak


def selectLowestSubharmonic(corr, idxSelectedPeak, minIBI, delta=250, harm_weight=1.0, proximity=0.1):
    """Look for lowest subharmonic above minIBI within tolerant of maximum correlation value

    Params:
        corr - all autocorrelation values
        idxSelectedPeak - default IBI (index of global corr maxima)
        minIBI - minimum allowable IBI
        delta - scan window used to lidentify local minima
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
                 hdo,  # Hilbert Data Object
                 corrWidth=5000,  # Window in samples used to compute initial HR estiate
                 staticCorrWidth=2000,  # static correlation width used with composite extractor
                 minIBI=250,  # minimum heartbeat period in samples (nominally ms)
                 maxIBI=1000,  # maximum heartbeat period in samples (nominally ms)
                 shift=250,  # shift factor when computing successive segemt autocorrelations (in ms)
                 skip=1000,  # skip factor  when unable to to identify valid autocorrelation (in ms)
                 minCorr=0.4,  # Minimum valid autocorrelation
                 minRelCorr=None,  # Minimum relative autocorrelation
                 relAcorrWindow=1.5,  # segment size relative to instantaneous heartbeat used
                 # for incremental autocorrelations
                 relRangeIBI=0.9,  # scale factor relative to mose recent instaneous IBI
                 # controlling range used for next incremental autocorrelation
                 useTriangleWeights=True,  # Weight values relatibe to mid-point of signal segment
                 update_callback=None,  # Callback for processing of intermediate results
                 ):

        self.hdo = hdo
        self.corrWidth = corrWidth
        self.staticCorrWidth = staticCorrWidth
        self.minIBI = minIBI
        self.maxIBI = maxIBI
        self.shift = shift
        self.skip = skip
        self.minCorr = minCorr
        self.minRelCorr = minRelCorr
        self.relAcorrWindow = relAcorrWindow
        self.relRangeIBI = relRangeIBI
        self.useTriangleWeights = useTriangleWeights
        self.update_callback = update_callback

        self.currentIBI = None
        self.offset = 0
        self.results = []
        self.seg_size = 256

    def extract_incremental(self):
        raise Exception('Abstract method extract_incremental not implemented')

    def get_results(self):
        # return results organized as arrays by each metric
        results = {}
        for key in ['pos', 'ibi', 'cor', 'rel', 'hr', 'valid', 'raw']:
            results[key] = np.array([x[key] for x in self.results])

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
            seg = self.hdo.getSegment(self.offset, self.corrWidth + self.maxIBI)
            if isinstance(seg, NoneType):
                return False
            currentIBI, corrMax, relCorrMax = performSegmentAcorr(seg, corrWidth=self.corrWidth,
                                                                  minIBI=self.minIBI, maxIBI=self.maxIBI,
                                                                  useTriangleWeights=self.useTriangleWeights,
                                                                  resolveHarmonics=True)
            self.currentIBI = currentIBI
            valid = self.validate(currentIBI, corrMax, relCorrMax)
            self.results.append({'pos': self.offset / 1000.0, 'ibi': currentIBI,
                                 'raw': 60000.0 / currentIBI if currentIBI != 0 else 0,
                                 'hr': 60000.0 / currentIBI if (currentIBI != 0) and valid else 0,
                                 'cor': corrMax, 'rel': relCorrMax, 'valid': True})

            self.offset += int(self.shift)
            if self.update_callback:
                self.update_callback(self.results)


class DynamicExtractor(Extractor):
    """Autocorrelation extractor with correlation windows tunded for most recent successful
    extraction +/- relRangeIBI (scale factor)"""

    def extract_incremental(self):

        # Perform incremental correlations
        while True:
            if self.currentIBI is None:
                # Find first valid value using autocorrelation larger window.
                # Skip when nothing found
                seg = self.hdo.getSegment(self.offset, self.corrWidth + self.maxIBI)
                if isinstance(seg, NoneType):
                    return False
                time.sleep(0)
                proposedIBI, corr, relCorr = performSegmentAcorr(seg, corrWidth=self.corrWidth,
                                                                 minIBI=self.minIBI, maxIBI=self.maxIBI,
                                                                 resolveHarmonics=True)

                if self.validate(proposedIBI, corr, relCorr):
                    # print 'Valid segment @ {:0.2f}  estimate: {}'.format(self.offset/1000.0, proposedIBI)
                    self.currentIBI = proposedIBI
                else:
                    # Invalid result -- Advance and try again
                    self.currentIBI = None
                    skip_end = self.offset + self.skip
                    # print '*** Invalid segment @ {:0.2f}  skipping to: {:0.2f} ***'.format(
                    #     self.offset / 1000.0, skip_end / 1000.0)

                    while self.offset < skip_end:
                        self.results.append({'pos': self.offset / 1000.0, 'ibi': 0, 'hr': 0, 'raw': 0,
                                             'cor': corr, 'rel': relCorr, 'valid': False})
                        self.offset += int(self.shift)
                        if self.update_callback:
                            self.update_callback(self.results)
                    continue

            # adjust local operating range
            localCorrWidth = int(self.currentIBI * self.relAcorrWindow)
            localMinIBI = int(self.currentIBI * self.relRangeIBI)
            localMaxIBI = int(self.currentIBI / self.relRangeIBI)

            seg = self.hdo.getSegment(self.offset, localCorrWidth + localMaxIBI)
            if isinstance(seg, type(None)):
                # Insufficient data, try again later
                return
            time.sleep(0)
            currentIBI, corrMax, relCorrMax = performSegmentAcorr(seg, corrWidth=localCorrWidth,
                                                                  minIBI=localMinIBI, maxIBI=localMaxIBI,
                                                                  resolveHarmonics=True,
                                                                  useTriangleWeights=self.useTriangleWeights)

            assert currentIBI >= 0
            if self.validate(currentIBI, corrMax, relCorrMax):
                self.currentIBI = currentIBI
                self.results.append({'pos': self.offset / 1000.0, 'ibi': currentIBI,
                                     'raw': 60000.0 / currentIBI if currentIBI > 0 else 0,
                                     'hr': 60000.0 / currentIBI if currentIBI > 0 else 0,
                                     'cor': corrMax, 'rel': relCorrMax, 'valid': True})
            else:
                # Invalid result, force recalibration
                self.currentIBI = None
                self.results.append({'pos': self.offset / 1000.0, 'ibi': 0,
                                     'raw': 60000.0 / currentIBI if currentIBI > 0 else 0,
                                     'hr': 0,
                                     'cor': corrMax, 'rel': relCorrMax, 'valid': False})

            self.offset += int(self.shift)
            if self.update_callback:
                self.update_callback(self.results)


class CompositeExtractor(Extractor):
    """Initially attempts to use dynamic autocorrelation with.  If failts, tries again during static
    autocorrelation nominally over 2000ms"""

    def extract_incremental(self):

        # Perform incremental correlations
        while True:
            if self.currentIBI is None:
                # Find first valid value using autocorrelation larger window.
                # Skip when nothing found
                seg = self.hdo.getSegment(self.offset, self.corrWidth + self.maxIBI)
                if isinstance(seg, NoneType):
                    return False
                time.sleep(0)
                proposedIBI, corr, relCorr = performSegmentAcorr(seg, corrWidth=self.corrWidth,
                                                                 minIBI=self.minIBI, maxIBI=self.maxIBI,
                                                                 resolveHarmonics=True)

                if self.validate(proposedIBI, corr, relCorr):
                    # print 'Valid segment @ {:0.2f}  estimate: {}'.format(self.offset/1000.0, proposedIBI)
                    self.currentIBI = proposedIBI
                else:
                    # Invalid result -- Advance and try again
                    self.currentIBI = None
                    skip_end = self.offset + self.skip
                    # print '*** Invalid segment @ {:0.2f}  skipping to: {:0.2f} ***'.format(
                    #     self.offset / 1000.0, skip_end / 1000.0)

                    while self.offset < skip_end:
                        self.results.append({'pos': self.offset / 1000.0, 'ibi': 0, 'hr': 0, 'raw': 0,
                                             'cor': corr, 'rel': relCorr, 'valid': False})
                        self.offset += int(self.shift)
                        if self.update_callback:
                            self.update_callback(self.results)
                    continue

            # adjust local operating range
            localCorrWidth = int(self.currentIBI * self.relAcorrWindow)
            localMinIBI = int(self.currentIBI * self.relRangeIBI)
            localMaxIBI = int(self.currentIBI / self.relRangeIBI)

            seg = self.hdo.getSegment(self.offset, localCorrWidth + localMaxIBI)
            if isinstance(seg, type(None)):
                # Insufficient data, try again later
                return
            time.sleep(0)
            currentIBI, corrMax, relCorrMax = performSegmentAcorr(seg, corrWidth=localCorrWidth,
                                                                  minIBI=localMinIBI, maxIBI=localMaxIBI,
                                                                  useTriangleWeights=self.useTriangleWeights)

            if self.validate(currentIBI, corrMax, relCorrMax):
                self.currentIBI = currentIBI
                self.results.append({'pos': self.offset / 1000.0, 'ibi': currentIBI,
                                     'raw': 60000.0 / currentIBI if currentIBI != 0 else 0,
                                     'hr': 60000.0 / currentIBI if currentIBI != 0 else 0,
                                     'cor': corrMax, 'rel': relCorrMax, 'valid': True})
            else:
                # Invalid result, Try medium duration static autocorrelation
                seg = self.hdo.getSegment(self.offset, self.staticCorrWidth + self.maxIBI)
                if isinstance(seg, NoneType):
                    return False
                time.sleep(0)
                currentIBI, corrMax, relCorrMax = performSegmentAcorr(seg, corrWidth=self.staticCorrWidth,
                                                                      minIBI=self.minIBI, maxIBI=self.maxIBI,
                                                                      useTriangleWeights=self.useTriangleWeights,
                                                                      resolveHarmonics=True)
                if self.validate(currentIBI, corrMax, relCorrMax):
                    self.currentIBI = currentIBI
                    self.results.append({'pos': self.offset / 1000.0, 'ibi': currentIBI,
                                         'raw': 60000.0 / currentIBI if currentIBI != 0 else 0,
                                         'hr': 60000.0 / currentIBI if currentIBI != 0 else 0,
                                         'cor': corrMax, 'rel': relCorrMax, 'valid': True})
                else:
                    # Invalid result, force recalibration
                    self.currentIBI = None
                    self.results.append({'pos': self.offset / 1000.0, 'ibi': 0,
                                         'raw': 60000.0 / currentIBI if currentIBI != 0 else 0,
                                         'hr': 0,
                                         'cor': corrMax, 'rel': relCorrMax, 'valid': False})

            self.offset += int(self.shift)
            if self.update_callback:
                self.update_callback(self.results)

