# -*- coding: utf-8 -*-
#
#  Copyright Douglas Williams, 2017-2018
#  All Rights Reserved
#

# TODO:
# 1) Update UC rules
#

from rules_constants import *
from rules_config import *
from rules_message_digest import *


#################################################
#
# Baseline:
#
#################################################

# Mean level of the most horizontal and less oscillatory FHR segments.
# * Estimated in time periods of 10 minutes
# * Expressed in beats per minute (bpm).
# * In tracings with unstable FHR signals, review of previous segments and/or evaluation of longer time periods may be necessary to:
#     * estimate the baseline during the second stage of labor
#     * identify the fetal behavioral state of active wakefulness that can lead to erroneously high baseline estimation.
#
# Classification:
# * Normal baseline: a value between 110 and 160 bpm.
# * Tachycardia: a baseline value above 160 bpm lasting more than 10 minutes.
# * Bradycardia: a baseline value below 110 bpm lasting more than 10 minutes.
#     * Values between 100 and 110 bpm may occur in normal fetuses, especially in postdate pregnancies.
#
# Continuous Monitoring Decision Guidelines:
# * Pathological:
#     * < 100 bpm lasting more than 10 minutes
# * Suspicious:
#     * < 110 bpm and < 100 lasting more than 10 minutes
#     * > 160 bpm lasting more than 10 minutes
# * Normal
#     * >= 110 bpm <= 160 lasting more than 10 minutes


# FHR_CLASSIFICATION = [
#     {'name': SEVERE_FETAL_BRADYCARDIA,  'bounds': [None, 100]},
#     {'name': BORDERLINE_FETAL_BRADYCARDIA,    'bounds': [101, 110]},
#     {'name': FETAL_HEART_RATE_NORMAL,   'bounds': [110, 160]},
#     {'name': FETAL_TACHYCARDIA,    'bounds': [161, None]},
#     ]

def rule_P0_00_no_fhr_measurement(e):
    # Default response when no updated basal heart rate available for > 10min
    # Also initial condition
    if e.absentHistory(FETAL_HEART_RATE, 10):
        e.proposeAssessment([FETUS, FETAL_HR], ASSESSMENT_SUSPICIOUS, diagnosis=[DIAG_CHECK_MONITOR])
        return True

    return False


def rule_P0_01_fetal_heart_rate_normal(e):
    if e.presenting(FETAL_HEART_RATE_NORMAL):
        e.proposeAssessment([FETUS, FETAL_HR], ASSESSMENT_NORMAL)
        return True

    return False


def rule_P0_01_fetal_heart_rate_tachy(e):
    if e.presenting(FETAL_TACHYCARDIA):
        e.proposeAssessment([FETUS, FETAL_HR], ASSESSMENT_SUSPICIOUS, diagnosis=[DIAG_TACHYCARDIA])
        return True

    return False


def rule_P0_01_fetal_heart_rate_borderline_brady(e):
    if e.presenting(BORDERLINE_FETAL_BRADYCARDIA):
        e.proposeAssessment([FETUS, FETAL_HR], ASSESSMENT_SUSPICIOUS, diagnosis=[DIAG_BRADYCARDIA])
        return True

    return False


def rule_P0_01_fetal_heart_rate_brady(e):
    if e.presenting(SEVERE_FETAL_BRADYCARDIA):
        e.proposeAssessment([FETUS, FETAL_HR], ASSESSMENT_PATHOLOGICAL, diagnosis=[DIAG_SEVERE_BRADYCARDIA])
        return True

    return False

#################################################
#
# Variability:
#
#################################################


# This refers to the oscillations in the FHR signal, evaluated as the average bandwidth amplitude of the signal in 1-minute segments.
#
# Classification:
# * Normal variability: a bandwidth amplitude of 5−25 bpm.
# * Reduced variability:
#     * a bandwidth amplitude below 5 bpm for more than 50 minutes in baseline segments
#     * more than 3 minutes during decelerations.
#     * Note: During deep sleep, variability is usually in the lower range of normality, but the bandwidth amplitude is seldom under 5 bpm.
# * Increased variability (saltatory pattern): a bandwidth value exceeding 25 bpm lasting more than 30 minutes
#
# Continuous Monitoring Decision Guidelines:
# * Pathological:
#     * Variability < 5 bpm lasting more than 50 minutes
#         * Special case 20 min if repetitive late decelerations
#     * Variability > 25 bpm lasting more than 30 minutes
# * Suspicious:
#     *
# * Normal
#     * Variability >= 5 bpm <= 25 bpm

