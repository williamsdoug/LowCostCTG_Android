# coding: utf-8

#
#  Copyright Douglas Williams, 2018
#  All Rights Reserved
#


import pickle
import os
from pprint import pprint
import datetime
from matplotlib import pyplot as plt
import numpy as np
from scipy import signal

#from analyze_recordings import computeBaseline

def tolist(val):
    if isinstance(val, np.ndarray):
        return val.tolist()
    else:
        return val


def getCrossings(deriv, offset=1):
    idxMinima = np.nonzero(np.logical_and(deriv[:-1] < 0 , deriv[1:] >= 0))[0]
    idxMaxima = np.nonzero(np.logical_and(deriv[:-1] > 0 , deriv[1:] <= 0))[0]
    idxMinima = [x + offset for x in idxMinima]
    idxMaxima = [x + offset for x in idxMaxima]
    return idxMinima, idxMaxima


def filterSignal(sig, fType='lowpass', useFiltFilt=True, fs_Hz=1000.0, freq=100.0, order=1):
    """Applies lowpass or highpass filter to signal"""

    # CreateFilter
    if fType not in ['lowpass', 'highpass']:
        raise Exception('Invalid filter type: {}'.format(fType))
    fNyquist = fs_Hz / 2.0
    order = min(order, max(int(fs_Hz / freq) - 1, 1))  # limit order to avoid oscillations
    b, a = signal.butter(order, freq / fNyquist, fType)
    if not useFiltFilt:
        zi = signal.lfilter_zi(b, a)

    if len(sig.shape) > 1:
        if useFiltFilt:
            newSig = np.vstack([signal.filtfilt(b, a, sig[i])
                                for i in range(sig.shape[0])])
        else:
            newSig = np.vstack([signal.lfilter(b, a, sig[i], zi=zi * sig[i, 0])[0]
                                for i in range(sig.shape[0])])
    else:

        if useFiltFilt:
            newSig = signal.filtfilt(b, a, sig)
        else:
            newSig, _ = signal.lfilter(b, a, sig, zi=zi * sig[0])

    return newSig


FILTER_CACHE = {}
def computeBaseline(sig, fs=1.0, filt_initial=1.0/4, filt_final=1.0/16,
                     order=1, tol=5, nPad=1000):
    """Compute baseline using two-step process
    1) apply initial higher frequency filter, then clip portions of signal > 5bpm from initial baseline estimate
    2) compute final baseline by apploying lower-frequency filter (4x) to this clipped signal

    initial filter: 0.25 cycles per minute (period = 4 min)
    final filter:   0.0625 cycles per minute (period = 16 min)
    """
    global FILTER_CACHE
    initial = str(filt_initial)+'cpm'
    final = str(filt_final)+'cpm'
    
    fNyquist = fs / 2.0
    hertzToCyclesPerMin = 1.0 / 60.0

    if initial  not in FILTER_CACHE:
        freqInitial = hertzToCyclesPerMin * filt_initial
        FILTER_CACHE[initial] =  signal.butter(order, freqInitial / fNyquist, 'lowpass')

    if final  not in FILTER_CACHE:
        freqFinal = hertzToCyclesPerMin * filt_final
        FILTER_CACHE[final] = signal.butter(order, freqFinal / fNyquist, 'lowpass')
        
    try:
        preBaseline = signal.filtfilt(FILTER_CACHE[initial][0], FILTER_CACHE[initial][1], sig)
        mask = np.abs(sig - preBaseline) < tol
        indices = np.arange(len(sig))
        clipped = np.interp(indices, indices[mask], sig[mask])
        baseline = signal.filtfilt(FILTER_CACHE[final][0], FILTER_CACHE[final][1], clipped)
        return preBaseline, baseline
    except Exception:
        print 'Exception during computeBaseline'
        return np.array([]), np.array([])

    
def findDecel(sig, mask, sigSmoothed, baseline, ts, classifiers=[], nadirWidth=5, includeEnd=True,
              verbose=True):
    """Find decelerations"""
    
    delta = sig-baseline
    deltaSmoothed5 = sigSmoothed-baseline + 5
    allRelease, allOnset = getCrossings(deltaSmoothed5)

    allEndpoints = [[i, 'onset'] for i in allOnset] + [[i, 'release'] for i in allRelease]
    allEndpoints = sorted(allEndpoints)

    if includeEnd and allEndpoints and allEndpoints[-1] != 'release':
        # create release at end of recording
        allEndpoints.append([len(sig)-1, 'release'])
    
    results = []
    for i, entry in enumerate(allEndpoints):
        if entry[1] != 'release':
            continue
        if i == 0 or allEndpoints[i-1][1] != 'onset':
            continue

        idxStart = allEndpoints[i-1][0]
        idxEnd = entry[0]

        duration = (ts[idxEnd] - ts[idxStart])*60
        if duration < 10:
            continue

        # refine onset/release estimates using local slops
        slopeL = (sigSmoothed[idxStart] - sigSmoothed[idxStart+5])/5.0
        slopeR = (sigSmoothed[idxEnd] - sigSmoothed[idxEnd-5])/5.0
        if slopeL > 0:
            idxStart = max(idxStart-int(5.0/slopeL), 0)
        if slopeR > 0:
            idxEnd = min(idxEnd+int(5.0/slopeR), len(sig)-1)
            
        # estimate magnitude based on triangle
        auc = np.sum(-delta[idxStart:idxEnd])
        triangleRatio = 2 * auc / (idxEnd-idxStart)

        pctValid = np.mean(mask[idxStart:idxEnd])

        idxNadir = np.argmin(sigSmoothed[idxStart:idxEnd]) + idxStart
        # find actual
        idxMin = np.argmin(sig[idxNadir - nadirWidth:idxNadir + nadirWidth]) + idxNadir - nadirWidth
        #idxMin = np.argmin(sig[idxStart:idxEnd]) + idxStart
        relMag = -delta[idxMin]
        mag = sig[idxMin]

        duration = (ts[idxEnd] - ts[idxStart])*60
        tOnset = (ts[idxNadir]-ts[idxStart])*60
        tRelease = (ts[idxEnd]-ts[idxNadir])*60

            
        decel = {'relMag':relMag, 'mag':mag, 'pctValid':pctValid,
                 'duration':duration, 'tOnset':tOnset, 'tRelease':tRelease,
                 'idxNadir': idxNadir, 'idxStart': idxStart, 'idxEnd': idxEnd,
                 'tNadir':float(ts[idxNadir]), 'tStart':float(ts[idxStart]), 'tEnd':float(ts[idxEnd]),
                 'triangleRatio':triangleRatio}
        
        found = False
        for classifier in classifiers:
            if classifier(decel):
                found = True
                break
                
        if not found:
            continue
        
        results.append(decel)

        if verbose:
            print '{:5.2f}m :{:5.1f} bpm   dur: {:3.0f}s  mag: {:5.1f} bpm  valid: {:0.0f}%  [{}]'.format(
                ts[idxNadir], relMag, duration, mag, pctValid*100.0, decel['classification'])
            print '                    tOnset: {:3.0f}s   tRelease: {:3.0f}s  span: {:5.2f} - {:5.2f} min'.format(
                tOnset, tRelease, ts[idxStart], ts[idxEnd])
        
    return results


