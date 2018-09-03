# coding: utf-8

#
#  Copyright Douglas Williams, 2018
#  All Rights Reserved
#

#
# To Do:
#
#  1) Review (re)Analyze
#

from kivy.config import Config
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')
import kivy
import kivy.utils

# from kivy.app import App
from AppWithParams import AppWithParams
from kivy.lang import Builder

from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.dropdown import DropDown
from kivy.uix.popup import Popup
from kivy.properties import ObjectProperty, StringProperty
from kivy.uix.label import Label
from kivy.uix.settings import SettingsWithSidebar

from dropdown_button_list import DropdownButtonList

import os
from os.path import sep, expanduser, isdir, dirname

import sys
from pprint import pprint
import pickle as pickle
import uuid
import time
import math

from settingsjson import all_settings
from persistence import RecordingsPersistenceManager, PatientPersistenceManager, get_db_path, \
    DB_NAME, REMOTE_DB_NAME, DEMO_DB_NAME
from recorder_ui import PlotPopup

from libPing import ping
from libTocopatchDevice import ping_tocopatch

from paramsThresholdsHR import *

NoneType = type(None)

RECORDINGS_DIR = ''  # will be filled in during initialization
SOFTWARE_VERSION = '0.0.2'

PATIENT_DATA = {}


# Create both screens. Please note the root.manager.current: this is how
# you can control the ScreenManager from kv. Each screen has by default a
# property manager that gives you the instance of the ScreenManager used.
Builder.load_string("""

<PingPopup>:
    auto_dismiss: False
    Button:
        text: 'Close'
        on_release: root.dismiss()

<Controller>:
    recording: recordingID
    patient: patientID
    patient_uuid_display: patient_uuid_display
    patient_comment_display: patient_comment_display
    recording_uuid_display: recording_uuid_display

    BoxLayout:
        orientation:  'vertical'
            
        # Banner
        BoxLayout:
            orientation:  'horizontal'
            size_hint: 1, .15
            Widget:

            Button:
                text: 'Ping'
                size_hint: .25, 1
                on_press: 
                    root.perform_ping()
                    
            Widget:
                size_hint: 0.05, 1

            Button:
                text: 'Settings'
                size_hint: .25, 1
                on_press: 
                    print 'settings pressed'
                on_release: app.open_settings()
            
        Widget:
            size_hint: 1, .05
            
        BoxLayout:
            orientation:  'horizontal'
            
            BoxLayout:
                orientation:  'vertical'
            
                # Patient Information Area
                BoxLayout:
                    orientation:  'horizontal'
                    size_hint: 1, .3
                    Label:
                        text: 'Patient:'
                        bold: True
                        font_size: '18sp'
                        size_hint: .2, 1

                    DropdownButtonList:
                        id: patientID
                        size_hint: 0.85, 1
                
                Widget:
                    size_hint: 1, 0.05
                    
                BoxLayout:
                    orientation:  'horizontal'
                    size_hint: 1, .2

                    Button:
                        text: 'Create'
                        on_press: root.create_patient()
                    
                    Widget:
                        size_hint: 0.05, 1
                        
                    Button:
                        text: 'Edit'
                        on_press: root.edit_current_patient()
                        #on_press: root.manager.current = 'recording'
                
                    Widget:
                        size_hint: 0.05, 1
                        
                    Button:
                        text: 'Delete' 
                        on_press: root.delete_current_patient()
              
                # Spacing  
                Widget:
                    size_hint: 1, .05
                
                BoxLayout:
                    orientation:  'horizontal'
                    size_hint: 1, .15
                    Label:
                        text: 'UUID:'
                        size_hint: 0.1, 1
                    Label:
                        id: patient_uuid_display
                        text: ''
                        text_size: self.width, None
                        halign: 'left'
                        size_hint: 0.8, 1
            
                # Spacing  
                Widget:
                    size_hint: 1, .3
                
                # Recording Information Area
                BoxLayout:
                    orientation:  'horizontal'
                    size_hint: 1, .3
                    Label:
                        text: 'Recording:'
                        bold: True
                        font_size: '18sp'
                        size_hint: .2, 1
                        
                    DropdownButtonList:
                        id: recordingID
                        size_hint: 0.85, 1
    
                Widget:
                    size_hint: 1, 0.05

                BoxLayout:
                    orientation:  'horizontal'
                    size_hint: 1, .2
                    
                    Button:
                        text: 'Record'
                        on_press: root.create_popup('record')
                    
                    Widget:
                        size_hint: 0.05, 1

                    Button:
                        text: 'View'
                        on_press: root.create_popup('view')

                    Widget:
                        size_hint: 0.05, 1

                    Button:
                        text: 'Delete'
                        on_press: 
                            print 'delete pressed'
                            root.delete_current_recording()

                Widget:
                    size_hint: 1, 0.05

                BoxLayout:
                    orientation:  'horizontal'
                    size_hint: 1, .2
    
                    Button:
                        text: 'Simulate CM'
                        on_press: root.create_popup('simulate')
                        #disabled: True

                    Widget:
                        size_hint: 0.05, 1

                    Button:
                        text: 'Simulate IA'
                        on_press: root.create_popup('simulate_ia')
                        #disabled: True

                    Widget:
                        size_hint: 0.05, 1
                        
                    Widget:     
      
                BoxLayout:
                    orientation:  'horizontal'
                    size_hint: 1, .15
                    Label:
                        text: 'UUID:'
                        size_hint: 0.1, 1
                    Label:
                        id: recording_uuid_display
                        text: ''
                        text_size: self.width, None
                        halign: 'left'
                        size_hint: 0.8, 1
                        
                Widget:    # Hack to force vertical justify
          
            Widget:
                size_hint: 0.05, 1
            
            BoxLayout:
                orientation:  'vertical'
                size_hint: 0.6, 1
                
                Label:
                    text: 'Comments:'
                    bold: True
                    font_size: '18sp'
                    size_hint_y: None
                    #text_size: self.width, None
                    height: self.texture_size[1]
                    #size_hint: 0.2, 1
                
                Label:
                    id: patient_comment_display
                    text: ''
                    #size_hint: 0.8, 1
                    #valign: 'top'
                    # option 1
                    #text_size: self.size
                    # option 2
                    size_hint_y: None
                    text_size: self.width, None
                    height: self.texture_size[1]
                Widget
            
            
<PatientPopup>:
    first_name: first_nameID
    last_name: last_nameID
    age: ageID
    uuid: uuid_ID
    comment_field: comment_ID

    title: 'Enter Patient Data'
    GridLayout:
        cols: 2
        rows: 6
        padding: 10
        spacing: 10
        
        Label:
            text:  'First Name'
        TextInput:
            id: first_nameID
            
        Label:
            text:  'Last Name'
        TextInput:
            id: last_nameID
            
        Label:
            text:  'Age'
        TextInput:
            id: ageID
            
        Label:
            text:  'Comments'
        TextInput:
            id: comment_ID
            
        Label:
            text:  'UUID'
        Label:
            id: uuid_ID
            
        Button:
            text: 'OK'
            on_press: root.finish('ok')
        Button:
            text: 'Cancel'
            on_press: root.finish('cancel')
        

<ConfirmDeletePopup>:
    first_name: first_nameID
    last_name: last_nameID
    age: ageID
    uuid: uuid_ID
    
    auto_dismiss: False
    title: 'Confirmation'
    BoxLayout:
        orientation: 'vertical'
        BoxLayout:
            orientation: 'vertical'
            size_hint: 1, 0.9
            Label:
                text:  'Are you sure you want to delete this patient?'
            GridLayout:
                cols: 2
                rows: 5
                padding: 10
                spacing: 10
                Label:
                    text:  'First Name'
                Label:
                    id: first_nameID
                Label:
                    text:  'Last Name'
                Label:
                    id: last_nameID
                Label:
                    text:  'Age'
                Label:
                    id: ageID
                Label:
                    text:  'UUID'
                Label:
                    id: uuid_ID
        GridLayout:
            size_hint: 1, 0.1
            cols: 2
            rows: 1
            Button:
                text: 'OK'
                on_release: root.process_ok()
            Button:
                text: 'Cancel'
                on_release: root.dismiss()        


<ConfirmRecordingDeletePopup>:
    date: dateID
    duration: durationID
    uuid: uuid_ID
    
    auto_dismiss: False
    title: 'Confirmation'
    BoxLayout:
        orientation: 'vertical'
        BoxLayout:
            orientation: 'vertical'
            size_hint: 1, 0.9
            Label:
                text:  'Are you sure you want to delete this recording?'
            GridLayout:
                cols: 2
                rows: 3
                padding: 10
                spacing: 10
                Label:
                    text:  'Date'
                Label:
                    id: dateID
                Label:
                    text:  'Duration'
                Label:
                    id: durationID
                Label:
                    text:  'UUID'
                Label:
                    id: uuid_ID
        GridLayout:
            size_hint: 1, 0.1
            cols: 2
            rows: 1
            Button:
                text: 'OK'
                on_release: root.process_ok()
            Button:
                text: 'Cancel'
                on_release: root.dismiss()

""")


