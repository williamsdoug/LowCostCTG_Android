# coding: utf-8

#
#  Copyright Douglas Williams, 2018
#  All Rights Reserved
#

from pprint import pprint
import numpy as np
from scipy import signal

from libSignalProcessing import filterSignal, getCrossings, tolist

#
# Design Notes
#
# Overall Flow
# 1. Extract UC - Modality Specific
# 2. Extract Prolonged Decelerations
#   A. Extract Candidates
#   B. Merge Adjacent (TODO)
#   C. Perform classification
# 3. Extract Periodic Decelerations
#   A. Ignore UC where periodic decel not possible
#     a. UC overlapping Prolonged Decels
#     b. UC during periods of high FHR signal loss
#   B. Extract Uniform decel candidates
#   C. Perform preliminary classification of candidated (prior to association with UC)
#   D. Associated decels with UC (UC annotation)
#   E. Reclassify periodic decels once UC relationship established
#   F. Merge periodic and prolonged decelerations, giving preference to prolonged decels when overlap exists
# 4. Extract Episodic Decelerations
#   A. Extract Candidates
#   B. Prune Adjacent (TODO)
#   C. Perform classification
#   D. Merge with other decels, giving preference to prolonged/periodic when overlap exists
# 5. Extract Acccelerations
#   A. Extract Candidates
#   B. Prune Adjacent
#     a. Back-to-back accelerations
#     b. Shoulders for variable decelerations
#   D. Perform classification
#   E. Merge with other decels, giving preference to prolonged/periodic when overlap exists
#
# To Do:
# - Add accelerations
# - Process overlapping and adjacent decelerations
#   - including combining prolonged decel segments where appropriate




def summarizeDecels(allDecels, tStart=None, tEnd=None, exclude=[], filterHasUC=False, shouldPrint=True):
    """Print information about decels within specified time region"""
    found = False
    text = ''
    for decel in allDecels:
        if tStart and decel['tEnd'] < tStart:
            continue
        if tEnd and decel['tStart'] > tEnd:
            continue
        if decel['classification'] in exclude:
            continue

        if filterHasUC and 'uc_tAcme' not in decel:
            continue

        text += '@{:5.2f}m : {}\n'.format(
            decel['tNadir'], decel['classification'])

        text += '                   {:5.1f} bpm   dur: {:3.0f}s ({:3.1f}min)   mag: {:5.1f} bpm   valid: {:0.0f}%\n'.format(
            decel['relMag'],
            decel['duration'], decel['duration'] / 60.0,
            decel['mag'], decel['pctValid'] * 100.0)

        text += '                    tOnset: {:3.0f}s   tRelease: {:3.0f}s   span: {:5.2f} - {:5.2f} min\n'.format(
            decel['tOnset'], decel['tRelease'], decel['tStart'], decel['tEnd'])


        if ('time_under_15' in decel and 'time_under_50pct' in decel
            and decel['time_under_15'] is not None and decel['time_under_50pct'] is not None):
            text += '                    time below -15bpm: {:.1f} min   time below 50% drop: {:.1f} min'.format(
                decel['time_under_15'], decel['time_under_50pct'])
        if 'var' in decel and decel['var'] is not None:
            text += '                    variability: {:0.0f} bpm\n'.format(decel['var'])

        if 'uc_tAcme' in decel:
            text += '                    UC tAcme: {:5.2f}m   lag: {:3.0f}s\n'.format(
                decel['uc_tAcme'], decel['uc_lag'])
        found = True

    if shouldPrint:
        print text,
        return found
    else:
        return text



