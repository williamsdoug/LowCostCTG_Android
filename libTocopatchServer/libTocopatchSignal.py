# coding: utf-8

#
#  Copyright Douglas Williams, 2018
#  All Rights Reserved
#

#
# Signal Processing for TocoPatch -- Extracts relevant signal components
#
# Based on algorithm concepts in : Low-complexity intrauterine pressure estimation using the Teager energy Operator by M.J. Rooijakkers, C. Rabotti, M. Mischi
#
# - https://www.tue.nl/en/university/departments/electrical-engineering/department/staff/detail/ep/e/d/ep-uid/20031643/ep-tab/4/
# - https://www.tue.nl/en/publication/ep/p/d/ep-uid/ec6a502e-f1af-4ae6-beb0-21a59a0519eb/
# - http://repository.tue.nl/ec6a502e-f1af-4ae6-beb0-21a59a0519eb
#

import numpy as np
import scipy
from scipy import signal


def processUC(sigIn, fs, **kwargs):

    try:
        sigD = signal.decimate(sigIn, 8, zero_phase=True)
        sigD = signal.decimate(sigD, 8, zero_phase=True)
    except Exception:
        return np.array([]), np.array([]), np.array([]), np.array([])

    sigD = sigD - np.mean(sigD)
    fs = fs / 64.0

    ts = np.arange(len(sigD)) / fs
    sigRel, sigUC = isolateUC(sigD, fs, **kwargs)
    return ts, sigD, sigRel, sigUC


class ProcessUC:
    def __init__(self, fs, **kwargs):
        self.decimator = Decimator([8,8], overlap=2, minPts=2) #minPts=10)
        self.downsample = 64.0
        self.fs = fs / self.downsample
        self.idxStart = 0
        self.kwargs = kwargs

        print 'kwargs:', kwargs

    def updateFS(self, fs):
        self.fs = fs / self.downsample

    def processData(self, sigIn, skew=0.0):
        self.decimator.decimateIncremental(sigIn[self.idxStart:])
        #self.idxStart = len(sigIn)

        sigD = self.decimator.getData()

        print 'sigD:', len(sigD), len(sigIn), len(sigIn[self.idxStart:])

        self.idxStart = len(sigIn)
        if len(sigD) == 0:
            return np.array([]), np.array([]), np.array([]), np.array([]), np.array([])

        sigD = sigD - np.mean(sigD)
        ts = skew + np.arange(len(sigD)) / self.fs

        # sigRel, sigUC = isolateUC(sigD, self.fs, **self.kwargs)
        sigRel, sigUC, sigAltUC = isolateUC(sigD, self.fs, **self.kwargs)
        return ts, sigD, sigRel, sigUC, sigAltUC


def isolateUC(sigRaw, fs, fLower=.25, fUpper=0.8, orderBandpass=3,
              freqUC=1.0 / 72, freqUC2=1.0 / 108, orderUC=4,
              pctClipMax=95, clipMaxScale=2, pctClipMin=20):
    # Select relevant frequencies and remove outliers
    try:
        sigFiltered = butter_bandpass_filter(sigRaw, fLower, fUpper, fs, order=orderBandpass)
    except Exception:
        return np.array([]), np.array([]), np.array([])
    sigFiltered = clipExtremeAC(sigFiltered, pct=pctClipMax, scale=clipMaxScale)

    # Rectify and smooth
    try:
        sigUC = butter_lowpass_filter(np.abs(sigFiltered), freq=freqUC, order=orderUC, fs=fs)
        sigUC = clipMinDC(sigUC, pctClipMin)
        sigUC = sigUC * (1.0 / np.max(sigUC))
    except Exception:
        sigUC = np.array([])

    # Afternate version, if requested
    sigUC2 = np.array([])
    if freqUC2 is not None:
        try:
            sigUC2 = butter_lowpass_filter(np.abs(sigFiltered), freq=freqUC2, order=orderUC, fs=fs)
            sigUC2 = clipMinDC(sigUC2, pctClipMin)
            sigUC2 = sigUC2 * (1.0 / np.max(sigUC2))
        except Exception:
            pass

    return sigFiltered, sigUC, sigUC2

# Basic signal processing functions


def butter_bandpass(lowcut, highcut, fs, order=5):
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = scipy.signal.butter(order, [low, high], btype='band')
    return b, a


def butter_bandpass_filter(data, lowcut, highcut, fs, order=5):
    b, a = butter_bandpass(lowcut, highcut, fs, order=order)
    y = scipy.signal.filtfilt(b, a, data)
    return y


def butter_highpass(freq, fs, order=5):
    nyq = 0.5 * fs
    freq = freq / nyq
    b, a = scipy.signal.butter(order, freq, btype='highpass')
    return b, a


def butter_highpass_filter(data, freq, fs, order=5):
    b, a = butter_highpass(freq, fs, order=order)
    y = scipy.signal.filtfilt(b, a, data)
    return y


def butter_lowpass(freq, fs, order=5):
    nyq = 0.5 * fs
    freq = freq / nyq
    b, a = scipy.signal.butter(order, freq, btype='lowpass')
    return b, a


