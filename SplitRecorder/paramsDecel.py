# coding: utf-8

#
#  Copyright Douglas Williams, 2018
#  All Rights Reserved
#

from libDecel import classifyDecel


#
# Parameters for Variable Decel Extraction
#

varValidParams = {
    'classification':'variable',
    'minDuration':15, 'maxDuration':60*3,
    'minMag':15,  'minPctValid':0.5, 'maxOnsetRatio':0.6}

varBorderlineParams = {
    'classification':'borderline_variable',
    'minDuration':14, 'maxDuration':60*3,
    'minMag':14,  'minPctValid':0.5, 'maxOnsetRatio':0.7}

varDecelClassifiers = [
    lambda x: classifyDecel(x, **varValidParams),
    # lambda x: classifyDecel(x, **varBorderlineParams)
]

varDecelParams = {
    'filterParams':{
        'fDetail': 1.0 / 6,
        'fSmooth': 1.0 / 18,
        'fBaselineInitial': 1.0/2,
        'fBaselineFinal': 1.0/6,
    },
    'classifiers':varDecelClassifiers,
}


#
# Parameters for Prolonged Decel Extraction
#

prolongedValidParams = {
    'classification':'prolonged',
    'minDuration':60*3, 'maxDuration':60*10,
    'minMag':15,  'minPctValid':0.25,
    'time_under_15':3.0, 'time_under_50pct':2.0,
    'maxOnsetRatio': None,
    'showDetail':False}

prolongedBorderlineParams = {
    'classification':'borderline_prolonged',
    'minDuration':60*3, 'maxDuration':60*10,
    'minMag':15,  'minPctValid':0.10,
    'time_under_15':0, 'time_under_50pct':0,
    'maxOnsetRatio': None,
    'showDetail':False}

prolongedDecelClassifiers = [
    lambda x: classifyDecel(x, **prolongedValidParams),
    # lambda x: classifyDecel(x, **prolongedBorderlineParams)
]

prolongedDecelParams = {
    'filterParams':{
        'fDetail': 1.0 / 6,
        #'fSmooth': 1.0 / 18,
        'fSmooth': 1.0 / 48,
        'fBaselineInitial': 1.0/4,
        #'fBaselineFinal': 1.0/32,
        'fBaselineFinal': 1.0/48,
        #'fBaselineFinal': 1.0/64,
    },
    'classifiers':prolongedDecelClassifiers,
}

#
# Periodic Decelerations including Late and Early
#

# Initial classification parameters
uniformValidParams = {
    'classification':'valid',
    'minDuration':45, 'maxDuration':60*2,
    'minOnsetOrRelease':25,
    'minMag':15,  'minPctValid':0.25,
    'minOnsetRatio':None, 'maxOnsetRatio':None}

uniformBorderlineParams = {
    'classification':'borderline',
    'minDuration':35, 'maxDuration':60*2,
    'minOnsetOrRelease':20,
    'minMag':5,  'minPctValid':0.25,
    'minOnsetRatio':None, 'maxOnsetRatio':None}

uniformOtherParams = {
    'classification':'other',
    'minDuration':15, 'maxDuration':45,
    'minOnset':15,
    'minMag':15,  'minPctValid':0.5, 'minOnsetRatio':0.40, 'maxOnsetRatio':0.7}

uniformClassifiers = [
    lambda x: classifyDecel(x, **uniformValidParams),
    lambda x: classifyDecel(x, **uniformBorderlineParams),
    lambda x: classifyDecel(x, **uniformOtherParams)
]


# Reclassification Parameters

lateParams = {
    'classification':'late_decel',
    'minDuration':45, 'maxDuration':60*2,
    'minOnsetOrRelease':25,
    'minLag': 20,
    'minMag':15,  'minPctValid':0.25,
    'minOnsetRatio':None, 'maxOnsetRatio':None}

mildLateParams = {
    'classification':'mild_late_decel',
    'minDuration':45, 'maxDuration':60*2,
    'minOnsetOrRelease':25,
    'minLag': 20,
    'minMag':8.5,  'minPctValid':0.25,
    'minOnsetRatio':None, 'maxOnsetRatio':None}