def extractAllDecels(fhr, mask, ts, allUC=[], allExtractorParams={}, includeAccelerations=True):
    """Top level extraction routine"""

    if len(fhr) == 0 or len(mask) == 0 or np.sum(mask) < 30:   # make sure we have data
        print 'extractAllDecels empty input data'
        return {}

    # Interpolate any masked values
    indices = np.arange(len(fhr))
    fhr = np.interp(indices, indices[mask], fhr[mask])

    var = computeVariability(fhr, allExtractorParams['freqVariability'])
    overallBaseline = []
    #
    # Extract Prolonged Decels
    #
    detailHR, smoothHR, baseline = extractFeatureSignals(fhr,
                                                         **allExtractorParams['prolongedDecelParams']['filterParams'])
    if len(baseline) > 0:
        candidateDecels = findProlongedDecelCandidates(detailHR, mask, smoothHR, baseline, ts, var)
        prolongedDecels = classifyAllDecels(candidateDecels, allExtractorParams['prolongedDecelParams']['classifiers'])
    else:
        prolongedDecels = []

    checkDecelOverlapAndAdjacent(prolongedDecels)

    # Ignore UC during prolonged decels
    selectedUC = ucIgnoreOverlapProlongedDecel(allUC, prolongedDecels)

    #
    # Extract Periodic Decels (Early Decels, Late Decels and Periodic Variable Decels)
    #
    detailHR, smoothHR, baseline = extractFeatureSignals(fhr, **allExtractorParams['uniformDecelParams']['filterParams'])
    _, candidateDecels = findUniformDecelCandidates(detailHR, mask, smoothHR, baseline, ts)

    uniformDecels = classifyAllDecels(candidateDecels, allExtractorParams['uniformDecelParams']['classifiers'],
                                      ignoreUnclassified=False)
    annotatedUC = associateDecelWithUC(uniformDecels, selectedUC, mask, ts)
    # perform final classification
    uniformDecels = classifyAllDecels(uniformDecels,
                                      allExtractorParams['uniformDecelParams']['reclassifiers'])
    reviseAnnotatedUC(annotatedUC, uniformDecels)
    allDecels = mergeDecels(prolongedDecels, uniformDecels)   # combine results

    #
    # Extract Episodic Decels (Variable Decels)
    #
    detailHR, smoothHR, baseline = extractFeatureSignals(fhr, **allExtractorParams['varDecelParams']['filterParams'])
    candidateDecels = findVarDecelCandidates(detailHR, mask, smoothHR, baseline, ts)
    varDecels = classifyAllDecels(candidateDecels, allExtractorParams['varDecelParams']['classifiers'])
    # checkDecelOverlapAndAdjacent(varDecels)
    allDecels = mergeDecels(allDecels, varDecels)

    #
    #  Accelerations
    #
    if includeAccelerations:
        allAccels = extractAccels(fhr, mask, ts, allDecels=allDecels,
                                  **allExtractorParams['accelParams'])
        allDecels = sorted(allDecels+allAccels, key=lambda x:x['tStart'])



    #
    # Variability and Baseline
    #

    # ignore regions with accelerations and decelerations
    revisedMask = maskIgnoreDecels(mask, allDecels)
    # variability is defined as < 2 CPM, so min period is 30 sec
    varSeg = varComputeSegments(var, revisedMask, ts, segSize=30, pctValid=0.8)
    overallBaseline, basalHR, minuteHR = summarizeHR(fhr, revisedMask, ts, freq=1.0/48)

    extractorResults = {'decels': allDecels, 'annotatedUC': annotatedUC, 'basalHR':basalHR, 'minuteHR':minuteHR,
                        'variability': var, 'varSeg':varSeg,
                        'baseline': overallBaseline, 'fastBaseline': baseline,
                        'smoothHR': smoothHR, 'detailHR': detailHR}

    return extractorResults


def extractFeatureSignals(fhr, fDetail=None, fSmooth=None, fBaselineInitial=None, fBaselineFinal=None):
    """Applies filters to compute feature signals -- smoothed and detail.  Also computes estimated
     baseline signal for class of decelerations being detected"""
    assert fDetail and fSmooth and fBaselineInitial and fBaselineFinal
    detailHR = filterSignal(fhr, fType='lowpass', freq=fDetail, useFiltFilt=True, order=4, fs_Hz=1.0)
    smoothHR = filterSignal(fhr, fType='lowpass', freq=fSmooth, useFiltFilt=True, order=4, fs_Hz=1.0)
    _, baseline = computeBaseline(fhr, filt_initial=fBaselineInitial, filt_final=fBaselineFinal)
    return detailHR, smoothHR, baseline


# convenience wrapper for standalone extractor testing purposes
def extractDecels(fhr, mask, ts, computeProlonged=False, classifiers=[], filterParams={}):
    """Convenience wrapper for standalone testing of episodic decel extractors (variable and prolonged)"""
    detailHR, smoothHR, baseline = extractFeatureSignals(fhr, **filterParams)

    var = computeVariability(fhr, freq=1.0 / 50)  # may be redundant

    if computeProlonged:
        candidateDecels = findProlongedDecelCandidates(detailHR, mask, smoothHR, baseline, ts, var)
    else:
        candidateDecels = findVarDecelCandidates(detailHR, mask, smoothHR, baseline, ts)

    allDecels = classifyAllDecels(candidateDecels, classifiers)
    checkDecelOverlapAndAdjacent(allDecels)

    return {'decels':allDecels, 'variability':var, 'baseline':baseline, 'smoothHR':smoothHR, 'detailHR':detailHR}


# convenience wrapper for standalone extractor testing purposes
def extractUniformDecels(fhr, mask, ts, allUC,
                         classifiers=[], reclassifiers=[], filterParams={}):
    """Convenience wrapper for standalone testing of periodic decel extractors
    (early, late and periodic variable)"""
    detailHR, smoothHR, baseline = extractFeatureSignals(fhr, **filterParams)
    var = computeVariability(fhr, freq=1.0 / 50)

    _, candidateDecels = findUniformDecelCandidates(detailHR, mask, smoothHR, baseline, ts)
    allDecels = classifyAllDecels(candidateDecels, classifiers, ignoreUnclassified=False)
    annotatedUC = associateDecelWithUC(allDecels, allUC, mask, ts)

    allDecels = classifyAllDecels(allDecels, reclassifiers)

    reviseAnnotatedUC(annotatedUC, allDecels)
    return {'decels': allDecels, 'annotatedUC': annotatedUC, 'variability':var,
            'baseline': baseline, 'smoothHR': smoothHR, 'detailHR': detailHR}