def butter_lowpass_filter(data, freq, fs, order=5):
    b, a = butter_lowpass(freq, fs, order=order)
    y = scipy.signal.filtfilt(b, a, data)
    return y


def butter_lowpass_filter_pad(data, freq, fs, order=5):
    n = int(fs * 1.0 / freq)
    padData = np.pad(data, (n, n), 'edge')
    y = butter_lowpass_filter(padData, freq, fs, order=order)
    y = y[n:-n]
    assert len(y) == len(data)
    return y


def teager(x):
    return np.abs(x[1:-1] ** 2 - x[:-2] * x[2:])


def running_mean(x, N, isCentered=True):
    # compute running mean in steady state
    cumsum = np.cumsum(np.insert(x, 0, 0))
    y = (cumsum[N:] - cumsum[:-N]) / float(N)

    # handle edges
    resid = len(x) - len(y)
    if isCentered:
        left = resid // 2
        right = resid - left
    else:
        left = resid
        right = 0
    y = np.pad(y, (left, right), mode='constant', constant_values=0)
    if left > 0:
        y[:left] = cumsum[1:left + 1] / np.arange(1, left + 1)
    if right > 0:
        y[-right:] = (cumsum[-1] - cumsum[-right - 1:-1]) / np.arange(right, 0, -1)

    return y


def clipExtremeAC(sig, pct=95, scale=2):
    thresh = np.percentile(np.abs(sig), pct)*scale
    sigClipped = np.copy(sig)
    sigClipped[sigClipped > thresh] = thresh
    sigClipped[sigClipped < -thresh] = -thresh
    return sigClipped


def clipMinDC(sig, pct=20):
    thresh = np.percentile(sig, pct)
    sigClipped = sig - thresh
    sigClipped[sigClipped < 0] = 0
    return sigClipped


def clip(sig, isHard=True, sigma=1.0):
    thresh = np.median(np.abs(sig)) * sigma
    sigH = np.copy(sig)
    sigL = np.copy(sig)
    if isHard:
        sigH[sigH < thresh] = 0
        sigL[sigL > - thresh] = 0
    else:
        sigH = sigH - thresh
        sigH[sigH < 0] = 0
        sigL = sigL + thresh
        sigL[sigL > 0] = 0

    return sigL + sigH


def localMax(x, w=50):
    wL = w // 2
    wR = w - wL
    N = len(x)
    local = np.zeros(N)
    absX = np.abs(x)
    for i in range(N):
        iStart = max(i - wL, 0)
        iEnd = min(i + wR, N)
        local[i] = np.max(absX[iStart:iEnd])

    ret = np.zeros(N)
    for i in range(N):
        if i < 2 * w:
            ret[i] = min(absX[i], local[i + 2 * w])
        elif i < N - 2 * w - 1:
            highestNeighbor = max(local[i + 2 * w], local[i - 2 * w])
            ret[i] = min(absX[i], highestNeighbor)
        else:
            ret[i] = min(absX[i], local[i - 2 * w])
    return ret


class Decimator:
    def __init__(self, downsample, overlap=2, minPts=10):
        self.downsample_factors = downsample
        self.downsample = np.prod(downsample)
        self.overlap = overlap
        self.coldStart = True
        self.flushed = False
        self.inData = np.array([])
        self.outData = np.array([])
        self.minPtsIn = minPts * self.downsample

    def decimateIncremental(self, data):
        # print 'Injest: {}'.format(len(data))
        self.inData = np.append(self.inData, data)

        pastPtr = len(self.outData)

        self._decimate()
        #print 'State inData: {}  outData: {}'.format(len(self.inData), len(self.outData))
        return self.outData[pastPtr:]

    def getData(self):
        if not self.flushed:
            self._decimate(flush=True)
            self.flushed = True
        return self.outData

    def _decimate(self, flush=False):
        if not flush and len(self.inData) < self.minPtsIn:  # b process data in batches
            print 'insufficient data - minPtsIn', len(self.inData),  self.minPtsIn
            return

        if len(self.inData) < self.downsample:  # b process data in batches
            print 'insufficient data - downsample', len(self.inData),  self.downsample
            return

        newOutData = self.inData
        if flush:
            # ignore errors related to insufficient data if performing flush
            try:
                for factor in self.downsample_factors:
                    newOutData = signal.decimate(newOutData, factor, zero_phase=True)
            except Exception:
                print 'Exception during _decimate with Flush'
                return
        else:
            for factor in self.downsample_factors:
                newOutData = signal.decimate(newOutData, factor, zero_phase=True)

        # discard overlap data
        if self.coldStart:
            if flush:
                self.outData = newOutData
            else:
                self.outData = newOutData[:-self.overlap]
            self.coldStart = False
        else:
            if flush:
                self.outData = np.append(self.outData, newOutData[self.overlap:])
            else:
                self.outData = np.append(self.outData, newOutData[self.overlap:-self.overlap])

        # discard input data, preserving overlap data
        nDiscard = (len(newOutData) - 2 * self.overlap) * self.downsample
        self.inData = self.inData[nDiscard:]

        self.coldStart = False

