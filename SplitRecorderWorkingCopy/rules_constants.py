#
#  Copyright Douglas Williams, 2017-2018
#  All Rights Reserved
#

#
# This file contains definitions of enumerated measurements and conditions.
# Unless condition is the result of a mapping table, the condition should also
# be included in the corresponding *_VOCABULARY in rules.py.
#
# Combination conditions should be defined in rules_config.py
#


#
# Entities
#

FETUS = 'fetus'
FETAL_HR = 'fetalHR'
FETAL_VAR = 'fetalVariability'
FETAL_DECELS = 'fetalDecelerations'
FETAL_ACCELS = 'fetalAccelerations'
MATERNAL_CONTRACTIONS = 'maternalContractions'

#
# Define potential Fetal Assessments
#

# Assessment vocabulary
ASSESSMENT_URGENT   = 'Urgent'
ASSESSMENT_PATHOLOGICAL   = 'Pathological'
ASSESSMENT_SUSPICIOUS = 'Suspicious'
# ASSESSMENT_ATYPICAL   = 'Atypical'
# ASSESSMENT_ABNORMAL = 'Abnormal'
ASSESSMENT_PRESENT = 'Present'
ASSESSMENT_ABSENT = 'Absent'
ASSESSMENT_NORMAL   = 'Normal'
ASSESSMENT_UNKNOWN  = 'Unknown'
ASSESSMENT_CONTINUE  = 'ContinueTesting'  # used for IA rules set


STANDARD_ASSESSMENT_LEVELS = {
    ASSESSMENT_URGENT: 100,
    ASSESSMENT_PATHOLOGICAL: 80,
    ASSESSMENT_SUSPICIOUS: 20,
    ASSESSMENT_NORMAL: 1,
    ASSESSMENT_UNKNOWN: 20,
    ASSESSMENT_CONTINUE: 20,
    }

ADVISORY_ASSESSMENT_LEVELS = {
    ASSESSMENT_PATHOLOGICAL: 80,
    ASSESSMENT_SUSPICIOUS: 20,
    ASSESSMENT_ABSENT: 3,
    ASSESSMENT_PRESENT: 2,
    ASSESSMENT_NORMAL: 1,
    ASSESSMENT_UNKNOWN: 20,
    }



#
# Define Alarm Levels for communication with midwife
#

ALARM_HIGH = 'HighAlarm'
ALARM_LOW = 'LowAlarm'
ALARM_NORMAL = 'NormalAlarm'


#
# Recording Metadata
#
RECORDING_DURATION = 'RecordingDuration'



#
# Measurements and Observations
#

# Automatically captured data
FETAL_HEART_RATE = 'fetalHeartRate'
FETAL_HEART_RATE_MINUTE = 'fetalHeartRateMinute'
FHR_VARIABILITY = 'fetalHeartRateVariability'
EPISODIC_FHR_PATTERNS = 'fhrPatternsEpisodic'
PERIODIC_PATTERNS = 'periodicPatterns'
CONTRACTIONS = 'contractions'




#
# Characterize Fetal Heart Rate
#

SEVERE_FETAL_BRADYCARDIA = 'SevereFetalBradycardia'
BORDERLINE_FETAL_BRADYCARDIA = 'BorderlineFetalBradycardia'
FETAL_TACHYCARDIA = 'FetalTachycardia'
FETAL_HEART_RATE_NORMAL = 'FetalHeartRateNormal'

PROLONGED_FETAL_TACHYCARDIA = 'ProlongedFetalTachycardia'
SEVERE_PROLONGED_FETAL_TACHYCARDIA = 'SevereProlongedFetalTachycardia'

#
# Fetal Heart Rate Characterization
#

NORMAL_VARIABILITY = 'NormalVariability'
LOW_VARIABILITY = 'LowVariability'
HIGH_VARIABILITY = 'ElevatedVariability'

PROLONGED_LOW_VARIABILITY_50 = 'ProlongedLowVariability-50min'
PROLONGED_LOW_VARIABILITY_20 = 'ProlongedLowVariability-20min'
PROLONGED_HIGH_VARIABILITY_30 = 'ProlongedHighVariability-30min'


FHR_TREND_RISING = 'fetalHeartRateTrendRising'
FHR_TREND_FALLING = 'fetalHeartRateTrendFalling'


#
# Episodic Patterns
#

ACCELERATION = 'Acceleration'
LONGER_MARKED_PROLONGED_DECELERATION = 'LongerMarkedProlongedDeceleration'
LONGER_PROLONGED_DECELERATION = 'LongerProlongedDeceleration'
PROLONGED_DECELERATION = 'ProlongedDeceleration'
VARIABLE_DECELERATION = 'VariableDecel'

# History
ACCELERATION_PRESENT = 'AccelerationsPresent'
LONGER_MARKED_PROLONGED_DECELERATION_PRESENT = 'LongerMarkedProlongedDecelerationPresent'
LONGER_PROLONGED_DECELERATION_PRESENT = 'LongerProlongedDecelerationPresent'
PROLONGED_DECELERATION_PRESENT = 'ProlongedDecelerationPresent'

#
# Periodic Patterns
#

EARLY_DECELERATION = 'EarlyDeceleration'
LATE_DECELERATION = 'LateDeceleration'
PERIODIC_VARIABLE_DECELERATION = 'PeriodicVariableDecel'
STANDALONE_CONTRACTION = 'standaloneContraction'

#
# Acceleration and Decelerations History
#
ACCELERATION_PRESENT = 'AccelerationsPresent'
EARLY_DECELERATIONS_PRESENT = 'EarlyDecelerationsPresent'

ANY_LATE_DECELERATIONS = 'AnyLateDecelerations'
REPETITIVE_LATE_DECELERATIONS_20 = 'RepetitiveLateDecelerations-20min'
REPETITIVE_LATE_DECELERATIONS_30 = 'RepetitiveLateDecelerations-30min'

OCCASIONAL_VARIABLE_DECELERATIONS = 'OccasionalVariableDecelerations'
REPETITIVE_VARIABLE_DECELERATIONS = 'RepetitiveVariableDecelerations'

OCCASIONAL_COMPLICATED_VARIABLE_DECELERATIONS = 'OccasionalComplexVariableDecelerations'
REPETITIVE_COMPLICATED_VARIABLE_DECELERATIONS = 'RepetitiveComplexVariableDecelerations'

MARKED_PROLONGED_DECELERATION_PRESENT = 'MarkedProlongedDecelerationPresent'


#
# Contraction History
#

CONTRACTION = 'contraction'    # actual contraction event
CONTRACTIONS = 'contractions'    # actual contraction event
