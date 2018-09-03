# -*- coding: utf-8 -*-
#
#  Copyright Douglas Williams, 2017-2018
#  All Rights Reserved
#

from rules_constants import *
from rules_config import *
from rules_message_digest import *


# Below is my initial summary of the FIGO IA Guidelines.
#
#
# FHR Monitoring Duration:
# 	• Timing:  During UC and > 30 after UC
# 	• Measured:
# 		• > 60 sec if normal
# 		• For 3 UC if abnormal
#
# Decision Guidelines:
# 	• Urgent (if not CTG [present). [in our case, we might immediately switch over to Continuous Monitoring mode]
# 		• FHR < 110 bpm for > 5min
# 		• FHR > 160 BPM for > 3 UC
# 		• Repetitive decelerations
# 	• Abnormal:   [in our case, we might immediately switch over to Continuous Monitoring mode]
# 		• FHR < 110 bpm
# 		• FHR > 160 BPM
# 		• Repetitive decelerations
# 		• Prolonged Deceleration (> 3min)
# 		• UC > 5 contractions/10 min
# 	• Normal:
# 		• None


def hasAnyConcerning(e):
    if (e.presenting(FETAL_TACHYCARDIA) or e.presenting(FETAL_BRADYCARDIA)
        or e.countHistory(LATE_DECELERATION, inMinutes=10) > 0
        or e.countHistory(PERIODIC_VARIABLE_DECELERATION, inMinutes=10) > 0):
        return True
    return False


def getRecordingDuration(e):
    duration = (e.getMeasurementTimestamp(RECORDING_DURATION)
                - e.getMeasurementTimestamp(RECORDING_DURATION, getOldest=True))
    return duration


def hasMinDurationExpired(e, minLagUC=3, durationWithoutUC=10):
    timeFirstUC = e.getMeasurementTimestamp(CONTRACTIONS, getOldest=True)

    if timeFirstUC is None:
        return getRecordingDuration(e) >= durationWithoutUC
    else:
        currentTime = e.getMeasurementTimestamp(RECORDING_DURATION)
        return currentTime - timeFirstUC > minLagUC


def hasMaxDurationExpired(e, minUC=3, minLagUC=3, durationWithoutUC=10):
    contractionCount = e.countAnyHistory(CONTRACTIONS)
    if contractionCount > minUC:
        return True
    elif contractionCount == minUC:
        timeLastUC = e.getMeasurementTimestamp(CONTRACTIONS)
        currentTime = e.getMeasurementTimestamp(RECORDING_DURATION)
        return currentTime - timeLastUC > minLagUC
    else:
        return getRecordingDuration(e) >= durationWithoutUC


def rule_P0_00_not_yet_min_duration(e):
    if not hasMinDurationExpired(e):
        e.proposeAssessment(FETUS, ASSESSMENT_CONTINUE, diagnosis=[DIAG_CONTINUE_IA])
        return True
    return False


def rule_P0_00_extended_evaluation(e):
    #print 'rule_P0_00_extended_evaluation -- hasAnyConcerning', hasAnyConcerning(e)
    if hasAnyConcerning(e) and not hasMaxDurationExpired(e):
        e.proposeAssessment(FETUS, ASSESSMENT_CONTINUE, diagnosis=[DIAG_CONTINUE_IA])
        return True
    return False



#################################################
#
# Baseline:
#
#################################################

def rule_P0_00_no_fhr_measurement(e, minDuration=10):
    # Default response when no updated basal heart rate available for > 10min
    # Also initial condition

    if getRecordingDuration(e) > minDuration and e.absentHistory(FETAL_HEART_RATE, minDuration):
        e.proposeAssessment([FETUS, FETAL_HR], ASSESSMENT_SUSPICIOUS, diagnosis=[DIAG_CHECK_MONITOR])
        return True

    return False



def rule_P0_01_fetal_heart_rate_normal(e):
    if e.presenting(FETAL_HEART_RATE_NORMAL):
        e.proposeAssessment(FETAL_HR, ASSESSMENT_NORMAL)
        if hasMinDurationExpired(e) and not hasAnyConcerning(e) or hasMaxDurationExpired(e):
            e.proposeAssessment(FETUS, ASSESSMENT_NORMAL, diagnosis=[DIAG_COMPLETE_IA])
        return True
    return False


def rule_P0_01_fetal_heart_rate_tachy(e):
    if e.presenting(FETAL_TACHYCARDIA):
        e.proposeAssessment(FETAL_HR, ASSESSMENT_SUSPICIOUS)
        if hasMaxDurationExpired(e):
            e.proposeAssessment(FETUS, ASSESSMENT_SUSPICIOUS, diagnosis=[DIAG_TACHYCARDIA, DIAG_COMPLETE_IA])
        else:
            e.proposeAssessment(FETUS, ASSESSMENT_CONTINUE, diagnosis=[DIAG_CONTINUE_IA])
        return True
    return False