# FHR_VARIABILITY_CLASSIFICATION = [
#     {'name': HIGH_VARIABILITY,   'bounds':[26, None]},
#     {'name': NORMAL_VARIABILITY, 'bounds':[6, 25]},
#     {'name': LOW_VARIABILITY,    'bounds':[None, 5]},
#     ]
#
# FHR_VARIABILITY_HISTORY = [
#     {'name': PROLONGED_LOW_VARIABILITY_50,   'metric': LOW_VARIABILITY,  'duration':50, 'isSustained': True },
#     {'name': PROLONGED_LOW_VARIABILITY_20, 'metric': LOW_VARIABILITY,  'duration':20, 'isSustained': True },
#     {'name': PROLONGED_HIGH_VARIABILITY_30,  'metric': HIGH_VARIABILITY, 'duration':30, 'isSustained': True},
#     ]


def rule_P0_02_fhrv_marked(e):
    if e.presenting(PROLONGED_HIGH_VARIABILITY_30):
        e.proposeAssessment([FETUS, FETAL_VAR], ASSESSMENT_PATHOLOGICAL, diagnosis=[DIAG_FHRV_MARKED])
        return True

    return False


def rule_P0_02_fhrv_prolonged_low(e):
    if e.presenting(PROLONGED_LOW_VARIABILITY_50) :
        e.proposeAssessment([FETUS, FETAL_VAR], ASSESSMENT_PATHOLOGICAL, diagnosis=[DIAG_FHRV_LOW])
        return True

    return False

#################################################
#
# Episodic Patterns
#
#################################################

# EPISODIC_PATTERN_HISTORY = [
#     {'name': ACCELERATION_PRESENT, 'metric': ACCELERATION,
#      'duration':50, 'bounds': [1, None] },
#     {'name': PROLONGED_DECELERATION_PRESENT, 'metric': PROLONGED_DECELERATION,
#      'duration':30, 'bounds': [1, None] },
#     {'name': LONGER_PROLONGED_DECELERATION_PRESENT, 'metric': LONGER_PROLONGED_DECELERATION,
#      'duration':30, 'bounds': [1, None] },
#     {'name': LONGER_MARKED_PROLONGED_DECELERATION_PRESENT, 'metric': LONGER_MARKED_PROLONGED_DECELERATION,
#      'duration':30, 'bounds': [1, None] },
# ]


# Accelerations
#
# Criteria:
# * Magnitude > 15 bpm
# * Onset < 30
# * Duration > 15 sec (and < 10min)
#
# Question:
# * Do we need too detect absence of accelerations?

# Feedback: For the acceleration. I think we should detect them. If there is no acceleration in 50 minutes trace we can stimulate fetus and try to trace for another 20 to 30 minutes to look for acceleration. As if the fetus is having deep sleep there might not be any acceleration.



def rule_P0_03_absent_accelerations(e, minDuration=50):
    # rule: at least 50 minute without acceleration
    duration = e.getLastMeasurement(RECORDING_DURATION)
    if duration < minDuration:
        return None

    if not e.presenting(ACCELERATION_PRESENT):
        e.proposeAssessment([FETUS, FETAL_ACCELS], ASSESSMENT_SUSPICIOUS, diagnosis=[DIAG_ACCEL_MISSING])
        return True

    return False


def rule_P0_03_present_accelerations(e):
    #
    if e.presenting(ACCELERATION_PRESENT):
        e.proposeAssessment([FETAL_ACCELS], ASSESSMENT_PRESENT)
    else:
        e.proposeAssessment([FETAL_ACCELS], ASSESSMENT_ABSENT)

    return False