class PingPopup(Popup):
    def __init__(self, ip, callback=None):
        ret = False
        if ping(ip):
            if ping_tocopatch(ip):
                title = 'Ping of {} PASSED'.format(ip)
                ret = True
            else:
                title = 'Connection to {} FAILED'.format(ip)
        else:
            title = 'Ping of {} FAILED'.format(ip)

        if callback is not None:
            callback(ret)

        super(PingPopup, self).__init__(title=title, size_hint=(None, None), size=(600, 200))


class ConfirmDeletePopup(Popup):
    def __init__(self, callback, patient={}, *args, **kwargs):
        super(ConfirmDeletePopup, self).__init__(*args, **kwargs)
        self.callback = callback
        self.first_name.text = patient['first_name']
        self.last_name.text = patient['last_name']
        self.age.text = patient['age']
        self.uuid.text = patient['uuid']

    def process_ok(self):
        self.dismiss()
        self.callback()


class PatientPopup(Popup):
    first_name = ObjectProperty()
    last_name = ObjectProperty()
    age = ObjectProperty()
    comment_field = ObjectProperty()
    uuid = ObjectProperty()

    def __init__(self, callback, data={}, *args, **kwargs):
        super(PatientPopup, self).__init__(*args, **kwargs)
        self.callback = callback

        pprint(data)

        self.first_name.text = data['first_name'] if 'first_name' in data else ''
        self.last_name.text = data['last_name'] if 'last_name' in data else ''
        self.age.text = data['age'] if 'age' in data else ''
        self.comment_field.text = data['comment'] if 'comment' in data else ''
        self.uuid.text = data['uuid'] if 'uuid' in data else str(uuid.uuid4())
        print 'returned from init'

    def finish(self, reason):
        print 'reason:', reason
        if reason == 'cancel':
            result = None
        else:
            # Correctness tests
            if self.first_name.text == '' or self.last_name.text == '':
                return
            if self.age.text == '':
                self.age.text = '?'
            # if not self.age.text.isdigit():
            #     self.age.text = '**invalid**'
            #     return

            result = {'first_name': self.first_name.text,
                      'last_name': self.last_name.text,
                      'age': self.age.text,
                      'comment': self.comment_field.text,
                      'uuid': self.uuid.text}

        self.dismiss()
        self.callback(result)


