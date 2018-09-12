# coding: utf-8

#
#  Copyright Douglas Williams, 2018
#  All Rights Reserved
#

# 
# TocoPatch Detect UC
#

import numpy as np
import scipy.signal
try:
    from matplotlib import pyplot as plt
except Exception:
    pass

from libSignalProcessing import filterSignal, getCrossings


def physionetExtractUC(filtUC, ts, includeUC=False):
    """UC Extractor tuned for physionet CTG recordings"""

    idxUC, _ = findUC(filtUC, ts)
    idxUC, normUC = normalizeUC(idxUC, filtUC, includeUC=True)
    allUC = [ts[i] for i in idxUC]
    if includeUC:
        return allUC, normUC
    else:
        return allUC


# May not be used
def teager(x):
    return np.abs(x[1:-1] ** 2 - x[:-2] * x[2:])


def compressSig(sig, ts, fs):
    """Compress signal using percentile value"""
    sigF = filterSignal(np.abs(sig), fType='lowpass', freq=0.25, 
                        useFiltFilt=True, order=4, fs_Hz=fs)  
    
    # recode signal based on percentile
    values = [[sigF[i], i] for i in range(len(sig))]
    values = [ i for _, i in sorted(values)]
    
    newSig = np.zeros(len(sig))
    for i, idx in enumerate(values):
        newSig[idx] = i
    
    newSig = newSig - len(newSig)/2
    newSig[newSig<0] = 0  
    
    newSig2 = filterSignal(newSig, fType='lowpass', freq=1.0/90,
                            useFiltFilt=True, order=4, fs_Hz=fs) 
    
    newSig3 = filterSignal(newSig, fType='lowpass', freq=1.0/120,
                            useFiltFilt=True, order=4, fs_Hz=fs) 
    
    ymax = np.max(newSig)
    plt.figure(figsize=(15, 2))
    plt.title('Normalized')
    plt.plot(ts, newSig, alpha=0.25)
    plt.plot(ts, newSig2, 'r')
    plt.plot(ts, newSig3, 'g')
    
    for j in range(int(ts[-1])):
        if j % 5 == 0:
            plt.plot([j,j], [0,ymax+1], 'k', alpha=0.5)
        else:
            plt.plot([j,j], [0,ymax+1], 'k', alpha=0.2)
    plt.xlim(0, ts[-1])
    plt.ylim(0, )
    plt.show() 
    
    return newSig2


def findUC(sigUC, ts, minSpacing=10.0/8, verbose=False):
    idxMinima, idxMaxima = getCrossings(np.diff(sigUC))
    
    peaks = sorted([[sigUC[i],  i] for i in idxMaxima], reverse=True)
    peaks = [i for _, i in peaks]
    
    selected = []
    for i, idxThis in enumerate(peaks):
        adjacent = [True for idxOther in peaks[:i] if abs(ts[idxThis]-ts[idxOther]) < minSpacing]
        if not adjacent:
            selected.append(idxThis)
            
    selected = sorted(selected)
    if verbose:
        for i in selected:
            print '{:0.1f}: {:0.1f}'.format(ts[i], sigUC[i])
      
    return selected, [ts[i] for i in selected]


def computeBaselineUC(peaks, sigUC, verbose=True, title=''):
    idxMinima = [np.argmin(sigUC[peaks[i-1]:peaks[i]])+peaks[i-1] for i in range(1, len(peaks))]
    magMinima = [sigUC[i] for i in idxMinima]

    if len(idxMinima) == 0:
        return np.zeros(len(sigUC)), idxMinima
    
    # Add Endpoints
    idxMinima = [0] + idxMinima + [len(sigUC)-1]
    magMinima = [magMinima[0]] + magMinima + [magMinima[-1]]

    base = np.interp(range(len(sigUC)), idxMinima, magMinima)
    
    if verbose:
        maxUC = np.max(sigUC)
        minUC = np.min(sigUC)

        plt.figure(figsize=(15, 2))
        plt.title(title)
        plt.plot(sigUC, 'r')
        plt.plot(base)
        plt.scatter(idxMinima, magMinima)
        for i in peaks:
            plt.plot([i,i], [minUC, maxUC], 'g--')
        plt.ylim(0,)
        plt.xlim(0,len(sigUC)-1)
        plt.show()
        
    return base, idxMinima


