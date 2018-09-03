import kivy
import kivy.utils

from kivy.app import App
from kivy.lang import Builder


from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.button import Button
from kivy.uix.dropdown import DropDown
from kivy.uix.popup import Popup
from kivy.properties import ObjectProperty, StringProperty
from kivy.uix.label import Label
from kivy.clock import Clock, mainthread
import threading
import multiprocessing

from garden_filebrowser import FileBrowser
# from kivy_garden_graph import Graph, MeshLinePlot, LinePlot
# from kivy_garden_graph import SmoothLinePlot
# from plot_extensions import ScatterPlot

import os
from os.path import sep, expanduser, isdir, dirname

import sys
from pprint import pprint
import pickle as pickle
import uuid
import shutil
import time
import math

from vitals_graphs import VitalsScatterGraph, VitalsSpanGraph, VitalsMappedPointsGraph
from vitals_graphs import VitalsPanZoomGraph, VitalsGraphNavigation, addGraphLegend
from vitals_graphs import COLORS

from persistence import RecordingsPersistenceManager, PatientPersistenceManager

import pyaudio
import wave
import numpy as np
# from matplotlib import pyplot as plt
import scipy
import scipy.signal

from UltrasoundExtractHR import HibertDataTransformer, Extractor

NoneType = type(None)

RECORDINGS_DIR = ''  # will be filled in during initialization

# Thresholds used by Trend Plots
THRESH_FETAL_BRADYCARDIA = 120
THRESH_FETAL_TACHYCARDIA = 160
THRESH_LOW_VARIABILITY = 5.5
THRESH_HIGH_VARIABILITY = 25.5
THRESH_TACHYSYSTOLE = 5.5

PATIENT_DATA = {}


# Top Level Routine
class backround_processing:
    stop = threading.Event()

    def __init__(self, infile, outfile='', monitor_audio=True,
                 chuck_size=1024, enable_playback=True, default_rate=8000,
                 update_callback=None, completion_callback=None, **kwargs):
        self.infile = infile
        self.outfile = outfile
        self.monitor_audio = monitor_audio
        self.chuck_size = chuck_size
        self.enable_playback = enable_playback
        self.default_rate = default_rate
        self.update_callback = update_callback
        self.completion_callback = completion_callback
        self.extractor_args = kwargs

        self.thread = threading.Thread(target=self.processRecording)
        self.thread.start()


    def processRecording(self):

        print 'subprocess started'

        # create an audio object
        p = pyaudio.PyAudio()

        wf = wave.open(self.infile, 'rb')
        channels = wf.getnchannels()
        chuck_size = self.chuck_size * channels

        print 'Sample Width: {} Format: {}  Framerate: {}  Channels: {}'.format(wf.getsampwidth(),
                                                                                p.get_format_from_width(wf.getsampwidth()),
                                                                                wf.getframerate(), channels)

        # open stream based on the wave object which has been input.
        stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                        channels=wf.getnchannels(),
                        rate=wf.getframerate(),
                        output=self.monitor_audio)

        hd = HibertDataTransformer()
        extractor = Extractor(hd, update_callback=self.update_callback, **self.extractor_args)

        # play stream (looping from beginning of file to the end)
        data = wf.readframes(chuck_size)
        while data != '':
            # print '.',
            # sys.stdout.flush()
            segment = np.fromstring(data, '<h')
            if channels > 1:
                segment = segment[::channels]
            sigD = scipy.signal.decimate(segment, 8, zero_phase=True)
            hd.addData(sigD)  # compute envelope using hilbert (lazy)
            extractor.extract_incremental()  # now compute instantaneous HR

            if self.enable_playback:
                # writing to the stream is what *actually* plays the sound.
                stream.write(data)

            # Get Next Data
            data = wf.readframes(chuck_size)

        # cleanup stuff.
        stream.close()
        p.terminate()

        print 'subprocess finished'
        results = extractor.get_results()
        if self.completion_callback is not None:
            self.completion_callback(results)

        return


class IBI_Callback:
    def __init__(self, update_freq=1000):
        self.update_freq = update_freq
        self.last_pos = -update_freq

    def update(self, entry):
        if entry['pos'] >= self.last_pos + self.update_freq:
            self.last_pos = entry['pos']
            print '{:0.0f} bpm @ {:0.0f} sec -- cor: {:0.2f}  rel: {:0.2f}'.format(
                entry['hr'], entry['pos']/1000.0, entry['cor'], entry['rel'])
            sys.stdout.flush()


