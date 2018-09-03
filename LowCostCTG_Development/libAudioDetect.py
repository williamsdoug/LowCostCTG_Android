# coding: utf-8
#
#  Copyright Douglas Williams, 2018
#  All Rights Reserved
#


import pyaudio
from pprint import pprint


def audio_detect(sampling_rate=8000):
    """Determines available audio devices. Includes flags for windows and mac"""
    results = []

    p = pyaudio.PyAudio()
    info = p.get_host_api_info_by_index(0)
    numdevices = info.get('deviceCount')
    last_input = -1
    last_output = -1

    # for each audio device, determine if is an input or an output and add it to the appropriate list and dictionary
    for i in range(0, numdevices):
        desc = p.get_device_info_by_host_api_device_index(0, i).get('name')

        entry = {'chan': i, 'desc':desc,
                 'isDoppler': 'doppler' in desc.lower(),
                 'isSpeaker': 'speaker' in desc.lower(),
                 'isUSB': 'usb' in desc.lower(),
                 'isHead': 'head' in desc.lower(),
                 'isMicrophone': 'micro' in desc.lower(),
                 'isRealtek': 'realtek' in desc.lower(),
                 'isBuiltin': 'built' in desc.lower(),
                 'isMapper': 'mapper' in desc.lower()
                 }
        results.append(entry)
        if False:
            print
            print 'device:', i
            pprint(p.get_device_info_by_host_api_device_index(0, i))
            pprint(p.get_device_info_by_index(i))

        if p.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels') > 0:
            print "Input Device id ", i, " - ", p.get_device_info_by_host_api_device_index(0, i).get('name')
            last_input = i
            entry['isInput'] = True

            devinfo = p.get_device_info_by_index(i)
            if p.is_format_supported(8000.0,  # Sample rate
                                     input_device=devinfo["index"],
                                     input_channels=devinfo['maxInputChannels'],
                                     input_format=pyaudio.paInt16):
                entry['supports8K'] = True
            else:
                entry['supports8K'] = False


        if p.get_device_info_by_host_api_device_index(0, i).get('maxOutputChannels') > 0:
            print "Output Device id ", i, " - ", p.get_device_info_by_host_api_device_index(0, i).get('name')
            last_output = i
            entry['isOutput'] = True

            devinfo = p.get_device_info_by_index(i)
            if p.is_format_supported(8000.0,  # Sample rate
                                     output_device=devinfo["index"],
                                     output_channels=devinfo['maxOutputChannels'],
                                     output_format=pyaudio.paInt16):
                entry['supports8K'] = True
            else:
                entry['supports8K'] = False

    p.terminate()
    for r in results:
        if 'isInput' not in r:
            r['isInput'] = False

        if 'isOutput' not in r:
            r['isOutput'] = False

        if 'isInput' in r and r['isUSB']:
            r['isHead'] = False
            r['isMicrophone'] = False

        if 'isInput' in r and r['isBuiltin'] and not r['isUSB']:
            r['isHead'] = True
            r['isMicrophone'] = True

        if 'isOutput' in r:
            r['isSpeaker'] = (r['isSpeaker'] and not r['isUSB']
                              or r['isBuiltin'])

    # Consolidate assessments

    return results


def select_preferred_io(results):
    """Selects preferred input and output for recording.  Doesn't allow use of same device class"""
    # try external input device first
    candidates = [x for x in results if x['isDoppler']]
    if candidates:
        preferred_input = candidates[0]
    else:
        candidates = [x for x in results if x['isInput'] and x['isUSB']]
        if candidates:
            preferred_input = candidates[0]
        else:
            candidates = [x for x in results if x['isInput'] and not x['isBuiltin']]
            if candidates:
                preferred_input = candidates[0]
            else:
                candidates = [x for x in results if x['isInput'] and x['isHead']]
                if candidates:
                    preferred_input = candidates[0]
                else:
                    preferred_input = {'chan':None}

    print 'Preferred Input:'
    pprint(preferred_input)

    # try internal output device first
    candidates = [x for x in results if x['isOutput'] and x['isSpeaker']]
    if candidates:
        preferred_output = candidates[0]
    else:
        candidates = [x for x in results if x['isOutput'] and x['isUSB']]
        if candidates:
            preferred_output = candidates[0]
        else:
            preferred_output = {'chan':None}

    if preferred_input['isBuiltin']:
        preferred_output= {'chan': None}

    print 'Preferred Output:'
    pprint(preferred_output)

    return preferred_input['chan'], preferred_output['chan']


def select_preferred_output(results):
    # try internal output device first
    candidates = [x for x in results if x['isOutput'] and x['isSpeaker']]
    if candidates:
        preferred_output = candidates[0]
    else:
        candidates = [x for x in results if x['isOutput'] and x['isHead']]
        if candidates:
            preferred_output = candidates[0]
        else:
            candidates = [x for x in results if x['isOutput'] and x['isUSB']]
            if candidates:
                preferred_output = candidates[0]
            else:
                preferred_output = {'chan':None}

    print 'Preferred Output:'
    pprint(preferred_output)

    return preferred_output['chan']


if __name__ == '__main__':
    results = audio_detect(sampling_rate=8000)
    print '*** Input Devices ***'
    for entry in results:
        if entry['isInput']:
            pprint(entry)
            print
    print
    print '*** Output Devices ***'
    for entry in results:
        if entry['isOutput']:
            pprint(entry)
            print
    print
    print
    select_preferred_io(results)