FILTER_CACHE = {}
def computeBaseline(sig, fs=1.0, filt_initial=1.0 / 4, filt_final=1.0 / 16,
                    order=1, tol=5, nPad=1000):
    """Compute baseline using two-step process
    1) apply initial higher frequency filter, then clip portions of signal > 5bpm from initial baseline estimate
    2) compute final baseline by apploying lower-frequency filter (4x) to this clipped signal

    initial filter: 0.25 cycles per minute (period = 4 min)
    final filter:   0.0625 cycles per minute (period = 16 min)
    """
    global FILTER_CACHE
    initial = str(filt_initial) + 'cpm'
    final = str(filt_final) + 'cpm'

    fNyquist = fs / 2.0
    hertzToCyclesPerMin = 1.0 / 60.0

    if initial not in FILTER_CACHE:
        freqInitial = hertzToCyclesPerMin * filt_initial
        FILTER_CACHE[initial] = signal.butter(order, freqInitial / fNyquist, 'lowpass')

    if final not in FILTER_CACHE:
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


def summarizeHR(sig, mask, ts, fs=1.0, freq=1.0 / 48, order=4, useFiltFilt=True,
                durationInSamples=60 * 10, minSamples=60):
    hertzToCyclesPerMin = 1.0 / 60.0
    freqHz = hertzToCyclesPerMin * freq

    # interpolate missing data
    indices = np.arange(len(mask))
    sig = np.interp(indices, indices[mask], sig[mask])

    minuteHR = []
    for iEnd in range(60, len(sig)-60, 60):
        iStart = iEnd - 60
        sigSeg = sig[iStart:iEnd]
        maskSeg = mask[iStart:iEnd]
        if np.sum(maskSeg) >= 40:
            segHR = np.median(sigSeg[maskSeg])
            minuteHR.append([segHR, ts[iEnd - 1]])
        else:
            minuteHR.append([None, ts[iEnd - 1]])

    basalHR = []
    for iEnd in range(60, len(sig), 60):
        iStart = max(0, iEnd - durationInSamples)

        sigSeg = sig[iStart:iEnd]
        maskSeg = mask[iStart:iEnd]
        if np.sum(maskSeg) >= minSamples:
            segHR = np.median(sigSeg[maskSeg])
            basalHR.append([segHR, ts[iEnd - 1]])
        else:
            basalHR.append([None, ts[iEnd - 1]])

    try:
        baseline = filterSignal(sig, fType='lowpass', freq=freqHz,
                                useFiltFilt=useFiltFilt, order=order, fs_Hz=fs)
        return baseline, basalHR, minuteHR
    except Exception, e:
        print 'exception during summarizeHR:', e
        return [], basalHR, minuteHR


def findVarDecelCandidates(sig, mask, sigSmoothed, baseline, ts, nadirWidth=5, includeEnd=True):
    """Find potential variable decelerations  """
    delta = sig - baseline
    deltaSmoothed5 = sigSmoothed - baseline + 5
    allRelease, allOnset = getCrossings(deltaSmoothed5)

    allEndpoints = [[i, 'onset'] for i in allOnset] + [[i, 'release'] for i in allRelease]
    allEndpoints = sorted(allEndpoints)

    if includeEnd and allEndpoints and allEndpoints[-1] != 'release':
        # create release at end of recording
        allEndpoints.append([len(sig) - 1, 'release'])

    results = []
    for i, entry in enumerate(allEndpoints):
        if entry[1] != 'release':
            continue
        if i == 0 or allEndpoints[i - 1][1] != 'onset':
            continue

        idxStart = allEndpoints[i - 1][0]
        idxEnd = entry[0]

        duration = (ts[idxEnd] - ts[idxStart]) * 60
        if duration < 10:
            continue

        # refine onset/release estimates using local slops
        slopeL = (sigSmoothed[idxStart] - sigSmoothed[idxStart + 5]) / 5.0
        slopeR = (sigSmoothed[idxEnd] - sigSmoothed[idxEnd - 5]) / 5.0
        if slopeL > 0:
            idxStart = max(idxStart - int(5.0 / slopeL), 0)
        if slopeR > 0:
            idxEnd = min(idxEnd + int(5.0 / slopeR), len(sig) - 1)

        startingBaseline = baseline[idxStart]

        # estimate magnitude based on triangle
        auc = np.sum(-delta[idxStart:idxEnd])
        triangleRatio = 2 * auc / (idxEnd - idxStart)

        pctValid = np.mean(mask[idxStart:idxEnd])

        idxNadir = np.argmin(sigSmoothed[idxStart:idxEnd]) + idxStart
        # find actual
        idxMin = np.argmin(sig[idxNadir - nadirWidth:idxNadir + nadirWidth]) + idxNadir - nadirWidth
        # idxMin = np.argmin(sig[idxStart:idxEnd]) + idxStart
        relMag = -delta[idxMin]
        mag = sig[idxMin]

        duration = (ts[idxEnd] - ts[idxStart]) * 60
        tOnset = (ts[idxNadir] - ts[idxStart]) * 60
        tRelease = (ts[idxEnd] - ts[idxNadir]) * 60

        decel = {'relMag': relMag, 'mag': mag, 'pctValid': pctValid, 'base': startingBaseline,
                 'duration': duration, 'tOnset': tOnset, 'tRelease': tRelease,
                 'idxNadir': idxNadir, 'idxStart': idxStart, 'idxEnd': idxEnd,
                 'tNadir': float(ts[idxNadir]), 'tStart': float(ts[idxStart]), 'tEnd': float(ts[idxEnd]),
                 'triangleRatio': triangleRatio}

        results.append(decel)

    return results