def normalizeUC(peaks, sigUC, sigma=1.0, sigmaP=0.25, verbose=False, includeUC=False):
    """Normalize individual contractions after baseline removal"""
    
    base, idxMinima = computeBaselineUC(peaks, sigUC, verbose=verbose, title='Pass 1')

    newUC = sigUC - base
    newPeakMag = [newUC[i] for i in peaks]
    #medPeaks = np.median(newPeakMag)
    medSig = np.median(newUC)
    
    if verbose:
        plt.figure(figsize=(15, 2))
        plt.plot(newUC, 'r')
        plt.plot([0, len(newUC)-1], [medSig, medSig], 'b--')
        #plt.plot([0, len(newUC)-1], [medPeaks, medPeaks], 'k--')
        maxUC = np.max(sigUC)
        minUC = np.min(sigUC)
        for i in peaks:
            plt.plot([i,i], [minUC, maxUC], 'g--')
        plt.ylim(0,)
        plt.xlim(0,len(sigUC)-1)
        plt.show()
    
    # Filter small peaks
    discard = [i for i in peaks if newUC[i] < sigma*medSig]
    peaks = [i for i in peaks if newUC[i] >= sigma*medSig]
    if verbose:
        print 'discarding:', discard
    
    base, idxMinima = computeBaselineUC(peaks, sigUC, verbose=verbose, title='Pass 2')

    newUC = sigUC - base
    newPeakMag = [newUC[i] for i in peaks]
    medPeaks = np.median(newPeakMag)
    
    if verbose:
        plt.figure(figsize=(15, 2))
        plt.plot(newUC, 'r')
        plt.plot([0, len(newUC)-1], [medPeaks, medPeaks], 'k--')
        maxUC = np.max(sigUC)
        minUC = np.min(sigUC)
        for i in peaks:
            plt.plot([i,i], [minUC, maxUC], 'g--')
        plt.ylim(0,)
        plt.xlim(0,len(sigUC)-1)
        plt.show()
    
    # Filter small peaks
    discard2 = [i for i in peaks if newUC[i] < sigmaP*medPeaks]
    peaks = [i for i in peaks if newUC[i] >= sigmaP*medPeaks]
    if verbose:
        print 'discarding:', discard2
    
    base, idxMinima = computeBaselineUC(peaks, sigUC, verbose=verbose, title='Pass 3')

    newUC = sigUC - base
    newPeakMag = [newUC[i] for i in peaks]
    #medPeaks = np.median(newPeakMag)
    
    if verbose:
        plt.figure(figsize=(15, 2))
        plt.plot(newUC, 'r')
        #plt.plot([0, len(newUC)-1], [medPeaks, medPeaks], 'k--')
        maxUC = np.max(sigUC)
        minUC = np.min(sigUC)
        for i in peaks:
            plt.plot([i,i], [minUC, maxUC], 'g--')
        for i in discard:
            plt.plot([i,i], [minUC, maxUC], 'm', lw=5)
        for i in discard2:
            plt.plot([i,i], [minUC, maxUC], 'r', lw=5)
        plt.ylim(0,)
        plt.xlim(0,len(sigUC)-1)
        plt.show()

    for i in range(1, len(idxMinima)):
        idxStart = idxMinima[i-1]
        idxEnd = idxMinima[i]
        newUC[idxStart:idxEnd] = newUC[idxStart:idxEnd] / np.max(newUC[idxStart:idxEnd])
        
    if verbose:
        plt.figure(figsize=(15, 2))
        plt.plot(newUC, 'r')
        for i in peaks:
            plt.plot([i,i], [0, 1.1], 'g--')
        plt.ylim(0, 1.1)
        plt.xlim(0,len(sigUC)-1)
        plt.show()

    if includeUC:
        return peaks, newUC
    else:
        return peaks
