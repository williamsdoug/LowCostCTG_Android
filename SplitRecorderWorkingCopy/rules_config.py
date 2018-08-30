# -*- coding: utf-8 -*-

#
#  Copyright Douglas Williams, 2017-2018
#  All Rights Reserved
#

# Configuration Constants used by Rules Engine and Rules Set


from rules_constants import *

#
# Fetal Heart Rate
#

FHR_CLASSIFICATION = [
    {'name': SEVERE_FETAL_BRADYCARDIA,  'bounds': [None, 100]},
    {'name': BORDERLINE_FETAL_BRADYCARDIA,    'bounds': [101, 110]},
    {'name': FETAL_HEART_RATE_NORMAL,   'bounds': [110, 160]},
    {'name': FETAL_TACHYCARDIA,    'bounds': [161, None]},
    ]

FETAL_BRADYCARDIA = [SEVERE_FETAL_BRADYCARDIA, BORDERLINE_FETAL_BRADYCARDIA]


#
# Fetal Heart Rate Variability
#

FHR_VARIABILITY_CLASSIFICATION = [
    {'name': HIGH_VARIABILITY,   'bounds':[26, None]},
    {'name': NORMAL_VARIABILITY, 'bounds':[5, 25]},
    {'name': LOW_VARIABILITY,    'bounds':[None, 5]},
    ]

FHR_VARIABILITY_HISTORY = [
    {'name': PROLONGED_LOW_VARIABILITY_50,   'metric': LOW_VARIABILITY,  'duration':50, 'isSustained': True },
    {'name': PROLONGED_LOW_VARIABILITY_20, 'metric': LOW_VARIABILITY,  'duration':20, 'isSustained': True },
    {'name': PROLONGED_HIGH_VARIABILITY_30,  'metric': HIGH_VARIABILITY, 'duration':30, 'isSustained': True},
    ]


#
# Episodic Fetal Heart Rate Patterns
#

# Map output of Pattern Detector output to vocabulary used by rules
MAP_EPISODIC_PATTERN_VOCABULARY = {
    'prolonged': [PROLONGED_DECELERATION, LONGER_PROLONGED_DECELERATION, LONGER_MARKED_PROLONGED_DECELERATION],
    'variable': VARIABLE_DECELERATION,
    'variable_periodic': PERIODIC_VARIABLE_DECELERATION,
    'late_decel': LATE_DECELERATION,
    'mild_late_decel':  LATE_DECELERATION,
    'early_decel':  EARLY_DECELERATION,
    #'shallow_early_decel': EARLY_DECELERATION,
    'acceleration':  ACCELERATION,
    #'borderline_acceleration': ACCELERATION,
}


EPISODIC_PATTERN_VOCABULARY = [
    ACCELERATION,
    PROLONGED_DECELERATION,
    LONGER_PROLONGED_DECELERATION,
    LONGER_MARKED_PROLONGED_DECELERATION,
    VARIABLE_DECELERATION,
]



# TODO:  What is the correct duration for prolonged deceleration alerting ?

EPISODIC_PATTERN_HISTORY = [
    {'name': ACCELERATION_PRESENT, 'metric': ACCELERATION,
     'duration':50, 'bounds': [1, None] },
    {'name': PROLONGED_DECELERATION_PRESENT, 'metric': PROLONGED_DECELERATION,
     'duration':30, 'bounds': [1, None] },
    {'name': LONGER_PROLONGED_DECELERATION_PRESENT, 'metric': LONGER_PROLONGED_DECELERATION,
     'duration':30, 'bounds': [1, None] },
    {'name': LONGER_MARKED_PROLONGED_DECELERATION_PRESENT, 'metric': LONGER_MARKED_PROLONGED_DECELERATION,
     'duration':30, 'bounds': [1, None] },
]




#
# Periodic Patterns
#
MAP_PERIODIC_PATTERN_VOCABULARY = {
    'variable_periodic': PERIODIC_VARIABLE_DECELERATION,
    'late_decel': LATE_DECELERATION,
    'mild_late_decel':  LATE_DECELERATION,
    'early_decel':  EARLY_DECELERATION,
    #'shallow_early_decel': EARLY_DECELERATION,
}


