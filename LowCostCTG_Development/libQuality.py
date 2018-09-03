# coding: utf-8

#
#  Copyright Douglas Williams, 2018
#  All Rights Reserved
#


import numpy as np
from matplotlib import pyplot as plt
try:
    from test_harness import addGrids
except Exception:
    pass

def showStats(stats):
    print 'medIBI: {:0.1f}  madIBI: {:0.1f}  meanIBI: {:0.1f}  stdIBI: {:0.1f}  pctValid: {:0.1f}%'.format(
        stats['medIBI'], stats['madIBI'], stats['meanIBI'], stats['stdIBI'], stats['pctValid'])

def getStats(valid, sigIBI, verbose=False):
    allValidIBI = sigIBI[valid]
    medIBI = np.median(allValidIBI)
    madIBI = np.median(np.abs(allValidIBI - medIBI))
    meanIBI = np.mean(allValidIBI)
    stdIBI = np.std(allValidIBI)
    pctValid = np.mean(valid)

    stats = {'medIBI':medIBI, 'madIBI':madIBI,
             'meanIBI':meanIBI, 'stdIBI':stdIBI,
             'pctValid':100 * pctValid}

    if verbose:
        showStats(stats)

    return medIBI, madIBI, pctValid, stats


class ErrorDetector:
    def __init__(self,
                 w=15,  # analysis window size idx-w to idx+w
                 minValid=5,  # minimum valid samples per window
                 sigma=5.0,  # MAD scake factor
                 minMAD=5.0,
                 maxMAD=13.0,
                 filterDensity=True,  # applies final sample density filter
                 showPlots=False):

        self.w = w
        self.minValid = minValid
        self.sigma = sigma
        self.minMAD = minMAD
        self.maxMAD = maxMAD
        self.filterDensity = filterDensity
        self.showPlots = showPlots

        self.allMedians = []
        self.new_valid = np.array([])
        self.last_end = None

    def applyLocalErrorDetection(self,
                                 valid,  # Input valid Mask
                                 sig,
                                 sigHR=None,  # used for plotting only
                                 ts=None,  # used for plotting
                                 offsetStart=None,  # limit range of analysis
                                 offsetEnd=None,  # limit range of analysis
                                 ):

        if len(valid) < 2*self.w:  # make sure sufficient data for analysis
            return valid

        # define analysis range
        if offsetStart is None:
            if self.last_end is None:
                offsetStart = 0  # start at beginning
            else:
                offsetStart = max(0, self.last_end - self.w)  # redo previous w points
        if offsetEnd is None:  # default is to process until end of signal
            offsetEnd = len(sig)
        self.last_end = offsetEnd  # remember for next time

        # extend valid mask as needed (used by incremental analysis)
        if len(self.new_valid) == 0:
            self.new_valid = np.copy(valid)
        else:
            idx = min(len(self.new_valid), offsetStart)
            self.new_valid = np.concatenate([self.new_valid[:idx], np.copy(valid[idx:])])

        # analyze selected points
        for i in range(offsetStart, offsetEnd):
            if valid[i] == 0:
                self.new_valid[i] = 0
                continue

            # adjust segment starting and ending range to address boundary conditions
            if i < self.w:
                iStart = 0
                iEnd = 2 * self.w
            elif i + self.w > len(sig):
                iStart = len(sig) - 2 * self.w
                iEnd = len(sig)
            else:
                iStart = i - self.w
                iEnd = i + self.w

            idx = np.arange(iStart, iEnd)
            seg = sig[iStart:iEnd]
            v = valid[iStart:iEnd]

            if np.sum(v) < self.minValid:  # discard point if insufficient valid neighnoring points
                self.new_valid[i] = 0
                continue

            allValidValues = seg[v]
            allValidIdx = idx[v]

            # Approximate this point using least squares fitting
            A = np.vstack([allValidIdx, np.ones(len(allValidIdx))]).T
            m, c = np.linalg.lstsq(A, allValidValues)[0]
            est = m * allValidIdx + c
            delta = allValidValues - est
            estThis = m * i + c

            # determine if actual value within expected range of estimate
            mad = np.median(np.abs(delta))
            mad = min(max(mad, self.minMAD), self.maxMAD)
            err = self.sigma * mad
            if sig[i] > estThis + err or sig[i] < estThis - err:
                self.new_valid[i] = 0

            if self.showPlots:  # remember error range for debug plots
                self.allMedians.append([ts[i], estThis, estThis + err, estThis - err])

        if self.showPlots:
            self.plotResults(sig, sigHR, ts, valid, self.new_valid)

        if self.filterDensity:  # reapply valid point density criteria
            for i in range(offsetStart, offsetEnd):
                if self.new_valid[i] == 0:
                    continue

                # adjust segment starting and ending range to address boundary conditions
                if i < self.w:
                    iStart = 0
                    iEnd = 2 * self.w
                elif i + self.w > len(sig):
                    iStart = len(sig) - 2 * self.w
                    iEnd = len(sig)
                else:
                    iStart = i - self.w
                    iEnd = i + self.w

                v = self.new_valid[iStart:iEnd]

                if np.sum(v) < self.minValid:  # discard point if insufficient valid neighnoring points
                    self.new_valid[i] = 0
                    continue

        return self.getValid()

    def getValid(self):
        return self.new_valid

    def plotResults(self, sig, sigHR, ts, valid, new_valid):
        plt.figure(figsize=(15, 2.5))
        plt.title('Local Estimate and Error Bands')
        plt.scatter([x[0] for x in self.allMedians], [x[1] for x in self.allMedians], s=0.5, c='g')
        plt.scatter([x[0] for x in self.allMedians], [x[2] for x in self.allMedians], s=0.5, c='r')
        plt.scatter([x[0] for x in self.allMedians], [x[3] for x in self.allMedians], s=0.5, c='r')
        plt.scatter(ts[valid], sig[valid], s=2, c='k')
        # addGrids(ts[-1])
        plt.ylabel('IBI')
        plt.xlabel('time in sec')
        # plt.ylim(50, 200)
        plt.xlim(0, max(600, ts[-1]))
        plt.show()

        outliers = np.logical_and(valid, ~new_valid)
        plt.figure(figsize=(15, 4))
        plt.title('After Local Filtering (outliers in red)')
        plt.scatter(ts[new_valid], sigHR[new_valid], s=2, c='k')
        plt.scatter(ts[outliers], sigHR[outliers], s=5, c='r')
        addGrids(ts[-1])
        plt.ylabel('HR')
        plt.xlabel('time in sec')
        plt.ylim(50, 200)
        plt.xlim(0, max(600, ts[-1]))
        plt.show()