def findProlongedDecelCandidates(sig, mask, sigSmoothed, baseline, ts, var,
                                 minRelMag=15, minDuration=(2.5 * 60)):
    """Find potential prolonged decelerations"""

    delta = sig - baseline
    deltaSmoothed5 = sigSmoothed - baseline + 5
    allRelease, allOnset = getCrossings(deltaSmoothed5)

    results = []
    lastEnd = -1
    for idxStart in allOnset:
        if idxStart < lastEnd:  # overlap
            continue

        # use starting point as baseline
        i = np.argmax(sigSmoothed[idxStart:] > sigSmoothed[idxStart])
        if i == 0:
            idxEnd = len(sigSmoothed) - 1
        else:
            idxEnd = idxStart + i
        lastEnd = idxEnd

        duration = (ts[idxEnd] - ts[idxStart]) * 60
        if duration < minDuration:
            continue

        pctValid = np.mean(mask[idxStart:idxEnd])

        idxNadir = np.argmin(sigSmoothed[idxStart:idxEnd]) + idxStart
        startingBaseline = baseline[idxStart]

        mag = sigSmoothed[idxNadir]
        relMag = startingBaseline - mag

        if relMag < minRelMag:
            continue

        # Time under 15 bpm
        deltaT = ts[1] - ts[0]
        sigSmoothed[idxStart:idxEnd] < startingBaseline - 15
        time_under_15 = np.sum(sigSmoothed[idxStart:idxEnd] < startingBaseline - 15) * deltaT

        # time under 50% of relMag
        sigSmoothed[idxStart:idxEnd] < startingBaseline - 15
        time_under_50pct = np.sum(sigSmoothed[idxStart:idxEnd] < startingBaseline - 0.5 * relMag) * deltaT

        duration = (ts[idxEnd] - ts[idxStart]) * 60
        tOnset = (ts[idxNadir] - ts[idxStart]) * 60
        tRelease = (ts[idxEnd] - ts[idxNadir]) * 60

        segVar = computeSegmentVariability(idxStart, idxEnd, var, mask)

        decel = {'relMag': relMag, 'mag': mag, 'pctValid': pctValid, 'base': startingBaseline,
                 'duration': duration, 'tOnset': tOnset, 'tRelease': tRelease,
                 'idxNadir': idxNadir, 'idxStart': idxStart, 'idxEnd': idxEnd,
                 'tNadir': float(ts[idxNadir]), 'tStart': float(ts[idxStart]), 'tEnd': float(ts[idxEnd]),
                 'var': segVar, 'time_under_15': time_under_15, 'time_under_50pct': time_under_50pct}
        results.append(decel)

    return results


def classifyAllDecels(candidateDecels, classifiers, ignoreUnclassified=True):
    """Applies classification rules to a set of deceleration candidates
    by default prunes any candidate not conforming to a classification rule"""
    revisedDecels = []
    for decel in candidateDecels:
        found = False
        for classifier in classifiers:
            if classifier(decel):
                found = True
                break

        if found or not ignoreUnclassified:
            revisedDecels.append(decel)

    return revisedDecels