def summarizeDecels(allDecels, tStart=None, tEnd=None, exclude=[]):
    found = False
    for decel in allDecels:
        if tStart and decel['tEnd'] < tStart:
            continue
        if tEnd and decel['tStart'] > tEnd:
            continue
        if decel['classification'] in exclude:
            continue

        print '{:5.2f}m :{:5.1f} bpm   dur: {:3.0f}s ({:3.1f}min) mag: {:5.1f} bpm  valid: {:0.0f}%  [{}]'.format(
            decel['tNadir'], decel['relMag'], decel['duration'], decel['duration']/60.0,
            decel['mag'], decel['pctValid'] * 100.0, decel['classification'])
        print '                    tOnset: {:3.0f}s   tRelease: {:3.0f}s  span: {:5.2f} - {:5.2f} min'.format(
            decel['tOnset'], decel['tRelease'], decel['tStart'], decel['tEnd'])
        found = True

    return found


def classifyDecel(decel, classification='valid',
                  minDuration=14, maxDuration=60*3, minMag=14, minOnset=0,
                  minPctValid=0.5, minOnsetRatio=0, maxOnsetRatio=0.6, showDetail=False):

    if (decel['duration'] < minDuration or decel['duration'] > maxDuration or decel['tOnset'] < minOnset
        or decel['relMag'] < minMag or decel['pctValid'] < minPctValid):
        return False

    if decel['triangleRatio'] < minMag:
        if showDetail:
            print 'rejected due to triangleRatio'
            pprint(decel)
        return False

    onsetRatio = decel['tOnset']/decel['duration']
    if onsetRatio > maxOnsetRatio:  # skewed
        if showDetail:
            print 'rejected due to maxOnsetRatio'
            pprint(decel)
        return False

    if onsetRatio < minOnsetRatio:  # skewed
        if showDetail:
            print 'rejected due to minOnsetRatio'
            pprint(decel)
        return False

    decel['classification'] = classification
    return True






def computeAnnotations(sigHR, mask, ts,
                       validParams={'classification': 'valid',
                                    'minDuration': 14, 'maxDuration': 60 * 3,
                                    'minMag': 14, 'minPctValid': 0.5, 'maxOnsetRatio': 0.6},
                       borderlineParams={'classification': 'borderline',
                                         'minDuration': 12, 'maxDuration': 60 * 3,
                                         'minMag': 12, 'minPctValid': 0.5, 'maxOnsetRatio': 0.7},
                       fVar = 1.0/50):

    # interpolate any missing datapoints
    indices = np.arange(len(sigHR))
    sigHR = np.interp(indices, indices[mask], sigHR[mask])

    _, baseline = computeBaseline(sigHR)
    _, localBaseline = computeBaseline(sigHR, filt_initial=1.0 / 2, filt_final=1.0 / 6)

    detailHR = filterSignal(sigHR, fType='lowpass', freq=1.0 / 6, useFiltFilt=True, order=4, fs_Hz=1.0)
    smoothHR = filterSignal(sigHR, fType='lowpass', freq=1.0 / 18, useFiltFilt=True, order=4, fs_Hz=1.0)

    classifiers = [lambda x: classifyDecel(x, **validParams),
                   lambda x: classifyDecel(x, **borderlineParams)]
    allDecels = findDecel(detailHR, mask, smoothHR, localBaseline, ts, classifiers=classifiers)
    if len(allDecels) == 0:
        print 'NO DECELS FOUND'
        # continue

    variability = computeVariability(sigHR, freq=fVar)
    print len(baseline), len(localBaseline), len(sigHR)

    if len(localBaseline) > 0:
        deltaLocalBaseline = sigHR-localBaseline
    else:
        deltaLocalBaseline = np.array([])

    try:
        deltaBaseline = sigHR-baseline
    except Exception:
        deltaBaseline = deltaLocalBaseline

    return baseline, allDecels, deltaBaseline, deltaLocalBaseline, variability


def computeVariability(sig, freq=1.0/25):
    smoothed = filterSignal(sig, fType='lowpass', freq=freq, useFiltFilt=True,
                        order=4, fs_Hz=1.0)
    return sig - smoothed