# Create both screens. Please note the root.manager.current: this is how
# you can control the ScreenManager from kv. Each screen has by default a
# property manager that gives you the instance of the ScreenManager used.
Builder.load_string("""

<PatientScreen>:
    recording: recordingID
    patient: patientID
    BoxLayout:
        orientation:  'vertical'
            
        BoxLayout:
            orientation:  'horizontal'
            size_hint: 1, .15
            Widget:

            Button:
                text: 'Settings'
                size_hint: .15, 1
                on_press: root.manager.current = 'recording'
                
        Widget:
            size_hint: 1, .05
            
        
        BoxLayout:
            orientation:  'horizontal'
            size_hint: 1, .15
            Label:
                text: 'Patient:'
                size_hint: .15, 1
            DropBut:
                id: patientID
                size_hint: .45, 1
                
            BoxLayout:
                orientation:  'horizontal'
                size_hint: 0.4, 1
                Button:
                    text: 'Create'
                    on_press: root.create_patient()
                Button:
                    text: 'Edit'
                    on_press: root.edit_current_patient()
                    #on_press: root.manager.current = 'recording'
                Button:
                    text: 'Delete' 
                    on_press: root.delete_current_patient()
                
        Widget:
            size_hint: 1, .05
            
        
        BoxLayout:
            orientation:  'horizontal'
            size_hint: 1, .30
            Label:
                text: 'Recording:'
                size_hint: .15, 1
                
            BoxLayout:
                orientation:  'vertical'
                size_hint: .45, 1
                Widget:
                    size_hint: 1, 0.25
                DropBut:
                    id: recordingID
                    size_hint: 1, 0.5
                Widget:
                    size_hint: 1, 0.25
                
            BoxLayout:
                orientation:  'vertical'
                size_hint: 0.4, 1
                
                BoxLayout:
                    orientation:  'horizontal'
                    Button:
                        text: 'Record'
                        # on_press: root.manager.current = 'recording'
                        on_press: root.create_recording()
                    Button:
                        text: 'View'
                        on_press: root.manager.current = 'recording' 
                    Button:
                        text: 'Delete'
                        on_press: root.delete_current_recording()
                
                BoxLayout:
                    orientation:  'horizontal'
                    Button:
                        text: 'Import'
                        #on_press: root.create_recording(live=False)
                        on_press: 
                            root.manager.current = 'recording'
                            root.recording_import()
                    Button:
                        text: 'Import Live'
                        #on_press: root.create_recording(live=True)
                        on_press: 
                            root.manager.current = 'recording'
                            root.recording_import()
                    Button:
                        text: 'Annotate'
                        on_press: root.edit_current_recording()
                
        Widget:    # Hack to force vertical justify

<RecordingScreen>:
    raw_data: raw_data
          
    BoxLayout:
        orientation:  'vertical'
        Label:
            size_hint: 1, 0.1
            text: 'Recording Screen'
        BoxLayout:
            id: raw_data
            orientation: 'vertical'
            padding: 20
        GridLayout:
            size_hint: 1, 0.1
            cols: 2
            Button:
                text: 'Cancel'
            Button:
                text: 'Done'
                on_press: root.manager.current = 'patient'
            
            
<PatientPopup>:
    first_name: first_nameID
    last_name: last_nameID
    age: ageID
    uuid: uuid_ID

    title: 'Enter Patient Data'
    GridLayout:
        cols: 2
        rows: 5
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
            
# Placeholder
<RecordingPopup>:
    date: dateID
    duration: durationID
    uuid: uuid_ID

    title: 'Enter Recording Data'
    GridLayout:
        cols: 2
        rows: 4
        padding: 10
        spacing: 10
        
        Label:
            text:  'Date'
        TextInput:
            id: dateID
            
        Label:
            text:  'Duration'
        TextInput:
            id: durationID
            
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
        
# Placeholder
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

# Alternative Syntax: Builder.load_file(join(dirname(__file__), 'confirmpopup.kv'))


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
    uuid = ObjectProperty()

    def __init__(self, callback, data={}, *args, **kwargs):
        super(PatientPopup, self).__init__(*args, **kwargs)
        self.callback = callback

        pprint(data)

        self.first_name.text = data['first_name'] if 'first_name' in data else ''
        self.last_name.text = data['last_name'] if 'last_name' in data else ''
        self.age.text = data['age'] if 'age' in data else ''
        self.uuid.text = data['uuid'] if 'uuid' in data else str(uuid.uuid4())

    def finish(self, reason):
        print 'reason:', reason
        if reason == 'cancel':
            result = None
        else:
            # Correctness tests
            if self.first_name.text == '' or self.last_name.text == '':
                return
            if not self.age.text.isdigit():
                self.age.text = '**invalid**'
                return

            result = {'first_name': self.first_name.text,
                      'last_name': self.last_name.text,
                      'age': self.age.text,
                      'uuid': self.uuid.text}

        self.dismiss()
        self.callback(result)


# Placeholderr
class ConfirmRecordingDeletePopup(Popup):
    def __init__(self, callback, entry={}, *args, **kwargs):
        super(ConfirmRecordingDeletePopup, self).__init__(*args, **kwargs)
        self.callback = callback
        self.date.text = entry['date']
        self.duration.text = entry['duration']
        self.uuid.text = entry['uuid']

    def process_ok(self):
        self.dismiss()
        self.callback()


# Placeholder
class RecordingPopup(Popup):
    date = ObjectProperty()
    duration = ObjectProperty()
    uuid = ObjectProperty()

    def __init__(self, callback, data={}, *args, **kwargs):
        super(RecordingPopup, self).__init__(*args, **kwargs)
        self.callback = callback

        pprint(data)

        self.date.text = data['date'] if 'date' in data else ''
        self.duration.text = data['duration'] if 'duration' in data else ''
        self.uuid.text = data['uuid'] if 'uuid' in data else str(uuid.uuid4())

    def finish(self, reason):
        print 'reason:', reason
        if reason == 'cancel':
            result = None
        else:
            # Correctness tests
            if self.date.text == '' or self.duration.text == '':
                return
            # if not self.age.text.isdigit():
            #     self.age.text = '**invalid**'
            #     return

            result = {'date': self.date.text,
                      'duration': self.duration.text,
                      'uuid': self.uuid.text}

        self.dismiss()
        self.callback(result)


class DropBut(Button):
    def __init__(self, **kwargs):
        super(DropBut, self).__init__(**kwargs)
        self.drop_list = None
        self.drop_list = DropDown()
        self.update_dropdown([])
        self.callback = None

        self.bind(on_release=self.drop_list.open)
        #self.drop_list.bind(on_select=lambda instance, x: setattr(self, 'text', x))
        self.drop_list.bind(on_select=self.do_select)


    def do_select(self, instance, x):
        setattr(self, 'text', x)
        if self.callback is not None:
            self.callback(x)


    def update_dropdown(self, entries):
        self.drop_list.clear_widgets()
        for i in entries:
            btn = Button(text=i, size_hint_y=None, height=50, valign="middle", padding_x= 5, halign='left')
            #btn.text_size = btn.size
            btn.bind(on_release=lambda btn: self.drop_list.select(btn.text))

            self.drop_list.add_widget(btn)

    def register_callback(self, callback):
        self.callback = callback


# Declare both screens
class PatientScreen(Screen):
    patient = ObjectProperty()
    recording = ObjectProperty()

    def __init__(self, parent, *args, **kwargs):
        super(PatientScreen, self).__init__(*args, **kwargs)
        self.sm = parent
        self.patient_mgr = PatientPersistenceManager(self.patient, on_update=self.patient_selection_changed)
        self.recording_mgr = RecordingsPersistenceManager(self.recording, on_update=self.recording_selection_changed)
        self.patient_mgr.load_data()


    #
    # Patient edit functions -- create, edit and delete
    #

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
                             size_hint=(None, None), size=(600, 400))
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
        self.patient_mgr.delete_selection()


    #
    # Recording Functions
    #
    def create_recording(self, live=False):
        """Create new recording entry"""
        self.edit_recording({})

    def edit_current_recording(self):
        """Update existing recording entry"""
        current_recording = self.recording_mgr.get_selection()
        if current_recording is not None:
            self.edit_recording(current_recording)
        return

    def edit_recording(self, entry):
        """Common recording data popup routine for both create and edit operations """
        popup = RecordingPopup(self.recordingPopupClosed, data=entry,
                             size_hint=(None, None), size=(600, 400))
        popup.open()

    def recordingPopupClosed(self, entry):
        """callback routine for recording data entry"""
        print 'recordingPopupClosed received:', entry
        self.recording_mgr.update_selection(entry)

    def delete_current_recording(self):
        """Removes entry associated with current patient"""
        selection = self.recording_mgr.get_selection()
        if selection is not None:
            # Confirm with user prior to deletion
            ConfirmRecordingDeletePopup(self.perform_recording_delete,
                                        entry=selection).open()

    def perform_recording_delete(self):
        """perform actual recording data deletion after upon user confirmation"""
        self.recording_mgr.delete_selection()


    def patient_selection_changed(self, patient_uuid):
        print '*'*40
        print 'patient_selection_changed:', patient_uuid
        print '*'*40
        self.recording_mgr.change_folder(patient_uuid)


    def recording_selection_changed(self, recording_uuid):
        print '*'*40
        print 'recording_selection_changed:', recording_uuid
        print '*'*40

    def recording_import(self):
        print 'import pressed'
        if sys.platform == 'win':
            user_base = dirname(expanduser('~'))
            user_path = dirname(expanduser('~')) + sep + 'Documents'
        else:
            user_base = expanduser('~')
            user_path = expanduser('~') + sep + 'Documents'
        browser = FileBrowser(filters=['*.mp3', '*.wav'], multiselect=False,
                              rootpath=user_base,   path=os.getcwd(),
                              select_string='Select',
                              favorites=[(user_path, 'Documents')])
        browser.bind(
                    on_success=self.import_process_selected,
                    on_canceled=self.import_canceled)
        self.browser_popup = Popup(title='Select file for import', content=browser,
                      #auto_dismiss=False
                      )
        self.browser_popup.open()

    def import_process_selected(self, instance):
        selection = instance.selection
        self.browser_popup.dismiss()
        if len(selection) == 1:
            print 'import_process_selected', selection[0]
            self.sm.recordings_screen.perform_import(selection[0])


    def recording_finished(self, results):
        self.bp_thread = None
        print 'recording_finished'
        pprint(results)

    def import_canceled(self, instance):
        print 'import_canceled'
        self.browser_popup.dismiss()


class RecordingScreen(Screen):
    raw_data = ObjectProperty()

    def __init__(self, parent, *args, **kwargs):
        super(RecordingScreen, self).__init__(*args, **kwargs)
        self.sm = parent
        # Declare instance variables and set initial condition
        self.allGraphs = {}
        self.createRawDataPlots()


    #
    # Raw Data Plot
    #
    def createRawDataPlots(self):
        lab = Label(text='FHR Signal', size_hint=(1, 0.1))
        self.raw_data.add_widget(lab)

        # graph = VitalsScatterGraph(graphspec={'ylabel':'bpm', 'xlabel': 'Time (in min)',
        #                                       'y_grid_label':True, 'x_grid_label':True,
        #                                       'x_ticks_minor': 1, 'x_ticks_major':  10,
        #                                       'y_ticks_major': 10, 'y_ticks_minor': 2,
        # })


        graph = VitalsPanZoomGraph(#color='white',default_duration=3, min_duration=100,
                                   #line_width=10,
                                   graphspec={'ymin':50,'ymax':200,
                                              'ylabel': 'bpm', 'y_grid_label': True,
                                              'y_ticks_major': 10, 'y_ticks_minor': 2,
                                              'xlabel': 'Time (in min)', 'x_grid_label':True,
                                              'x_ticks_minor': 1, 'x_ticks_major':  10})




        graph.size_hint = (1, 0.5)
        self.allGraphs['raw_fhr'] = graph
        self.raw_data.add_widget(graph)

        data = [(i/10.0, 150+50*float(math.sin(i/10.0))) for i in range(600)]
        self.allGraphs['raw_fhr'].updatePlot(data, 60)


    def XcreateRawDataPlots(self):
        lab = Label(text='FHR Signal', size_hint=(1, 0.1))
        self.raw_data.add_widget(lab)

        # graph = VitalsScatterGraph(upperLimit=THRESH_FETAL_TACHYCARDIA,
        #                            lowerLimit=THRESH_FETAL_BRADYCARDIA,
        #                            graphspec={'ylabel':'bpm', 'xlabel': 'Time (in min)',
        #                                       'y_grid_label':True, 'x_grid_label':True,
        #                                       'x_ticks_minor': 1, 'x_ticks_major':  10,
        #                                       'y_ticks_major': 10, 'y_ticks_minor': 2,
        # })

        graph = VitalsPanZoomGraph(color='white',default_duration=3, min_duration=10,
                                   line_width=10,
                                   ymin=50, ymax=200,
                                   graphspec={'ymin':50,'ymax':200,
                                              'ylabel': 'bpm', 'y_grid_label': True,
                                              'y_ticks_major': 10, 'y_ticks_minor': 2,
                                              'xlabel': 'Time (in min)', 'x_grid_label':True,
                                              'x_ticks_minor': 1, 'x_ticks_major':  10})
        graph.size_hint = (1, 0.5)
        self.allGraphs['raw_fhr'] = graph
        self.raw_data.add_widget(graph)

        data = [(i, 150+50*float(math.sin(i))) for i in range(60)]
        self.allGraphs['raw_fhr'].updatePlot(data, 60)




        # lab = Label(text='UC Signal', size_hint=(1, 0.1))
        # self.raw_data.add_widget(lab)
        #
        # graph = VitalsPanZoomGraph(graphspec={'ymin':0,'ymax':100,
        #                                       'ylabel': 'uc', 'y_grid_label': True,
        #                                       #'y_ticks_major': 100, 'y_ticks_minor': 1,
        #                                       'xlabel': 'Time (in min)', 'x_grid_label':True,
        #                                       'x_ticks_minor': 1, 'x_ticks_major':  10})
        # graph.size_hint = (1, 0.3)
        # self.allGraphs['raw_uc'] = graph
        # self.raw_data.add_widget(graph)
        #
        # nav = VitalsGraphNavigation(callback=self.raw_data_nav_callback, size_hint=(1, 0.1))
        # self.raw_data.add_widget(nav)


    def updateRawDataPlots(self):
        data = [(x, y) for x, y in self.raw_fhr if x <= self.tCurrent]
        self.allGraphs['raw_fhr'].updatePlot(data, self.tCurrent)

        data = [(x, y) for x, y in self.raw_uc if x <= self.tCurrent]
        self.allGraphs['raw_uc'].updatePlot(data, self.tCurrent)


    def raw_data_nav_callback(self, val):
        print 'raw_data_nav_callback:', val
        self.allGraphs['raw_fhr'].do_nav(val)
        self.allGraphs['raw_uc'].do_nav(val)
    pass


    def perform_import(self, fname):
        self.update_freq = 1000
        self.last_pos = -1000
        self.bp_thread = backround_processing(fname,
                                              update_callback=self.recording_update,
                                              completion_callback=self.recording_finished,
                                              useTriangleWeights=False)

    def recording_update(self, results):
        entry = results[-1]

        #data = [(x['pos'], x['hr']) for x in results ]
        data = [(i, float(x['hr'])) for i, x in enumerate(results)]
        self.allGraphs['raw_fhr'].updatePlot(data, max(len(results), 60))



        if entry['pos'] >= self.last_pos + self.update_freq:
            self.last_pos = entry['pos']
            print '{:0.0f} bpm @ {:0.0f} sec -- cor: {:0.2f}  rel: {:0.2f}'.format(
                entry['hr'], entry['pos']/1000.0, entry['cor'], entry['rel'])
            sys.stdout.flush()

    def recording_finished(self, results):
        self.bp_thread = None
        print 'recording_finished'
        pprint(results)


class TestApp(App):

    def build(self):
        self.title = 'CTG Recorder'
        # Create the screen manager
        self.screen_manager = ScreenManager()
        self.patient_screen = PatientScreen(self, name='patient')
        self.screen_manager.add_widget(self.patient_screen)

        self.recordings_screen = RecordingScreen(self, name='recording')
        self.screen_manager.add_widget(self.recordings_screen)
        return self.screen_manager

    # def on_start(self):
    #     self.patient_screen.load_data()



if __name__ == '__main__':
    if kivy.utils.platform == 'android':
        RECORDINGS_DIR = '/sdcard/ctg_recordings/'
    elif getattr(sys, 'frozen', False):
    # running in a bundle
        print 'running frozen'
        bundle_dir = sys._MEIPASS
        print 'bundle_dir', bundle_dir
        RECORDINGS_DIR = bundle_dir
    else:
    # running live
        print 'running live'
        RECORDINGS_DIR = os.getcwd()

    TestApp().run()