def classifyDecel(decel, classification='valid',
                  #minDuration=14, maxDuration=60 * 3, minMag=14, maxMag=None,
                  minDuration=None, maxDuration=None, minMag=None, maxMag=None,
                  minOnset=None, maxOnset=None,
                  minRelease=None, maxRelease=None,
                  minOnsetOrRelease=None,
                  minLag=None, maxLag=None,
                  #minPctValid=0.5, minOnsetRatio=None, maxOnsetRatio=0.6,
                  minPctValid=None, minOnsetRatio=None, maxOnsetRatio=None,
                  time_under_15=None, time_under_50pct=None,
                  showDetail=False):
    if minDuration is not None and decel['duration'] < minDuration:
        return False

    if maxDuration is not None and decel['duration'] > maxDuration:
        return False

    if minOnset is not None and decel['tOnset'] < minOnset:
        return False

    if maxOnset is not None and decel['tOnset'] > maxOnset:
        return False

    if minRelease is not None and decel['tRelease'] < minRelease:
        return False

    if maxRelease is not None and decel['tRelease'] > maxRelease:
        return False

    if minOnsetOrRelease is not None and max(decel['tOnset'], decel['tRelease']) < minOnsetOrRelease:
        return False

    if minMag is not None and decel['relMag'] < minMag:
        return False

    if maxMag is not None and decel['relMag'] > maxMag:
        return False

    if minLag is not None:
        if 'uc_lag' not in decel or decel['uc_lag'] < minLag:
            return

    if maxLag is not None:
        if 'uc_lag' not in decel or decel['uc_lag'] > maxLag:
            return False

    if minPctValid is not None and decel['pctValid'] < minPctValid:
        return False


    if time_under_15 is not None and decel['time_under_15'] < time_under_15:
        if showDetail:
            print 'rejected due to time_under_15', decel['time_under_15']
            # pprint(decel)
        return False

    if time_under_50pct is not None and decel['time_under_50pct'] < time_under_50pct:
        if showDetail:
            print 'rejected due to time_under_15', decel['time_under_50pct']
            # pprint(decel)
        return False


    if 'triangleRatio' in decel and decel['triangleRatio'] is not None and decel['triangleRatio'] < minMag:
        if showDetail:
            print 'rejected due to triangleRatio'
            pprint(decel)
        return False

    if minOnsetRatio or maxOnsetRatio:
        onsetRatio = decel['tOnset'] / decel['duration']
        if maxOnsetRatio is not None and onsetRatio > maxOnsetRatio:  # skewed
            if showDetail:
                print 'rejected due to maxOnsetRatio'
                pprint(decel)
            return False

        if minOnsetRatio is not None and onsetRatio < minOnsetRatio:  # skewed
            if showDetail:
                print 'rejected due to minOnsetRatio'
                pprint(decel)
            return False

    decel['classification'] = classification
    return True


# def computeAnnotations(sigHR, mask, ts,
#                        validParams={'classification': 'valid',
#                                     'minDuration': 14, 'maxDuration': 60 * 3,
#                                     'minMag': 14, 'minPctValid': 0.5, 'maxOnsetRatio': 0.6},
#                        borderlineParams={'classification': 'borderline',
#                                          'minDuration': 12, 'maxDuration': 60 * 3,
#                                          'minMag': 12, 'minPctValid': 0.5, 'maxOnsetRatio': 0.7},
#                        fVar=1.0 / 50):
#     # interpolate any missing datapoints
#     indices = np.arange(len(sigHR))
#     sigHR = np.interp(indices, indices[mask], sigHR[mask])
#
#     _, baseline = computeBaseline(sigHR)
#     _, localBaseline = computeBaseline(sigHR, filt_initial=1.0 / 2, filt_final=1.0 / 6)
#
#     detailHR = filterSignal(sigHR, fType='lowpass', freq=1.0 / 6, useFiltFilt=True, order=4, fs_Hz=1.0)
#     smoothHR = filterSignal(sigHR, fType='lowpass', freq=1.0 / 18, useFiltFilt=True, order=4, fs_Hz=1.0)
#
#     classifiers = [lambda x: classifyDecel(x, **validParams),
#                    lambda x: classifyDecel(x, **borderlineParams)]
#     allDecels = findDecel(detailHR, mask, smoothHR, localBaseline, ts, classifiers=classifiers)
#     if len(allDecels) == 0:
#         print 'NO DECELS FOUND'
#         # continue
#
#     variability = computeVariability(sigHR, freq=fVar)
#
#     return baseline, allDecels, sigHR - baseline, sigHR - localBaseline, variability


def maskIgnoreDecels(mask, allDecels, extend_points=10):
    # ignore regions with accelerations and decelerations
    revisedMask = np.copy(mask)
    for decel in allDecels:
        idxStart = max(0, decel['idxStart'] - extend_points)
        idxEnd = min(len(mask), decel['idxEnd'] + extend_points)
        revisedMask[idxStart:idxEnd] = False

    return revisedMask


def computeVariability(sig, freq=1.7 / 60, order=4,):
    # freq set near 2 CPM
    var = filterSignal(sig, fType='highpass', freq=freq, useFiltFilt=True, order=order, fs_Hz=1.0)
    return var


def computeSegmentVariability(idxStart, idxEnd, var, mask, segSize=30, ignore=10, pctValid=0.8):
    # variability is defined as < 2 CPM, so min period is 30 sec
    # source: http://perinatology.com/Fetal%20Monitoring/Intrapartum%20Monitoring.htm
    minValid = segSize * pctValid
    allSegmentVariability = []
    for i in range(idxStart + ignore, idxEnd - segSize - ignore, segSize):
        var[i:i + segSize]
        maxVal = np.max(var[i:i + segSize])
        minVal = np.min(var[i:i + segSize])
        valid = np.sum(mask[i:i + segSize])
        if valid >= minValid:
            allSegmentVariability.append(maxVal - minVal)

    if len(allSegmentVariability) > 2:
        return np.median(allSegmentVariability)
    else:
        return -1


def varComputeSegments(var, mask, ts, segSize=30, pctValid=0.8):
    minValid = segSize * pctValid
    allSegmentVariability = []
    for i in range(0, len(var) - segSize+1, segSize):
        var[i:i + segSize]
        maxVal = np.max(var[i:i + segSize])
        minVal = np.min(var[i:i + segSize])
        valid = np.sum(mask[i:i + segSize])
        if valid >= minValid:
            allSegmentVariability.append([ts[i + segSize-1], maxVal - minVal])

    return allSegmentVariability