class ConfirmRecordingDeletePopup(Popup):
    def __init__(self, callback, entry={}, *args, **kwargs):
        super(ConfirmRecordingDeletePopup, self).__init__(*args, **kwargs)
        self.callback = callback
        self.date.text = time.ctime(entry['date'])
        self.duration.text = '{:0.1f} min'.format(entry['duration'])
        self.uuid.text = entry['uuid']

    def process_ok(self):
        self.dismiss()
        self.callback()


class Controller(FloatLayout):
    patient = ObjectProperty()
    recording = ObjectProperty()
    patient_uuid_display  = ObjectProperty()
    patient_comment_display  = ObjectProperty()
    recording_uuid_display  = ObjectProperty()

    def __init__(self, *args, **kwargs):
        super(Controller, self).__init__(*args, **kwargs)
        #self.patient_mgr = PatientPersistenceManager(self.patient, on_update=self.patient_selection_changed)
        #self.recording_mgr = RecordingsPersistenceManager(self.recording, on_update=self.recording_selection_changed)
        #self.patient_mgr.load_data()
        self.mode = None

        # Code from recorder_ui standalone tester

        self.rec_uuid = None
        self.user_uuid = None
        self.metadata_file = None
        self.audio_file = None
        self.toco_file = None
        self.tocopatch_connection_validated = False


    def on_startup(self):
        self.patient_mgr = PatientPersistenceManager(self.patient, on_update=self.patient_selection_changed)
        self.recording_mgr = RecordingsPersistenceManager(self.recording, on_update=self.recording_selection_changed)
        pprint(AppWithParams.params)

        self.patient_mgr.load_data()
        self.recording_uuid_display.text = ''


    def config_change(self):
        print 'App params'
        pprint(ControllerApp.params)


    #
    # Patient data management
    #

    def patient_selection_changed(self, patient_uuid):
        print '*'*40
        print 'patient_selection_changed:', patient_uuid
        print '*'*40
        self.recording_mgr.change_folder(patient_uuid)
        self.patient_comment_display.text = ''
        self.patient_uuid_display.text = ''
        self.recording_uuid_display.text = ''

        if patient_uuid is not None:
            self.patient_uuid_display.text = patient_uuid
            selection =  self.patient_mgr.get_selection()
            if selection and 'comment' in selection:
                self.patient_comment_display.text =  selection['comment']
        else:
            self.recording_mgr.clear()


    def create_patient(self):
        """Create new patient entry"""
        self.edit_patient({})


    def edit_current_patient(self):
        """Update existing patient entry"""
        current_patient = self.patient_mgr.get_selection()
        if current_patient is not None:
            self.edit_patient(current_patient)
        return


    def edit_patient(self, patient_data):
        """Common patient data popup routine for both create and edit operations """
        popup = PatientPopup(self.patientPopupClosed, data=patient_data,
                             #size_hint=(None, None), size=(600, 400)
                             )
        popup.open()


    def patientPopupClosed(self, patient_record):
        """callback routine for patient data entry"""
        print 'patientPopupClosed received:', patient_record
        self.patient_mgr.update_selection(patient_record)


    def delete_current_patient(self):
        """Removes entry associated with current patient"""
        selection = self.patient_mgr.get_selection()
        if selection is not None:
            # Confirm with user prior to deletion
            ConfirmDeletePopup(self.perform_patient_delete, patient=selection).open()


    def perform_patient_delete(self):
        """perform actual patient data deletion after upon user confirmation"""
        current_patient = self.patient_mgr.get_selection()
        if current_patient and 'uuid' in current_patient:
            self.recording_mgr.remove_folder(current_patient['uuid'])
        self.patient_mgr.delete_selection()


    #
    # Prior Recordings Data Management functions -- select, edit and delete
    #

    def recording_selection_changed(self, recording_uuid):
        print '*'*40
        print 'recording_selection_changed:', recording_uuid
        print '*'*40
        if recording_uuid is not None:
            self.recording_uuid_display.text = recording_uuid



    def delete_current_recording(self):
        """Removes entry associated with current patient"""
        selection = self.recording_mgr.get_selection()
        if selection is not None:
            # Confirm with user prior to deletion
            ConfirmRecordingDeletePopup(self.perform_recording_delete,
                                        entry=selection).open()


    def perform_recording_delete(self):
        """perform actual recording data deletion after upon user confirmation"""

        # ensure that we have an associated patient
        user_uuid = self.patient_mgr.get_selected_uuid()
        if user_uuid is None:
            return
        rec_uuid = self.recording_mgr.get_selected_uuid()
        if rec_uuid is None:
            return

        file_path = get_db_path(user_uuid=user_uuid, rec_uuid=rec_uuid)
        metadata_file = file_path+'.p'
        toco_file = file_path+'.csv'
        audio_file = file_path + '.wav'

        self.recording_mgr.delete_selection()
        if metadata_file and os.path.exists(metadata_file):
            os.remove(metadata_file)
        if audio_file and os.path.exists(audio_file):
            os.remove(audio_file)
        if toco_file and os.path.exists(toco_file):
            os.remove(toco_file)



    #
    # Detailed Recording Functions -- View and Record
    #


    def create_popup(self, mode, *args, **kwargs):
        print 'create_popup pressed', mode
        self.mode = mode      # save for callback

        # ensure that we have an associated patient
        self.user_uuid = self.patient_mgr.get_selected_uuid()
        if self.user_uuid is None:
            return

        if mode in ['record', 'import', 'import_live']:
            self.rec_uuid = str(uuid.uuid4())
        else:
            self.rec_uuid = self.recording_mgr.get_selected_uuid()
            if self.rec_uuid is None:
                return

        file_path = get_db_path(user_uuid=self.user_uuid, rec_uuid=self.rec_uuid)
        self.metadata_file = file_path+'.p'
        self.audio_file = file_path + '.wav'
        self.toco_file = file_path+'.csv'

        if mode == 'record':
            self.do_record()
        elif mode == 'view':
            p = PlotPopup(mode, metadata_file=self.metadata_file,
                          title='Viewing: {}/{}'.format(self.user_uuid, self.rec_uuid))
            p.open()
        elif mode in ['simulate', 'simulate_ia']:
            p = PlotPopup(mode, metadata_file=self.metadata_file,
                          title='Simulating: {}/{}'.format(self.user_uuid, self.rec_uuid))
            p.open()
        elif mode == 'analyze':
            #fname = file_path + '.wav'
            p = PlotPopup(mode, audio_file=self.audio_file,
                          metadata_file=self.metadata_file, toco_file=self.toco_file,
                          title='Analyzing: {}/{}'.format(self.user_uuid, self.rec_uuid))
            p.open()
        else:
            raise Exception('Unknown plot type')


    def do_record(self):
        """Initiates recording, also used for recording restart"""
        ip = AppWithParams.params['ip_address']

        if AppWithParams.params['tocopatch_enable'] and not self.tocopatch_connection_validated:
            if ping_tocopatch(ip):
                self.tocopatch_connection_validated = True
                time.sleep(2)
            else:
                AppWithParams.params['tocopatch_enable'] = False
                self.tocopatch_connection_validated = False
                p = Popup(title='TocoPatch Connection Failed',
                          content=Label(text='TocoPatch temporarily disabled\n'+
                                        'Upcated config and verify with Ping'),
                          size_hint=(None, None), size=(600, 400))

                p.open()
                return

        #print 'tocopatch_connection_validated', self.tocopatch_connection_validated
        p = PlotPopup(self.mode, metadata_file=self.metadata_file, audio_file=self.audio_file,
                      toco_file=self.toco_file,
                      restart_callback=self.do_record, completion_callback=self.record_completion,
                      title='Recording')
        p.open()



    def record_completion(self, results):
        # Callback at the end of the recording
        print 'Recording and/or import done'
        entry = {'date': results['start_time'], 'duration': results['recording_duration'],  'uuid': self.rec_uuid}
        self.recording_mgr.update_selection(entry)
        pass


    def recording_finished(self, results):
        self.bp_thread = None
        print 'recording_finished'
        pprint(results)


    #
    # Ping Operation
    #


    def perform_ping(self):
        ip = AppWithParams.params['ip_address']
        popup = PingPopup(ip, callback=self.ping_callback)
        popup.open()

    def ping_callback(self, response):
        print 'ping popup returned', response
        AppWithParams.params['tocopatch_enable'] = response
        self.tocopatch_connection_validated = response



