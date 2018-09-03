# coding: utf-8

#
#  Copyright Douglas Williams, 2018
#  All Rights Reserved
#


import json


##################################
#
# TocoPatch Settings
#
##################################

general_settings_json = json.dumps([
    {'type': 'bool',
     'title': 'Enable Realtime Pattern Detection',
     'desc': 'Enable pattern analysis during recording',
     'section': 'general',
     'key': 'enable_realtime_pattern_detection'},
    ])


general_defaults = {
    'enable_realtime_pattern_detection': 0,
}

tocopatch_settings_json = json.dumps([
    {'type': 'bool',
     'title': 'Enable TocoPatch',
     'desc': 'Enable use of TocoPatch for UC monitoring',
     'section': 'tocopatch',
     'key': 'tocopatch_enable'},

    {'type': 'string',
     'title': 'IP Address',
     'desc': 'IP Address of Tocopatch Device',
     'section': 'tocopatch',
     'key': 'ip_address'},

    {'type': 'bool',
     'title': 'Annotate TocoPatch',
     'desc': 'Enable manual annotation of TocoPatch signal',
     'section': 'tocopatch',
     'key': 'tocopatch_annotate'},

    ])


tocopatch_defaults = {
    'tocopatch_enable': 1,
    'ip_address': 'heartypatch.local',
    'tocopatch_annotate': 0,
}



##################################
#
# Threshold Settings
#
##################################

thresholds_settings_json = json.dumps([
    {'type': 'bool',
     'title': 'Adult Mode',
     'desc': 'Use adult HR ranges (defaults to fetal)',
     'section': 'thresholds',
     'key': 'adult'},

    {'type': 'bool',
     'title': 'Use Custom Thresholds',
     'desc': 'Enables use custom thresholds for Tachycardia/Braycardia ',
     'section': 'thresholds',
     'key': 'custom_range'},

    {'type': 'numeric',
     'title': 'Bradycardia',
     'desc': 'Upper user for Bradycardia in bpm',
     'section': 'thresholds',
     'key': 'bradycardia'},

    {'type': 'numeric',
     'title': 'Tachycardia',
     'desc': 'Lower threshold for Tachycardia in bpm',
     'section': 'thresholds',
     'key': 'tachycardia'},
    ])


thresholds_defaults = {
    'adult': '0',
    'custom_range': '0',
    'bradycardia': '-1',
    'tachycardia': '-1',
}


##################################
#
# Storage Settings
#
##################################

storage_settings_json = json.dumps([
    {'type': 'bool',
     'title': 'Read-only',
     'desc': 'Disable any writing of updates of stored data',
     'section': 'storage',
     'key': 'readonly'},

    {'type': 'bool',
     'title': 'Remote',
     'desc': 'Access remote (Malawi) database',
     'section': 'storage',
     'key': 'remote'},

    {'type': 'bool',
     'title': 'Demo',
     'desc': 'Access demo database',
     'section': 'storage',
     'key': 'demo'},

    {'type': 'bool',
     'title': 'Use Custom Path',
     'desc': 'Enables use custom directory path for ctg_db',
     'section': 'storage',
     'key': 'custom_path'},

    {'type': 'path',
     'title': 'Recording Path',
     'desc': 'Directory containing recordings file',
     'section': 'storage',
     'key': 'recording_path'},
    ])


storage_defaults = {
    'readonly': '0',
    'remote': '0',
    'demo': '0',
    'custom_path': '0',
    'recording_path': '',  # defaultPath,
}


##################################
#
# Extyractor Settings
#
##################################

extractor_settings_json = json.dumps([

    {'type': 'bool',
     'title': 'Disable Filter',
     'desc': 'Disable filtering of results',
     'section': 'extractor',
     'key': 'disable_filter'},

    {'type': 'bool',
     'title': 'Custom Extractor',
     'desc': 'Enable custom extractor settings',
     'section': 'extractor',
     'key': 'enable_custom'},

    # hack alert:  field currently string since numeric improperly handles floatingpoint numbers
    {'type': 'string',
     'title': 'Duration',
     'desc': 'Extraction duration (in sec)',
     'section': 'extractor',
     'key': 'duration'},

    # hack alert:  field currently string since numeric improperly handles floatingpoint numbers
    {'type': 'string',
     'title': 'Interval',
     'desc': 'Extraction interval (in sec)',
     'section': 'extractor',
     'key': 'interval'},

    # hack alert:  field currently string since numeric improperly handles floatingpoint numbers
    {'type': 'string',
     'title': 'Min Correlation',
     'desc': 'Minimum correlation value',
     'section': 'extractor',
     'key': 'corr_thresh'},

])


extractor_defaults = {
    'disable_filter': '0',
    'enable_custom': '0',
    'duration': '-1',
    'interval': '-1',
    'corr_thresh': '-1',
}


##################################
#
# Developer Settings
#
##################################

developer_settings_json = json.dumps([
    {'type': 'bool',
     'title': 'Developer Mode',
     'desc': 'Enable developer mode',
     'section': 'developer',
     'key': 'developer_mode'},

])


developer_defaults = {
    'developer_mode': '0',
}


##################################
#
# About Settings
#
##################################

about_settings_json = json.dumps([
    {'type': 'string',
     'title': 'Description',
     'section': 'about',
     'key': 'description'},
    {'type': 'string',
     'title': 'Limitations',
     'section': 'about',
     'key': 'limitations'},
    {'type': 'string',
     'title': 'Version',
     'section': 'about',
     'key': 'version'},
    {'type': 'string',
     'title': 'Copyright',
     'section': 'about',
     'key': 'copyright'},
])


about_defaults = {
    'description': '****',
    'limitations': '****',
    'version': '****',
    'copyright': '****'
}


##################################
#
# Overall Settings
#
##################################

all_settings = [
    ['general', 'General Optiomns', general_settings_json, general_defaults],
    ['tocopatch',  'Tocopatch Options', tocopatch_settings_json, tocopatch_defaults],
    ['thresholds', 'HR Threshold Options', thresholds_settings_json, thresholds_defaults],
    ['storage',    'Storage Options', storage_settings_json,    storage_defaults],
    ['developer',  'Developer Options', developer_settings_json,  developer_defaults],
    ['extractor',  'Extractor Options', extractor_settings_json,  extractor_defaults],
    ['about',      'About', about_settings_json, about_defaults],
]


for section, desc, json_spec, defaults in all_settings:
    pass