def checkDecelOverlapAndAdjacent(allDecels, minSpacing=20):
    for i, decel in enumerate(allDecels):
        if i == 0:
            continue

        spacing = (decel['tStart'] - allDecels[i - 1]['tEnd']) * 60

        if spacing < 0:
            print '** Overlapping Decels @ {:0.1f} and {:0.1f}'.format(
                allDecels[i - 1]['tNadir'], decel['tNadir'])
        elif spacing < minSpacing:
            print '** Adjacent Decels @ {:0.1f} and {:0.1f}  spacing {:0.1f} sec'.format(
                allDecels[i - 1]['tNadir'], decel['tNadir'], spacing)


def isOverlapDecel(decelList, newDecel):
    """Determine if decel overlaps with any existing decel"""
    foundOverlap = False
    for decel in decelList:
        if (decel['tEnd'] < newDecel['tStart']) or (newDecel['tEnd'] < decel['tStart']):
            continue
        foundOverlap = True
        break

    return foundOverlap


def mergeDecels(existingDecels, newDecels):
    """Combines new decels with existing decels provided that
    new decels do not overlap with existing decels"""

    if len(existingDecels) == 0:
        return newDecels

    if len(newDecels) == 0:
        return existingDecels

    filtderedDecels = []
    for decel in newDecels:
        if not isOverlapDecel(existingDecels, decel):
            filtderedDecels.append(decel)

    combinedDecels = existingDecels + filtderedDecels
    combinedDecels = sorted(combinedDecels, key=lambda x: x['tStart'])
    return combinedDecels


def findUniformDecelCandidates(sig, mask, sigSmoothed, baseline, ts,
                               threshBase=-1, minChange=5,
                               threshDeriv=1.0,  # 0.5
                               threshDeriv2=0.125,  # 0.25
                               ):
    deriv = np.diff(sigSmoothed)
    delta = sigSmoothed - baseline

    allMin, allMax = getCrossings(deriv)
    allPoints = [[i, 'max'] for i in allMax if delta[i] > threshBase]
    allPoints += [[i, 'min'] for i in allMin if delta[i] <= threshBase]

    _, allEnd = getCrossings(deriv - threshDeriv)
    allPoints += [[i, 'end'] for i in allEnd if delta[i] >= -minChange]

    _, allStart = getCrossings(deriv + threshDeriv)
    allPoints += [[i, 'start'] for i in allStart if delta[i] >= -minChange]

    if threshDeriv2:
        _, allEnd = getCrossings(deriv - threshDeriv2)
        allPoints += [[i, 'end'] for i in allEnd if delta[i] >= -minChange]

        _, allStart = getCrossings(deriv + threshDeriv2)
        allPoints += [[i, 'start'] for i in allStart if delta[i] >= -minChange]

    allPoints = sorted(allPoints)

    allPoints = pruneMinima(allPoints, sigSmoothed)
    allPoints = pruneEndpoints(allPoints, sigSmoothed)

    allDecels = identifyUniformDecel(allPoints, sigSmoothed, baseline, ts, mask)

    return allPoints, allDecels


def pruneEndpoints(allPoints, sig):
    newPoints = []
    for i, entry in enumerate(allPoints):
        if i == 0 or entry[1] in ['min', 'max']:
            newPoints.append(entry)
        elif entry[1] == 'end' and newPoints[-1][1] == 'start':
            # ignore - missing minima
            pass
        elif entry[1] == 'start' and newPoints[-1][1] == 'start':
            # adjacent starts, keep most recent
            newPoints = newPoints[:-1]
            newPoints.append(entry)
        elif entry[1] == 'end' and newPoints[-1][1] == 'end':
            # deplicate ends, ignore most recent
            pass
        else:
            newPoints.append(entry)

    return newPoints


def pruneMinima(allPoints, sig):
    newPoints = []
    lastMinima = -1
    lastMaxima = -1
    for i, entry in enumerate(allPoints):
        if entry[1] == 'min':
            if lastMinima == -1 or lastMaxima == -1 or lastMaxima > lastMinima:
                lastMinima = len(newPoints)
                newPoints.append(entry)
            else:
                idxThis = entry[0]
                idxLast = newPoints[lastMinima][0]
                if sig[idxThis] < sig[idxLast]:
                    # replace prior minima and everything in between
                    # print 'replacing minima'
                    newPoints = newPoints[:lastMinima]
                    lastMinima = len(newPoints)
                    newPoints.append(entry)
                else:
                    # ignore this minima
                    # print 'ignoring minima'
                    pass

        elif entry[1] == 'max':
            lastMaxima = len(newPoints)
            newPoints.append(entry)
        else:
            newPoints.append(entry)
    return newPoints


