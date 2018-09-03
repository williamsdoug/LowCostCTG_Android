#
# Messages
#

# Enumeration of messages
DIAG_CHECK_MONITOR = 'DIAG_CHECK_MONITOR'
DIAG_NORMAL = 'DIAG_NORMAL'
DIAG_TACHYCARDIA = 'DIAG_TACHYCARDIA'
DIAG_BRADYCARDIA = 'DIAG_BRADYCARDIA'
DIAG_SEVERE_BRADYCARDIA = 'DIAG_SEVERE_BRADYCARDIA'
DIAG_FHRV_MARKED = 'DIAG_FHRV_MARKED'
DIAG_FHRV_LOW = 'DIAG_FHRV_LOW'

DIAG_MARKED_PROLONGED = 'DIAG_MARKED_PROLONGED'
DIAG_LONG_PROLONGED = 'DIAG_LONG_PROLONGED'
DIAG_PROLONGED = 'DIAG_PROLONGED'

DIAG_REPETITIVE_LATE_DECEL_LOW_VAR = 'DIAG_REPETITIVE_LATE_DECEL_LOW_VAR'
DIAG_REPETITIVE_LATE_DECEL = 'DIAG_REPETITIVE_LATE_DECEL'
DIAG_LATE_DECEL = 'DIAG_LATE_DECEL'

DIAG_REPETITIVE_PERIODIC_VARIABLE = 'DIAG_REPETITIVE_PERIODIC_VARIABLE'

DIAG_ACCEL_MISSING = 'DIAG_ACCEL_MISSING'
DIAG_TACHYSYSTOLE = 'DIAG_TACHYSYSTOLE'
DIAG_NO_CONTRACTIONS = 'DIAG_NO_CONTRACTIONS'



# Diag meetinga for IA
DIAG_CONTINUE_IA = 'DIAG_CONTINUE_IA'
DIAG_COMPLETE_IA = 'DIAG_COMPLETE_IA'



# DIAG_PLACENTAL_INSUFFICIENCY = 'DIAG_PLACENTAL_INSUFFICIENCY'
# DIAG_ABRUPTION = 'DIAG_ABRUPTION'
#
# DIAG_CORD_COMPRESSION = 'DIAG_CORD_COMPRESSION'
#
# DIAG_OBSTRUCTED_LABOR = 'DIAG_OBSTRUCTED_LABOR'



# Message details
ALL_DIAGNOSTIC_MESSAGES = {
    DIAG_CHECK_MONITOR: {'text': 'No recent updates from patient monitor', 'order': 1},
    DIAG_NORMAL: {'text': 'Normal for this fetus', 'order': 1},
    DIAG_TACHYCARDIA: {'text': 'Tachycardia: Fetal heart rate above 160', 'order': 2},
    DIAG_BRADYCARDIA: {'text': 'Bradycardia: Fetal heart rate below 110', 'order': 2},
    DIAG_SEVERE_BRADYCARDIA: {'text': 'Severe Bradycardia: Fetal heart rate above 100', 'order': 3},

    DIAG_FHRV_MARKED: {'text': 'Marked fetal heart rate variability for over 30 min', 'order': 2},
    DIAG_FHRV_LOW: {'text': 'Low fetal heart rate variability for over 50 min', 'order': 2},

    DIAG_MARKED_PROLONGED: {'text': 'URGENT: Prolonged Deceleleration with severe bradycardia', 'order': 4},
    DIAG_LONG_PROLONGED: {'text': 'Prolonged Deceleleration over 5 min', 'order': 3},
    DIAG_PROLONGED: {'text': 'Prolonged Deceleleration present', 'order': 2},

    DIAG_REPETITIVE_LATE_DECEL: {'text': 'Repetitive Late Decelelerations', 'order': 3},
    DIAG_REPETITIVE_LATE_DECEL_LOW_VAR: {'text': 'Repetitive Late Decelelerations with low variability', 'order': 4},
    DIAG_LATE_DECEL: {'text': 'Late Decelelerations present', 'order': 2},

    DIAG_REPETITIVE_PERIODIC_VARIABLE: {'text': 'Repetitive Variable Decelelerations', 'order': 3},

    DIAG_ACCEL_MISSING: {'text': 'Accelerations absent for over 50 min', 'order': 2},

    DIAG_TACHYSYSTOLE: {'text': 'Tachysystole: Contraction rate > 5 per 10 min', 'order': 2},
    DIAG_NO_CONTRACTIONS: {'text': 'No recent contractions', 'order': 2},

    DIAG_CONTINUE_IA: {'text': 'Continue monitoring of patient', 'order': 1},
    DIAG_COMPLETE_IA: {'text': 'IA Testing Complete', 'order': 1},

    # DIAG_PLACENTAL_INSUFFICIENCY: {'text': 'Placental insufficiency', 'order': 1},
    # DIAG_ABRUPTION: {'text': 'Abruption', 'order': 2},
    # DIAG_CORD_COMPRESSION: {'text': 'Potential cord compression', 'order': 2},
}

