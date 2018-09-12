# coding: utf-8

#
#  Copyright Douglas Williams, 2018
#  All Rights Reserved
#


import numpy as np
from scipy import signal


def tolist(val):
    if isinstance(val, np.ndarray):
        return val.tolist()
    else:
        return val


def getCrossings(deriv, offset=1):
    idxMinima = np.nonzero(np.logical_and(deriv[:-1] < 0, deriv[1:] >= 0))[0]
    idxMaxima = np.nonzero(np.logical_and(deriv[:-1] > 0, deriv[1:] <= 0))[0]
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