def identifyUniformDecel(allPoints, sig, baseline, ts, mask, verbose=False):
    delta = sig - baseline
    allDecels = []
    for i, entry in enumerate(allPoints):
        if entry[1] != 'min':
            continue

        idxNadir = entry[0]
        tNadir = ts[idxNadir]

        if i == 0 or allPoints[i - 1][1] != 'start':
            # print '{:0.2f}: Missing Start'.format(tNadir)
            continue

        idxStart = allPoints[i - 1][0]
        fall = sig[idxStart] - sig[idxNadir]
        change = fall

        if i == len(allPoints) - 1:
            idxEnd = len(sig) - 1
            rise = baseline[idxNadir] - sig[idxNadir]
        elif allPoints[i + 1][1] != 'end':
            # print '{:0.2f}: Missing End'.format(tNadir)
            continue
        else:
            idxEnd = allPoints[i + 1][0]
            rise = sig[idxEnd] - sig[idxNadir]
            change = min(fall, rise)

        tStart = ts[idxStart]
        tEnd = ts[idxEnd]
        duration = (tEnd - tStart) * 60
        tOnset = (tNadir - tStart) * 60
        tRelease = (tEnd - tNadir) * 60
        pctValid = np.mean(mask[idxStart:idxEnd])

        localBaseline = min(sig[idxStart], sig[idxEnd])

        if verbose:
            print '{:0.2f}: Decel  Change: {:0.1f}  Rise: {:0.1f}  Fall: {:0.1f}'.format(
                tNadir, change, rise, fall)
            print '     Start: {:0.2f}  End: {:0.2f}  Duration: {:0.0f}  Onset: {:0.0f}  Release: {:0.0f}'.format(
                tStart, tEnd, duration, tOnset, tRelease)
            print

        decel = {'relMag': change, 'mag': sig[idxNadir], 'pctValid': pctValid,
                 'duration': duration, 'tOnset': tOnset, 'tRelease': tRelease,
                 'idxNadir': idxNadir, 'idxStart': idxStart, 'idxEnd': idxEnd,
                 'tNadir': float(tNadir), 'tStart': float(tStart), 'tEnd': float(tEnd),
                 'classification': 'unspecified', 'base': localBaseline,
                 'triangleRatio': None,  # triangleRatio
                 }
        allDecels.append(decel)

    return allDecels


def associateDecelWithUC(allDecels, allUC, valid, ts,
                         includeDecel=[], excludeDecel=[],
                         maxLeadSec=5, maxLagSec=60, maxAcmeToOnsetSec=10, verbose=False):
    # Filter decels first according to inclusion and exclusion criteria
    if includeDecel:
        allDecels = [d for d in allDecels if d['classification'] in includeDecel]

    if excludeDecel:
        allDecels = [d for d in allDecels if d['classification'] not in excludeDecel]

    features = sorted([[decel['tNadir'], 'decel', decel] for decel in allDecels]
                      + [[t, 'uc'] for t in allUC])

    annotatedUC = []
    for i in range(len(features)):
        # Find closest decel to each UC
        if features[i][1] == 'decel':
            continue
        tAcmeUC = features[i][0]

        tLead = None
        if i > 0 and features[i - 1][1] == 'decel':
            # UC Acme must be between Decel onset and release
            decelBefore = features[i - 1][2]
            if tAcmeUC > decelBefore['tStart'] and tAcmeUC < decelBefore['tEnd']:
                tLead = (tAcmeUC - decelBefore['tNadir']) * 60
                if tLead > maxLeadSec:
                    tLead = None

        tLag = None
        if i < len(features) - 2 and features[i + 1][1] == 'decel':
            decelAfter = features[i + 1][2]
            tLag = (decelAfter['tNadir'] - tAcmeUC) * 60
            if tLag > maxLagSec:
                # use secondary criteria decel onset near decel tAcme
                spacing = (decelAfter['tStart'] - tAcmeUC) * 60
                if spacing > maxAcmeToOnsetSec:
                    tLag = None

        if tLead and tLag:
            if tLead < tLag:
                annotatedUC.append({'tAcme': tAcmeUC, 'decel': decelBefore, 'lag': -tLead})
            else:
                annotatedUC.append({'tAcme': tAcmeUC, 'decel': decelAfter, 'lag': tLag})
            if verbose:
                print 'UC @ {:0.2f}  selecting between lead:  {:0.0f}  and lag:  {:0.0f}'.format(
                    tAcmeUC, tLead, tLag)

        elif tLead:
            annotatedUC.append({'tAcme': tAcmeUC, 'decel': decelBefore, 'lag': -tLead})
            if verbose:
                print 'UC @ {:0.2f}  selected lead:  {:0.0f}'.format(
                    tAcmeUC, tLead)
        elif tLag:
            annotatedUC.append({'tAcme': tAcmeUC, 'decel': decelAfter, 'lag': tLag})
            if verbose:
                print 'UC @ {:0.2f}  selected lag:  {:0.0f}'.format(
                    tAcmeUC, tLag)
        else:
            annotatedUC.append({'tAcme': tAcmeUC, 'decel': None, 'lag': None})

    # Annotate Decelerations with UC when present
    for entry in annotatedUC:
        decel = entry['decel']
        if decel:
            decel['uc_tAcme'] = entry['tAcme']
            decel['uc_lag'] = entry['lag']

    ucVerifyValidFHR(annotatedUC, valid, ts)

    return annotatedUC