PERIODIC_PATTERN_VOCABULARY = [
    EARLY_DECELERATION,
    LATE_DECELERATION,
    PERIODIC_VARIABLE_DECELERATION,
    STANDALONE_CONTRACTION
]



PERIODIC_PATTERN_HISTORY = [
    {'name': ANY_LATE_DECELERATIONS,                       'metric': LATE_DECELERATION,
     'duration':20, 'bounds': [1, None] },
]


#
#  FHR Trend
#

FHR_TREND_CLASSIFICATION = [
    {'name': FHR_TREND_RISING,   'bounds':[20, None]},
    {'name': FHR_TREND_FALLING,    'bounds':[None, -20]},
    ]

#
# Contractions
#


STANDARD_REMINDERS = { ASSESSMENT_PATHOLOGICAL: 000, ASSESSMENT_SUSPICIOUS: 000, ASSESSMENT_NORMAL: 000}


rulesEngineConfig = {

    # Register available asssessment levels and precedence for each
    # entity being evaluated
    'assessmentEntities': {
        # Overall Assessments
        FETUS: {'values':STANDARD_ASSESSMENT_LEVELS, 'default': ASSESSMENT_NORMAL,
                'reminders': { ASSESSMENT_PATHOLOGICAL: 14, ASSESSMENT_SUSPICIOUS: 15, ASSESSMENT_NORMAL: 30}},

        # Individual Assessments
        FETAL_HR: {'values':STANDARD_ASSESSMENT_LEVELS, 'default': ASSESSMENT_NORMAL},
        FETAL_VAR: {'values':STANDARD_ASSESSMENT_LEVELS, 'default': ASSESSMENT_NORMAL},
        FETAL_DECELS: {'values':STANDARD_ASSESSMENT_LEVELS, 'default': ASSESSMENT_NORMAL},
        FETAL_ACCELS: {'values':ADVISORY_ASSESSMENT_LEVELS, 'default': ASSESSMENT_NORMAL},
        MATERNAL_CONTRACTIONS: {'values':ADVISORY_ASSESSMENT_LEVELS, 'default': ASSESSMENT_NORMAL},
    },

    'evaluationOrdering': [
        {'type': 'rules', 'name':'pass 0', 'prefix':'rule_P0_'},  # standalone assessments
        {'type': 'resolve', 'entities':[FETUS, FETAL_HR, FETAL_VAR, FETAL_DECELS,
                                        FETAL_ACCELS, MATERNAL_CONTRACTIONS]},
        ],

    # HACK:  Duration must be > 0
    'measurements': [
        {'name': RECORDING_DURATION, 'duration':60},     # recording duration in minutes
        {'name': FETAL_HEART_RATE_MINUTE, 'classify': FHR_CLASSIFICATION, 'duration':60},
        {'name': FETAL_HEART_RATE, 'classify': FHR_CLASSIFICATION, 'duration':60},
        {'name': FHR_VARIABILITY,  'classify': FHR_VARIABILITY_CLASSIFICATION,
         'classifyHistory': FHR_VARIABILITY_HISTORY, 'duration':60},
        {'name': EPISODIC_FHR_PATTERNS, 'vocab': EPISODIC_PATTERN_VOCABULARY,
         'classifyHistory': EPISODIC_PATTERN_HISTORY, 'duration':60},
        {'name': PERIODIC_PATTERNS, 'vocab': PERIODIC_PATTERN_VOCABULARY,
         'classifyHistory': PERIODIC_PATTERN_HISTORY, 'duration':60},
        {'name': CONTRACTIONS,  'duration':60},

    ],
    # 'measurement_to_assessment': {},
    # 'assessment_to_measurement': {},

    'assessmentToPriority': {
        ASSESSMENT_URGENT: 100,
        ASSESSMENT_PATHOLOGICAL: 80,
        ASSESSMENT_SUSPICIOUS: 60,
        ASSESSMENT_NORMAL: 0,
        ASSESSMENT_ABSENT: 0,
        ASSESSMENT_PRESENT: 0,
        ASSESSMENT_CONTINUE:20,
        ASSESSMENT_UNKNOWN: 20
    },

    'alarmToPriority': {
        ALARM_HIGH: 100,
        ALARM_LOW: 50,
        ALARM_NORMAL: 0,
    },

}