# Prolonged Decelerations:
#
# Criteria:
# * lasting more than 3 minutes.
# * Decelerations exceeding 5 minutes, with FHR maintained at less than 80 bpm and reduced variability within the deceleration, are frequently associated with acute fetal hypoxia/acidosis and require emergent intervention.
#
# Continuous Monitoring Decision Guidelines:
# * Urgent Action:
#     * Decelerations exceeding 5 minutes, with FHR maintained at less than 80 bpm and reduced variability within the deceleration
# * Pathological:
#     * Decelerations exceeding 5 minutes
#     * Repetitive Prolonged Decels
#         * Question:  What is definition of repetitive in context of Prolonged Decels
# * Suspicious:
#     * Any Prolonged Decel (> 3min)
# * Normal:
#     * None
#

def rule_P0_03_shorter_prologned_decel(e):
    if e.presenting(PROLONGED_DECELERATION_PRESENT):
        e.proposeAssessment([FETUS, FETAL_DECELS], ASSESSMENT_SUSPICIOUS, diagnosis=[DIAG_PROLONGED])
        return True
    return False


def rule_P0_03_longer_prologned_decel(e):
    if e.presenting(LONGER_PROLONGED_DECELERATION_PRESENT):
        e.proposeAssessment([FETUS, FETAL_DECELS], ASSESSMENT_PATHOLOGICAL, diagnosis=[DIAG_LONG_PROLONGED])
        return True
    return False

def rule_P0_03_marked_prologned_decel(e):
    if e.presenting(LONGER_MARKED_PROLONGED_DECELERATION_PRESENT):
        e.proposeAssessment([FETUS, FETAL_DECELS, FETAL_HR], ASSESSMENT_URGENT, diagnosis=[DIAG_MARKED_PROLONGED])
        return True
    return False


# Episodic Variable Decelerations:
#
# Ignored for now


#################################################
#
# Periodic Patterns
#
#################################################

# PERIODIC_PATTERN_HISTORY = [
#     {'name': ANY_LATE_DECELERATIONS,                       'metric': LATE_DECELERATION,
#      'duration':20, 'bounds': [1, None] },
# ]

# Late Decelerations:
#
# Criteria:
# * Magnitude > 15 bpm
#     * In the presence of a tracing with no accelerations and reduced variability, the definition of late decelerations also includes those with an amplitude of 10−15 bpm.
# * Deceleration with:
#     * a gradual onset
#     * and/or a gradual return to the baseline
#     * and/or reduced variability within the deceleration
#     * Gradual onset and return occurs when more than 30 seconds elapses between the beginning/end of a deceleration and its nadir.
# * Duration > 30 sec (and < 3min)
# * Lag: When contractions are adequately monitored, late decelerations
#     * start more than 20 seconds after the onset of a contraction,
#     * have a nadir after the acme,
#     * and a return to the baseline after the end of the contraction.
#
#
# Continuous Monitoring Decision Guidelines:
# * Pathological:
#     * Repetitive Late Decels (> 50% of UC) for >30 min
#         * > 20 min if reduced variability
# * Suspicious:
#     * Any late decelerations (new rule based on Jiya's feedback)
# * Normal:
#     * None

# Feedback from Jiya: For late decels.  I suggest it will be better idea to add shorter time e.g. decels in less then 50% of uterine contractions Is suspicious. So that at least it will alert the team early as in cases of busy places with limited resources it will give head up for working staff and alert them early.



def isRepetitive(e, pattern, duration,  verbose=False):
    allPeriodic = e.countAnyHistory(PERIODIC_PATTERNS, inMinutes=duration)
    if allPeriodic == 0:
        if verbose:
            print 'isRepetitive: {} for {} -- No Periodic'.format(pattern, duration)
        return False
    selectedPeriodic = e.countHistory(pattern, inMinutes=duration)

    if verbose:
        print 'isRepetitive: {} for {} -- {}  of {}'.format(pattern, duration, selectedPeriodic, allPeriodic)
        print '    returns ', selectedPeriodic >= 0.5*allPeriodic
    return (selectedPeriodic >= 0.5*allPeriodic)