# Wrappers for testing

def applyErrorDetectorIncremental(valid,  # Input valid Mask
                                  sig,
                                  sigHR=None,  # used for plotting only
                                  ts=None,  # used for plotting
                                  **kwargs):
    ed = ErrorDetector(**kwargs)

    for i in range(60, len(sig), 60):
        if isinstance(sigHR, type(None)) or isinstance(ts, type(None)):
            new_valid = ed.applyLocalErrorDetection(valid[:i], sig[:i])
        else:
            new_valid = ed.applyLocalErrorDetection(valid[:i], sig[:i], sigHR[:i], ts[:i])

    new_valid = ed.applyLocalErrorDetection(valid, sig, sigHR, ts)
    return new_valid


def applyErrorDetector(valid,  # Input valid Mask
                       sig,
                       sigHR=None,  # used for plotting only
                       ts=None,  # used for plotting
                       **kwargs):
    ed = ErrorDetector(**kwargs)
    new_valid = ed.applyLocalErrorDetection(valid, sig, sigHR, ts)
    return new_valid


# Legacy Wrapper - has different parameter orderings
def applyLocalErrorDetection(sig, sigHR, ts, valid,
                             **kwargs):
    ed = ErrorDetector(**kwargs)
    new_valid = ed.applyLocalErrorDetection(valid, sig, sigHR, ts)
    return new_valid


#
# --------------------------------------------------------------------------------------
#