def ucVerifyValidFHR(annotatedUC, valid, ts, beforeMin=30.0/60, afterMin=90/60.0, verbose=False):
    for entry in annotatedUC:
        if entry['decel']:
            continue
        tAcme = entry['tAcme']
        mask = np.logical_and(ts > tAcme-beforeMin, ts < tAcme+afterMin)
        pctValid = np.mean(valid[mask])
        entry['pctValidFHR'] = pctValid
        if verbose:
            print '{:0.2f}: pctValidFHR: {:0.1f}%'.format(tAcme, pctValid*100)


def reviseAnnotatedUC(annotatedUC, allDecels, verbose=False):
    """Remove annotations when decel no longer present"""
    for entry in annotatedUC:
        if entry['decel'] and entry['decel'] not in allDecels:
            if verbose:
                print 'ignoring annotation for decel', entry['decel']['classification']
            entry['decel'] = None
            entry['lag'] = None


def ucIgnoreOverlapProlongedDecel(allUC, allDecels, beforeMin=30.0 / 60, afterMin=30 / 60.0, verbose=True):
    """Ignores contractions that overlap prolonged decelerations"""
    selectedUC = []
    for tAcme in allUC:
        found = False
        for decel in allDecels:
            if tAcme - beforeMin > decel['tStart'] and tAcme + afterMin < decel['tEnd']:
                found = True
                if verbose:
                    print '{:0.2f}: Ignoring UC overlapping Prolonged Decel {:0.2f}-{:0.2f}'.format(
                        tAcme, decel['tStart'], decel['tEnd'])
                break
        if not found:
            selectedUC.append(tAcme)

    return selectedUC


def extractAccels(fhr, mask, ts, allDecels=[],
                  classifiers=[], filterParams={}):
    """Convenience wrapper for standalone testing of accel extractor"""
    detailHR, smoothHR, baseline = extractFeatureSignals(fhr, **filterParams)

    candidateAccels = findAccelCandidates(detailHR, mask, smoothHR, baseline, ts)
    allAccels = classifyAllDecels(candidateAccels, classifiers)

    allAccels = filterAccelerations(allAccels, allDecels)

    #
    checkDecelOverlapAndAdjacent(allAccels)

    return allAccels


def findAccelCandidates(sig, mask, sigSmoothed, baseline, ts, classifiers=[], peakWidth=5, includeEnd=True,
                        verbose=True):
    """Find accelerations"""

    delta = sig - baseline
    deltaSmoothed5 = sigSmoothed - baseline - 5
    allRelease, allOnset = getCrossings(-deltaSmoothed5)

    allEndpoints = [[i, 'onset'] for i in allOnset] + [[i, 'release'] for i in allRelease]
    allEndpoints = sorted(allEndpoints)

    if includeEnd and allEndpoints and allEndpoints[-1] != 'release':
        # create release at end of recording
        allEndpoints.append([len(sig) - 1, 'release'])

    results = []
    for i, entry in enumerate(allEndpoints):
        if entry[1] != 'release':
            continue
        if i == 0 or allEndpoints[i - 1][1] != 'onset':
            continue

        idxStart = allEndpoints[i - 1][0]
        idxEnd = entry[0]

        duration = (ts[idxEnd] - ts[idxStart]) * 60
        if duration < 10:
            continue

        pctValid = np.mean(mask[idxStart:idxEnd])

        idxPeak = np.argmax(sigSmoothed[idxStart:idxEnd]) + idxStart
        # find actual
        idxPeak = np.argmax(sig[idxPeak - peakWidth:idxPeak + peakWidth]) + idxPeak - peakWidth
        # idxMin = np.argmin(sig[idxStart:idxEnd]) + idxStart
        relMag = delta[idxPeak]
        mag = sig[idxPeak]

        duration = (ts[idxEnd] - ts[idxStart]) * 60
        tOnset = (ts[idxPeak] - ts[idxStart]) * 60
        tRelease = (ts[idxEnd] - ts[idxPeak]) * 60

        decel = {'relMag': relMag, 'mag': mag, 'pctValid': pctValid,
                 'duration': duration, 'tOnset': tOnset, 'tRelease': tRelease,
                 'idxNadir': idxPeak, 'idxStart': idxStart, 'idxEnd': idxEnd,
                 'tNadir': float(ts[idxPeak]), 'tStart': float(ts[idxStart]), 'tEnd': float(ts[idxEnd]),
                 'triangleRatio': None}

        results.append(decel)
    return results


def filterAccelerations(allAccels, allDecels, margin=0.75):
    results = []
    for accel in allAccels:
        aStart = accel['tStart']
        aEnd = accel['tEnd']
        found = False
        for decel in allDecels:
            # expand decel start and end to incorporate margin
            # (nominally to cover primary and secondary decels)
            dStart = decel['tStart'] - margin
            dEnd = decel['tEnd'] + margin

            if aStart <= dStart and dStart <= aEnd:
                found = True
                break

            if dStart <= aStart and aStart <= dEnd:
                found = True
                break

        if not found:
            results.append(accel)

    return results