def rule_P0_04_any_late_decel(e):
    if e.presenting(ANY_LATE_DECELERATIONS):
        e.proposeAssessment([FETUS, FETAL_DECELS], ASSESSMENT_SUSPICIOUS, diagnosis=[DIAG_LATE_DECEL])
        return True
    return False


def rule_P0_04_repetitive_late_decel(e):
    if isRepetitive(e, LATE_DECELERATION, duration=30):
        e.proposeAssessment([FETUS, FETAL_DECELS], ASSESSMENT_PATHOLOGICAL, diagnosis=[DIAG_REPETITIVE_LATE_DECEL])
        return True
    return False

def rule_P0_04_fhrv_low_plus_late_decel(e):
    if (isRepetitive(e, LATE_DECELERATION, duration=20) and e.presenting(PROLONGED_LOW_VARIABILITY_20)):
        e.proposeAssessment([FETUS, FETAL_VAR, FETAL_DECELS], ASSESSMENT_PATHOLOGICAL, diagnosis=[DIAG_REPETITIVE_LATE_DECEL_LOW_VAR])
        return True
    return False



# Early Decelerations:
#
# Criteria:
# * Shape: shallow, short-lasting
# * Phase:  Coincident with contraction
# * Variability: normal variability within the deceleration
#
# Ignored for now


# Periodic Variable Decelerations:
#
# Criteria:
# * Magnitude > 15 bpm
# * Onset < 30
# * Duration > 15 sec (and < 3min)
#
# Continuous Monitoring Decision Guidelines:
# * Pathological:
#     * None
# * Suspicious:
#     * Repetitive Variable Decels (> 50% of UC)
#         *  Question:  Is there a minimum duration for repetition?
# * Normal:
#     * None

# Feedback: For variable decels from guidelines I haven’t seen any shorter time period but may be other  colleagues can advise on that.

def rule_P0_04_repetitive_variable_decel(e):
    if isRepetitive(e, PERIODIC_VARIABLE_DECELERATION, duration=20):
        e.proposeAssessment([FETUS, FETAL_DECELS], ASSESSMENT_SUSPICIOUS, diagnosis=[DIAG_REPETITIVE_PERIODIC_VARIABLE])
        return True
    return False



#################################################
#
# Contractions
#
#################################################


# From FIGO Guidelines:
#
# Tachysystole: This represents an excessive frequency of contrac- tions and is defined as
# the occurrence of more than five contractions in 10 minutes, in two successive 10-minute
# periods, or averaged over a 30-minute period.
#
#
# Continuous Monitoring Decision Guidelines:
# * Pathological:
#     * None
# * Suspicious:
#     * Contraction rate > 5 per 10 min averaged over 30 minutes
#       or 2 successive intervals of 5 per 10 minutes within 30 min
# * Normal:
#     * None

def getContractionRate(e, minDuration=10, preferredDuration=20, verbose=False):
    duration = e.getLastMeasurement(RECORDING_DURATION)
    if duration < minDuration:
        return None

    duration = min(duration, preferredDuration)

    contractionCount = e.countAnyHistory(CONTRACTIONS, inMinutes=duration)
    contractionRate = round(10*float(contractionCount)/duration)
    if verbose:
        print 'contraction rate:', contractionRate

    return contractionRate


def rule_P0_05_tachysystole_contractions(e):
    contractionRate = getContractionRate(e)
    duration = e.getLastMeasurement(RECORDING_DURATION)
    if duration is None:   # insufficient duration
        return False

    if contractionRate > 5:
        e.proposeAssessment([FETUS, MATERNAL_CONTRACTIONS], ASSESSMENT_SUSPICIOUS, diagnosis=[DIAG_TACHYSYSTOLE])
        return True
    return False


def rule_P0_05_any_contractions(e):
    contractionRate = getContractionRate(e)
    if contractionRate == 0:
        e.proposeAssessment(MATERNAL_CONTRACTIONS, ASSESSMENT_ABSENT, diagnosis=[DIAG_NO_CONTRACTIONS])
    else:
        e.proposeAssessment(MATERNAL_CONTRACTIONS, ASSESSMENT_PRESENT)

    return False