# No longer used
def applyGlobalErrorDetection(valid, sigIBI, sigHR, pos,
                              threshold=15, threshMed=1.7, spacing=1, showPlots=False, verbose=False):

    medIBI, madIBI, pctValid, _ = getStats(valid, sigIBI, verbose)

    # filter extreme values
    valid[sigIBI > medIBI * threshMed] = 0
    valid[sigIBI < medIBI / threshMed] = 0

    # filter extreme changes -- compute differences
    validTransition = np.logical_and(valid[:-spacing], valid[spacing:])
    delta = sigIBI[spacing:] - sigIBI[:-spacing]
    validDelta = delta[validTransition]

    # compute stats -- for reporting only
    madDelta = np.median(np.abs(validDelta))
    stdDelta = np.std(validDelta)
    pctOutlier = np.mean(np.abs(validDelta) > threshold)

    # discard samples unless has at least 1 valid transition within limits
    validTransition = np.logical_and(validTransition, np.abs(delta) < threshold)
    revisedValid = np.zeros(len(valid))
    revisedValid[:-spacing][validTransition] = 1
    revisedValid[spacing:][validTransition] = 1
    revisedValid = np.logical_and(revisedValid, valid)

    if verbose:
        print 'madDelta: {:0.1f}  stdDelta: {:0.1f}  threshold: {:0.1f}   pctOutlier: {:0.1f}%  pctValid: {:0.1f}%'.format(
            madDelta, stdDelta, threshold, pctOutlier * 100.0, np.mean(revisedValid)*100)
        print

    if showPlots:
        outliers = np.logical_and(valid, ~revisedValid)
        plt.figure(figsize=(15, 4))
        plt.title('After Global Filtering (outliers in red)')
        #plt.scatter(pos, sigHR, s=0.5, c='r')
        plt.scatter(pos[outliers], sigHR[outliers], s=5, c='r')
        plt.scatter(pos[revisedValid], sigHR[revisedValid], s=2, c='k')
        addGrids(pos[-1])
        plt.ylabel('hr')
        plt.xlabel('time in sec')
        plt.ylim(50, 200)
        plt.xlim(0, max(600, pos[-1]))
        plt.show()

    return revisedValid


def OBSOLETE_applyLocalErrorDetection(sig, sigHR, ts, valid,
                             w=15, minValid=5, sigma=5.0,
                             minMAD=5.0, maxMAD=13.0, showPlots=False, verbose=False):
    allMedians = []
    new_valid = np.copy(valid)

    for i in range(0, len(sig)):
        if valid[i] == 0:
            new_valid[i] = 0
            continue

        if i < w:
            iStart = 0
            iEnd = 2*w
        elif i+ w > len(sig):
            iStart = len(sig)-2*w
            iEnd = len(sig)
        else:
            iStart = i-w
            iEnd = i+w

        idx = np.arange(iStart, iEnd)
        seg = sig[iStart:iEnd]
        v = valid[iStart:iEnd]

        if np.sum(v) < minValid:
            new_valid[i] = 0
            continue

        allValidValues = seg[v]
        allValidIdx = idx[v]

        # per example: https://docs.scipy.org/doc/numpy/reference/generated/numpy.linalg.lstsq.html#numpy.linalg.lstsq
        A = np.vstack([allValidIdx, np.ones(len(allValidIdx))]).T
        m, c = np.linalg.lstsq(A, allValidValues)[0]
        est = m * allValidIdx + c
        delta = allValidValues-est

        estThis = m * i + c

        madH = np.median(delta[delta>0])
        madL = -np.median(delta[delta<0])

        mad = np.median(np.abs(delta))
        madH = mad
        madL = mad

        madH = min(max(madH, minMAD), maxMAD)
        madL = min(max(madL, minMAD), maxMAD)

        allMedians.append([ts[i], estThis, estThis+sigma*madH, estThis-sigma*madL])

        if sig[i] > estThis+sigma*madH or sig[i] < estThis-sigma*madL:
            new_valid[i] = 0

        if False:
            validDiff = np.logical_and(v[:-1], v[1:])
            allValidDiff = np.diff(seg)[validDiff]

            madDiff = np.median(np.abs(allValidDiff))

    if showPlots:
        plt.figure(figsize=(15, 2.5))
        plt.title('Local Estimate and Error Bands')
        plt.scatter([x[0] for x in allMedians], [x[1] for x in allMedians],s=0.5, c='g')
        plt.scatter([x[0] for x in allMedians], [x[2] for x in allMedians],s=0.5, c='r')
        plt.scatter([x[0] for x in allMedians], [x[3] for x in allMedians],s=0.5, c='r')
        plt.scatter(ts[valid], sig[valid], s=2, c='k')
        #addGrids(ts[-1])
        plt.ylabel('IBI')
        plt.xlabel('time in sec')
        #plt.ylim(50, 200)
        plt.xlim(0, max(600, ts[-1]))
        plt.show()


    if showPlots:
        outliers = np.logical_and(valid, ~new_valid)
        plt.figure(figsize=(15, 4))
        plt.title('After Local Filtering (outliers in red)')
        plt.scatter(ts[new_valid], sigHR[new_valid], s=2, c='k')
        plt.scatter(ts[outliers], sigHR[outliers], s=5, c='r')
        addGrids(ts[-1])
        plt.ylabel('HR')
        plt.xlabel('time in sec')
        plt.ylim(50, 200)
        plt.xlim(0, max(600, ts[-1]))
        plt.show()

    return new_valid