class ControllerApp(AppWithParams):

    # params = {}

    def build(self):
        self.setConfigConstants()
        self.title = 'Low Cost CTG'
        self.controller = Controller()
        # this_controller.customize()
        self.settings_cls = SettingsWithSidebar
        return self.controller

    def on_start(self):
        self.summarize_config()
        self.controller.on_startup()

    def on_stop(self):
        print 'called on_stop'
        # stop_pinger()
        for child in self.root_window.children:
            if isinstance(child, PlotPopup):
                #print 'Found PlotPopup', child
                child.cleanup_on_stop()


    def setConfigConstants(self):
        self.config.set('about', 'description', 'Low Cost CTG Audio Extractor')
        self.config.set('about', 'limitations', 'Prototype software in active development.')
        self.config.set('about', 'version', SOFTWARE_VERSION)
        self.config.set('about', 'copyright', 'Doug Williams, 2018')
        pass

    def build_config(self, config):
        for section, desc, json_spec, defaults in all_settings:
            config.setdefaults(section, defaults)


    def build_settings(self, settings):
        for section, desc, json_spec, defaults in all_settings:
            settings.add_json_panel(desc, self.config, data=json_spec)


    def on_config_change(self, config, section, key, value):
        print 'on_config_change:', section, key, value
        self.summarize_config()


    def summarize_config(self):
        print 'called summarize_config'


        self.params['enable_realtime_pattern'] = self.getSetting('general', 'enable_realtime_pattern_detection', isBoolean=True)

        self.params['ip_address'] = self.getSetting('tocopatch', 'ip_address')
        self.params['readonly'] = self.getSetting('storage', 'readonly', isBoolean=True)

        if self.getSetting('thresholds', 'custom_range', isBoolean=True):
            self.params['tachycardia'] = self.getSetting('thresholds', 'tachycardia', isInt=True)
            self.params['bradycardia'] = self.getSetting('thresholds', 'bradycardia', isInt=True)
        elif self.getSetting('thresholds', 'adult', isBoolean=True):
            self.params['tachycardia'] = THRESH_ADULT_TACHYCARDIA
            self.params['bradycardia'] = THRESH_ADULT_BRADYCARDIA
        else:
            self.params['tachycardia'] = THRESH_FETAL_TACHYCARDIA
            self.params['bradycardia'] = THRESH_FETAL_BRADYCARDIA

        self.params['readonly'] = self.getSetting('storage', 'readonly', isBoolean=True)

        # TODO:  Adapt to use get_base_dir()
        if sys.platform == 'win':
            user_base = dirname(expanduser('~'))
        else:
            user_base = expanduser('~')
        user_base= user_base + sep + 'Documents'

        if self.getSetting('storage', 'custom_path', isBoolean=True):
            self.params['recording_path'] = self.getSetting('storage', 'recording_path')
        elif self.getSetting('storage', 'remote', isBoolean=True):
            self.params['recording_path'] = user_base  +  sep + REMOTE_DB_NAME
        elif self.getSetting('storage', 'demo', isBoolean=True):
            self.params['recording_path'] = user_base  +  sep + DEMO_DB_NAME
        else:
            self.params['recording_path'] = user_base  + sep + DB_NAME

        self.params['disable_filter'] = self.getSetting('extractor', 'disable_filter', isBoolean=True)

        if self.getSetting('extractor', 'enable_custom', isBoolean=True):
            extractor_params = {}

            for k in ['duration', 'interval', 'corr_thresh']:
                val = self.getSetting('extractor', k, isFloat=True)
                if val != -1:
                    extractor_params[k] = val
            self.params['extractor'] = extractor_params

        self.params['ip_address'] = self.getSetting('tocopatch', 'ip_address')
        self.params['tocopatch_enable'] = self.getSetting('tocopatch', 'tocopatch_enable', isBoolean=True)
        self.params['tocopatch_annotate'] = self.getSetting('tocopatch', 'tocopatch_annotate', isBoolean=True)

        pprint(self.params)
        self.controller.config_change()


def get_base_dir():
    if kivy.utils.platform == 'android':
        return '/sdcard'
    elif getattr(sys, 'frozen', False):
         # running in a bundle
        bundle_dir = sys._MEIPASS
        print 'running frozen -- bundle_dir', bundle_dir
        return bundle_dir
    else:
        # running live
        if sys.platform == 'win':
            user_base = dirname(expanduser('~'))
        else:
            user_base = expanduser('~')
        user_base= user_base + sep + 'Documents'
        return user_base


if __name__ == '__main__':
    ControllerApp().run()