relaxedLateParams = {
    'classification':'relaxed_late_decel',
    'minDuration':35, 'maxDuration':60*2,
    'minOnsetOrRelease':20,
    'minLag': 20,
    'minMag':7.5,  'minPctValid':0.25,
    'minOnsetRatio':None, 'maxOnsetRatio':None}

earlyParams = {
    'classification':'early_decel',
    'minDuration':35, 'maxDuration':60*2,
    'minOnsetOrRelease':20,
    'maxLag': 20,
    'minMag':8.5,  'maxMag':30,
    'minPctValid':0.25,
    'minOnsetRatio':None, 'maxOnsetRatio':None}

shallowEarlyParams = {
    'classification':'shallow_early_decel',
    'minDuration':35, 'maxDuration':60*2,
    'minOnsetOrRelease':20,
    'maxLag': 20,
    'minMag':0.5,  'maxMag':30,
    'minPctValid':0.25,
    'minOnsetRatio':None, 'maxOnsetRatio':None}

otherUniformParams = {
    'classification':'other_uniform_decel',
    'minDuration':45, 'maxDuration':60*2,
    'minOnsetOrRelease':25,
    'minLag': 20,
    'minMag':8.5,  'minPctValid':0.25,
    'minOnsetRatio':None, 'maxOnsetRatio':None}

variablePeriodicParams = {
    'classification':'variable_periodic',
    'minDuration':15, 'maxDuration':60*2,
    'minLag': -20,
    'minOnset':15,
    'minMag':15,  'minPctValid':0.5, #'minOnsetRatio':0.40,
    'maxOnsetRatio':0.7
}

otherPeriodicParams = {
    'classification':'other_periodic',
    'minLag': -20,
    'minDuration':None, 'maxDuration':None, 'minMag':None,
    'minOnset':None, 'minOnsetRatio':None, 'maxOnsetRatio':None, 'minPctValid':None}

uniformReclassifiers = [
    lambda x: classifyDecel(x, **lateParams),
    lambda x: classifyDecel(x, **mildLateParams),
#     lambda x: classifyDecel(x, **relaxedLateParams),
    lambda x: classifyDecel(x, **earlyParams),
    lambda x: classifyDecel(x, **shallowEarlyParams),
    # lambda x: classifyDecel(x, **otherUniformParams),
    lambda x: classifyDecel(x, **variablePeriodicParams),
    # lambda x: classifyDecel(x, **otherPeriodicParams),
]

uniformDecelParams = {
    'filterParams': {
        'fDetail': 1.0 / 6,
        'fSmooth': 1.0 / 36,
        #'fSmooth': 1.0 / 48,
        'fBaselineInitial': 1.0/2,
        'fBaselineFinal': 1.0/6,
    },
    'classifiers':uniformClassifiers,
    'reclassifiers':uniformReclassifiers,
}


#
# Acceleration Parame
#
accelValidParams = {
    'classification':'acceleration',
    'minDuration':15, 'maxDuration':60*3, 'maxOnset':30, 'minOnset':10,
    'minMag':15,  'minPctValid':0.75, #'maxOnsetRatio':0.55
}

accelBorderlineParams = {
    'classification':'borderline_acceleration',
    'minDuration':15, 'maxDuration':60*3, 'maxOnset':30, 'minOnset':8,
    'minMag':13,  'minPctValid':0.75, #'maxOnsetRatio':0.55
}

accelClassifiers = [
    lambda x: classifyDecel(x, **accelValidParams),
    lambda x: classifyDecel(x, **accelBorderlineParams),
]

accelParams = {
    'filterParams': varDecelParams['filterParams'],  # same as variable decels
    'classifiers':accelClassifiers,
}




#
# Combined Parameter Set
#
FEATURE_EXTRACT_PARAMS = {
    'varDecelParams':varDecelParams,
    'uniformDecelParams':uniformDecelParams,
    'prolongedDecelParams':prolongedDecelParams,
    'accelParams': accelParams,
    'freqVariability':1.0 / 50
}