def rule_P0_01_fetal_heart_rate_brady(e):
    if e.presenting(FETAL_BRADYCARDIA):
        e.proposeAssessment(FETAL_HR, ASSESSMENT_SUSPICIOUS, diagnosis=[DIAG_BRADYCARDIA])
        if getRecordingDuration(e) > 5:
            e.proposeAssessment(FETUS, ASSESSMENT_SUSPICIOUS, diagnosis=[DIAG_BRADYCARDIA, DIAG_COMPLETE_IA])
        else:
            e.proposeAssessment(FETUS, ASSESSMENT_CONTINUE, diagnosis=[DIAG_CONTINUE_IA])
        return True
    return False



#################################################
#
# Prolonged Decelerations:
#
#################################################


def rule_P0_03_shorter_prologned_decel(e):
    if e.presenting(PROLONGED_DECELERATION_PRESENT):
        e.proposeAssessment([FETUS, FETAL_DECELS], ASSESSMENT_SUSPICIOUS, diagnosis=[DIAG_PROLONGED, DIAG_COMPLETE_IA])
        return True
    return False


def rule_P0_03_longer_prologned_decel(e):
    if e.presenting(LONGER_PROLONGED_DECELERATION_PRESENT):
        e.proposeAssessment([FETUS, FETAL_DECELS], ASSESSMENT_PATHOLOGICAL,
                            diagnosis=[DIAG_LONG_PROLONGED, DIAG_COMPLETE_IA])
        return True
    return False


def rule_P0_03_marked_prologned_decel(e):
    if e.presenting(LONGER_MARKED_PROLONGED_DECELERATION_PRESENT):
        e.proposeAssessment([FETUS, FETAL_DECELS, FETAL_HR], ASSESSMENT_URGENT,
                            diagnosis=[DIAG_MARKED_PROLONGED, DIAG_COMPLETE_IA])
        return True
    return False


#################################################
#
# Periodic Decelerations:
#
#################################################

def rule_P0_04_late_decel(e):
    count = e.countHistory(LATE_DECELERATION, inMinutes=10)
    if count >0:
        if count >= 2:
            e.proposeAssessment([FETUS, FETAL_DECELS], ASSESSMENT_PATHOLOGICAL,
                                diagnosis=[DIAG_REPETITIVE_LATE_DECEL, DIAG_COMPLETE_IA])
        else:
            e.proposeAssessment(FETAL_DECELS, ASSESSMENT_SUSPICIOUS, diagnosis=[DIAG_LATE_DECEL])
        return True
    return False


def rule_P0_04_periodic_variable_decel(e):
    count = e.countHistory(PERIODIC_VARIABLE_DECELERATION, inMinutes=10)
    if count >0:
        if count >= 2:
            e.proposeAssessment([FETUS, FETAL_DECELS], ASSESSMENT_SUSPICIOUS,
                                diagnosis=[DIAG_REPETITIVE_PERIODIC_VARIABLE, DIAG_COMPLETE_IA])
        else:
            e.proposeAssessment(FETAL_DECELS, ASSESSMENT_SUSPICIOUS)
        return True
    return False


#################################################
#
# Accelerations
#
#################################################


def rule_P0_03_present_accelerations(e):
    #
    if e.presenting(ACCELERATION_PRESENT):
        e.proposeAssessment([FETAL_ACCELS], ASSESSMENT_PRESENT)
    else:
        e.proposeAssessment([FETAL_ACCELS], ASSESSMENT_ABSENT)

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
    duration = getRecordingDuration(e)
    if duration < minDuration:
        return None

    duration = min(duration, preferredDuration)

    contractionCount = e.countAnyHistory(CONTRACTIONS, inMinutes=duration)
    contractionRate = round(10*float(contractionCount)/duration)
    if verbose:
        print 'contraction rate:', contractionRate

    return contractionRate


def rule_P0_05_tachysystole_contractions(e, minDuration=5):
    if getRecordingDuration(e) < minDuration:   # insufficient duration
        return False

    contractionRate = getContractionRate(e, minDuration=minDuration, preferredDuration=10)
    if contractionRate > 5:
        e.proposeAssessment([FETUS, MATERNAL_CONTRACTIONS], ASSESSMENT_SUSPICIOUS,
                            diagnosis=[DIAG_TACHYSYSTOLE, DIAG_COMPLETE_IA])
        return True
    return False


def rule_P0_05_any_contractions(e):
    contractionCount = e.countAnyHistory(CONTRACTIONS)
    if contractionCount == 0:
        e.proposeAssessment(MATERNAL_CONTRACTIONS, ASSESSMENT_ABSENT, diagnosis=[DIAG_NO_CONTRACTIONS])
    else:
        e.proposeAssessment(MATERNAL_CONTRACTIONS, ASSESSMENT_PRESENT)

    return False

