# coding: utf-8

#
#  Copyright Douglas Williams, 2018
#  All Rights Reserved
#


from kivy.config import Config
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')
import kivy
#kivy.require('1.0.5')

from  kivy.uix.scatter import Scatter
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.app import App
from AppWithParams import AppWithParams
from kivy.properties import ObjectProperty, StringProperty
from kivy.uix.textinput import TextInput
from kivy.uix.tabbedpanel import TabbedPanel
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.checkbox import CheckBox
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.widget import Widget
from kivy.clock import Clock
import kivy.utils
from kivy.lang import Builder
from kivy.utils import get_color_from_hex as hex

from confirmRecording import ConfirmRecordingPopup
from kivy_garden_graph import Graph
from simple_graph import SimpleLineGraph, COLORS

import traceback
from pprint import pprint
import sys
import pickle as pickle
import copy
import math
import numpy as np
import time
import os
import platform
import gc


from libAudioDetect import audio_detect, select_preferred_io
from libAudio import audio_recorder
from libUltrasound import combineExtractionResults
from paramsUltrasound import EXTRACTOR_ARGS

from libTocopatchSignal import ProcessUC, isolateUC, UC_DEFAULT_PARAMS
from libTocopatchDevice import HeartyPatch_Listener


from libUC import findUC

#from libDecel import extractAllDecels, summarizeDecels
from wrapLibDecel import extractAllDecels, summarizeDecels



from libSignalProcessing import tolist                   # New
from paramsDecel import FEATURE_EXTRACT_PARAMS

import rules_constants
from rules_integration import Decision

prefix = os.path.join(os.path.join('/', *os.getcwd().split('/')[:-1]), 'recordings')


# ARTIFACT_RENDERING = {
#     'valid': {'row': 2, 'color':'fuchia'},
#     'borderline': {'row': 1, 'color':'gray'},
# }

ARTIFACT_MAX_ROWS = 3
ARTIFACT_RENDERING = {
    'prolonged':               {'row': 3, 'color': COLORS['magenta']},
    'variable':                {'row': 2, 'color': COLORS['yellow']},  # hex('#ffff00')
    'variable_periodic':       {'row': 3, 'color': hex('#FFA500')},
    'late_decel':              {'row': 3, 'color': COLORS['red']},    # hex('#ff0000')
    #'mild_late_decel':         {'row': 3, 'color': hex('#ffc0c0')},
    'early_decel':             {'row': 1, 'color': COLORS['gray']},
    #'shallow_early_decel':     {'row': 2, 'color': hex('#c0ffc0')},
    'acceleration':            {'row': 1, 'color': COLORS['green']},
    #'borderline_acceleration': {'row': 1, 'color': COLORS['green']},
}


UC_RENDERING = {'onset':{'color':'lime', 'lw': 2},
                'acme':{'color':'white',  'lw': 2},
                'release':{'color':'red', 'lw': 2},
                }

UC_TIMING_RENDERING = {
    'uc': {'color': 'white', 'lw': 1.5},
    'decel': {'color': 'red', 'lw': 1.5},
}

ASSESSMENT_DISPLAY_MAX_ROWS = 5
ASSESSMENT_DISPLAY = {
    rules_constants.ASSESSMENT_URGENT: {'text': 'Urgent', 'color': COLORS['magenta'], 'row': 4},
    rules_constants.ASSESSMENT_PATHOLOGICAL: {'text': 'Pathological', 'color': COLORS['red'], 'row': 3},
    rules_constants.ASSESSMENT_SUSPICIOUS: {'text': 'Suspicious', 'color': COLORS['yellow'], 'row': 2},
    rules_constants.ASSESSMENT_NORMAL: {'text': 'Normal', 'color': COLORS['lime'], 'row': 1},
    rules_constants.ASSESSMENT_ABSENT: {'text': 'Absent', 'color': COLORS['white'], 'row': None},
    rules_constants.ASSESSMENT_PRESENT: {'text': 'Present', 'color': COLORS['white'], 'row': None},
    rules_constants.ASSESSMENT_UNKNOWN: {'text': 'Unknown', 'color': COLORS['white'], 'row': None},
    rules_constants.ASSESSMENT_CONTINUE: {'text': 'Continue Testing', 'color': COLORS['white'], 'row': 0.1},
}

ENTITY_TO_VIEW = {
    'assessment': 'dashboard',
    'baseline_hr': 'analysis',
    'variability': 'analysis',
    'decelerations': 'combined',
    'accelerations': 'combined',
    'contractions': 'combined'
}

kv_string = """
#:kivy 1.0

#:import Graph kivy_garden_graph.Graph
#:import os os

<SizedClickableLabel>:
    height: 10
    text_size: self.size


<RLabel>
    rotation: 90
    do_rotation: False
    #size: text_label.size
    size: text_label.size[1], text_label.size[0]
    
    Label:
        id: text_label
        text: root.text
        halign: 'left'  # 'center'
        valign: 'middle'
        size: self.texture_size

    
<Dashboard>:
    orientation: 'vertical'
    
    assessment: assessment
    baseline_hr: baseline_hr
    variability: variability
    decelerations: decelerations
    accelerations: accelerations
    contractions: contractions
    recommendations_area: recommendations_area
    
    Label:
        id: assessment
        text:  'Fetal Assessment: Unknown'
        font_size: '32sp'
        valign: 'top'
        size_hint: 1, 0.2
        
    GridLayout:
        size_hint: 1, 0.8
        cols: 2
        
        # Stats
        BoxLayout:
            orientation: 'vertical'
            
            Label:
                text:  'Summary'
                text_size: self.size
                font_size: '24sp'
                valign: 'top'
                size_hint: 1, 0.2
                
            
            BoxLayout:
                orientation: 'vertical'
                size_hint: 1, 0.8
            
                ClickableLabel:
                    id: baseline_hr
                    text:  'Baseline HR: Unknown'
                    text_size: self.size
                    font_size: '18sp'
                    valign: 'top'
                    on_press: root.touched('baseline_hr')
                
                ClickableLabel:
                    id: variability
                    text:  'Variability: Unknown'
                    text_size: self.size
                    font_size: '18sp'
                    valign: 'top'
                    on_press: root.touched('variability')
            
                ClickableLabel:
                    id: decelerations
                    text:  'Decelerations: Unknown'
                    text_size: self.size
                    font_size: '18sp'
                    valign: 'top'
                    on_press: root.touched('decelerations')
                
                ClickableLabel:
                    id: accelerations
                    text:  'Accelerations: Unknown'
                    text_size: self.size
                    font_size: '18sp'
                    valign: 'top'
                    on_press: root.touched('accelerations')
                
                ClickableLabel:
                    id: contractions
                    text:  'Contractions: Unknown'
                    text_size: self.size
                    font_size: '18sp'
                    valign: 'top'
                    on_press: root.touched('contractions')

        # Recommendations
        BoxLayout:
            orientation: 'vertical'
            
            Label:
                text:  'Recommendations'
                text_size: self.size
                font_size: '24sp'
                valign: 'top'
                size_hint: 1, 0.2
            
            ScrollableLabel:
            #BoxLayout:
                id: recommendations_area
                #orientation: 'vertical'
                size_hint: 1, 0.8
       
# source:  https://github.com/kivy/kivy/wiki/Scrollable-Label      
<ScrollableLabel>:
    bar_width: 20
    do_scroll_x: False
    do_scroll_y: True
    bar_color: 1,1,1,1
    bar_inactive_color: 1,1,1,1
    scroll_type: ['content', 'bars']
    
    Label:
        size_hint_y: None
        height: self.texture_size[1]
        text_size: self.width, None
        text: root.text
       
        
<PlotPopup>:
    cancel_button: cancel_button
    restart_button: restart_button
    
    dashboard_button: dashboard_button
    analysis_button: analysis_button
    combined_button: combined_button
    fhr_detail_button: fhr_detail_button
    uc_detail_button: uc_detail_button
    decel_button: decel_button
    
    
    recent_button: recent_button
    full_button: full_button
    pan_zoom_button: pan_zoom_button
    
    uc_onset_button:   uc_onset_button
    uc_acme_button:    uc_acme_button
    uc_release_button: uc_release_button
    uc_ignore_button:  uc_ignore_button
    
    plot_area: plot_area
    pan_zoom_area: pan_zoom_area
    assessment_text: assessment_text
    
    BoxLayout:
        orientation: 'horizontal'    
    
        BoxLayout:
            orientation: 'vertical'
            size_hint: 0.8, 1       

            #
            # View Selection
            #

            GridLayout:
                size_hint: 1, 0.0725 
                rows: 1
                
                ToggleButton:
                    id: dashboard_button
                    text: 'Dashboard' 
                    group: 'view_button_group'  
                    on_press: root.select_plot_view('dashboard')
                
                ToggleButton:
                    id: combined_button
                    text: 'FHR/UC'
                    group: 'view_button_group'
                    state: 'down'  
                    on_press: root.select_plot_view('combined')    
                
                ToggleButton:
                    id: analysis_button
                    text: 'Analysis' 
                    group: 'view_button_group'  
                    on_press: root.select_plot_view('analysis')
                
                ToggleButton:
                    id: decel_button
                    text: 'Decel' 
                    group: 'view_button_group'  
                    on_press: root.select_plot_view('decel')  
                
                ToggleButton:
                    id: fhr_detail_button
                    text: 'FHR Detail'
                    group: 'view_button_group'  
                    on_press: root.select_plot_view('fhr_detail') 
                
                ToggleButton:
                    id: uc_detail_button
                    text: 'UC Detail'
                    group: 'view_button_group'  
                    on_press: root.select_plot_view('uc_detail') 

            ClickableLabel:
                id: assessment_text
                text: ''
                font_size: '18sp'
                size_hint: 1, 0.01 
                opacity: 0
                on_press: root.touched_entity('assessment')

            #
            # Area for Plots
            #

            BoxLayout:
                id: plot_area
                orientation: 'vertical'
                size_hint: 1, 0.925
                padding: 20
                
                Label:
                    text: 'Envelope' 
                    bold: True
                    text_size: self.size
                    size_hint: 1, 0.1
                
                BoxLayout:
                    orientation: 'horizontal'
                    
                    Label:
                        text: 'FHR' 
                        size_hint: 0.1, 1
                        
                    Graph: 
                        size_hint: 0.9, 1
                
                BoxLayout:
                    orientation: 'horizontal'
                    size_hint: 1, 0.3
                    
                    Label:
                        text: 'Valid' 
                        size_hint: 0.1, 1
                        
                    Graph: 
                        size_hint: 0.9, 1
                
                BoxLayout:
                    orientation: 'horizontal'
                    size_hint: 1, 0.3
                    
                    Label:
                        text: 'Corr' 
                        size_hint: 0.1, 1
                        
                    Graph: 
                        size_hint: 0.9, 1
                
                Label:
                    text: 'Pitch' 
                    bold: True
                    text_size: self.size
                    size_hint: 1, 0.1
                
                BoxLayout:
                    orientation: 'horizontal'
                    
                    Label:
                        text: 'FHR' 
                        size_hint: 0.1, 1
                        
                    Graph: 
                        size_hint: 0.9, 1
                
                BoxLayout:
                    orientation: 'horizontal'
                    size_hint: 1, 0.3
                    
                    Label:
                        text: 'Valid' 
                        size_hint: 0.1, 1
                        
                    Graph: 
                        size_hint: 0.9, 1
                
                BoxLayout:
                    orientation: 'horizontal'
                    size_hint: 1, 0.3
                    
                    Label:
                        text: 'Corr' 
                        size_hint: 0.1, 1
                        
                    Graph: 
                        size_hint: 0.9, 1 

            #
            # Area for Pan/Zoom Controls
            #

            BoxLayout:
                id: pan_zoom_area
                orientation: 'horizontal'
                size_hint: 1, 0.125
                padding: 20

                Button:
                    id: pan_left_button
                    text: 'Left'
                    on_press: root.do_pan_zoom('left')  
                               
                Widget: 
                    size_hint: 0.025, 1

                Button:
                    text: 'Right'
                    on_press: root.do_pan_zoom('right')  
                               
                Widget:  
                    size_hint: 0.5, 1

                Button:
                    text: 'Zoom In'
                    on_press: root.do_pan_zoom('zoom_in')  
                               
                Widget: 
                    size_hint: 0.025, 1

                Button:
                    text: 'Zoom Out'
                    on_press: root.do_pan_zoom('zoom_out')  

        # Spacing between main area and controls            
        Widget: 
            size_hint: 0.025, 1 
           
           
        #
        # Right Sidebar Controls
        #
           
        GridLayout:
            # Side area for buttons
            #orientation: 'vertical'  
            size_hint: 0.1, 1   
            cols: 1
            
            #
            # Session Status
            #
                
            Button:
                text: 'Done'
                on_press: root.do_completion('done') 
                
            Widget:
                size_hint: 1, 0.1
                
            Button:
                id: cancel_button
                text: 'Cancel'
                on_press: root.do_completion('cancel')
                
            Widget:
                size_hint: 1, 0.1
            
            Button:
                id: restart_button
                text: 'Restart'
                disabled: True
                opacity: 0
                on_press: root.do_completion('restart') 
                
            Widget:
                size_hint: 1, 0.5
                
            #
            # Plot Scaling Controls
            #
             
            ToggleButton:
                id: recent_button
                text: 'Recent'
                on_press: root.select_plot_duration('recent')
                group: 'zoom_button_group'
                state: 'down'  
                
            Widget:
                size_hint: 1, 0.1
            
            ToggleButton:
                id: full_button
                text: 'Full'
                on_press: root.select_plot_duration('full')
                group: 'zoom_button_group'  
                
            Widget:
                size_hint: 1, 0.1
            
            ToggleButton:
                id: pan_zoom_button
                text: 'Pan/Zoom'
                on_press: root.select_plot_duration('pan_zoom')
                group: 'zoom_button_group'

                
            Widget:
                size_hint: 1, 0.5
            
            #
            # UC Manual Annotation Buttons
            #

            Button:
                id: uc_onset_button
                text: 'Onset'
                on_press: root.uc_annotate_button_pressed('onset')
                
            Widget:
                size_hint: 1, 0.1
    
            Button:
                id: uc_acme_button
                text: 'Acme'
                on_press: root.uc_annotate_button_pressed('acme')
                
            Widget:
                size_hint: 1, 0.1

            Button:
                id: uc_release_button
                text: 'Release'
                on_press: root.uc_annotate_button_pressed('release')
                
            Widget:
                size_hint: 1, 0.1

            Button:
                id: uc_ignore_button
                text: 'Ignore'
                on_press: root.uc_annotate_button_pressed('ignore')  

"""

Builder.load_string(kv_string)


class ClickableLabel(ButtonBehavior, Label):
    callback = ObjectProperty(None)
    tag = ObjectProperty(None)

    def on_press(self):
        if self.callback is not None:
            self.callback(self.tag)


class SizedClickableLabel(ClickableLabel):
    pass




class RLabel(Scatter):
    text = ObjectProperty()

    def __init__(self, text='', **kwargs):
        super(RLabel, self).__init__(**kwargs)
        self.text = text


class ScrollableLabel(ScrollView):
    text = StringProperty('')


class Dashboard(BoxLayout):
    assessment = ObjectProperty()
    baseline_hr = ObjectProperty()
    variability = ObjectProperty()
    decelerations = ObjectProperty()
    accelerations = ObjectProperty()
    contractions = ObjectProperty()
    recommendations_area = ObjectProperty()

    def __init__(self, callback=None, **kwargs):
        self.callback = callback
        super(Dashboard, self).__init__(**kwargs)

    def touched(self, val):
        if self.callback is not None:
            self.callback(val)




class PlotPopup(Popup):
    cancel_button = ObjectProperty()
    restart_button = ObjectProperty()

    dashboard_button = ObjectProperty()
    analysis_button = ObjectProperty()
    combined_button = ObjectProperty()
    fhr_detail_button = ObjectProperty()
    uc_detail_button = ObjectProperty()
    decel_button =  ObjectProperty()

    recent_button = ObjectProperty()
    full_button = ObjectProperty()
    pan_zoom_button = ObjectProperty()

    uc_onset_button = ObjectProperty()
    uc_acme_button = ObjectProperty()
    uc_release_button = ObjectProperty()
    uc_ignore_button = ObjectProperty()

    plot_area = ObjectProperty()
    pan_zoom_area = ObjectProperty()
    assessment_text = ObjectProperty()

    common_graphspec = {
        'font_size': '9sp', 'xlabel': 'Time (in min)', 'color': COLORS['yellow'], 'line_width': 2,
        'x_grid_label': True, 'x_ticks_minor': 3, 'x_ticks_major': 0.5, 'x_grid': True,
        'y_grid_label': True, 'y_grid': True,
        'dynamic_xmin': False, 'dynamic_xmax': False,
        'dynamic_ymax': False, 'dynamic_ymin': False, }

    graphspec_no_x = {
        'font_size': '9sp', 'color': COLORS['yellow'], 'line_width': 2,
        'x_grid_label': False, 'x_ticks_minor': 3, 'x_ticks_major': 0.5, 'x_grid': True,
        'y_grid_label': True, 'y_grid': True,
        'dynamic_xmin': False, 'dynamic_xmax': False,
        'dynamic_ymax': False, 'dynamic_ymin': False, }

    graphspec_no_y = {
        'font_size': '9sp', 'xlabel': 'Time (in min)', 'color': COLORS['yellow'], 'line_width': 2,
        'x_grid_label': True, 'x_ticks_minor': 3, 'x_ticks_major': 0.5, 'x_grid': True,
        'y_grid_label': False, 'y_grid': False,
        'dynamic_xmin': False, 'dynamic_xmax': False,
        'dynamic_ymax': False, 'dynamic_ymin': False, }

    graphspec_no_y_no_x = {
        'font_size': '9sp', 'color': COLORS['yellow'], 'line_width': 2,
        'x_grid_label': False, 'x_ticks_minor': 3, 'x_ticks_major': 0.5, 'x_grid': True,
        'y_grid_label': False, 'y_grid': False,
        'dynamic_xmin': False, 'dynamic_xmax': False,
        'dynamic_ymax': False, 'dynamic_ymin': False, }


    def __init__(self, mode, restart_callback=None, completion_callback=None,
                 metadata_file=None, audio_file=None, toco_file=None, title='Recording'):
        super(PlotPopup, self).__init__()

        self.mode =  mode
        self.title = title

        # recording files
        self.metadata_file = metadata_file
        self.audio_file = audio_file
        self.toco_file = toco_file

        # callbacks
        self.restart_callback = restart_callback
        self.completion_callback = completion_callback

        # other params  (from settings)
        self.readonly = AppWithParams.getParam('readonly')
        self.host = AppWithParams.params['ip_address']
        self.useTocopatch = AppWithParams.params['tocopatch_enable']
        self.ucEnableAnnotate = AppWithParams.params['tocopatch_annotate'] or not AppWithParams.params['tocopatch_enable']

        # Recording related variables
        self.completion_status = None

        self.audio_thread = None
        self.audio_start_time = None
        self.audio_config = []

        # Toco Recorder related variables
        self.toco_start_time = None
        self.toco_skew = None
        self.toco_listener = None
        self.processUC = ProcessUC(fs=128, **UC_DEFAULT_PARAMS)

        # Manual UC Annotation state
        self.rawAnnotations = []   # manual UC Annotations clicks

        # Plotting related
        self.allGraphs = {}
        self.last_plot_state    = {'view': None, 'scale': None, 'scale_limits': None,
                                   'hr_updated': False, 'uc_updated': False, 'assessment_updated': False}
        self.current_plot_state = {'view': 'combined', 'scale': 'recent', 'scale_limits': None,
                                   'hr_updated': False, 'uc_updated': False, 'assessment_updated': False}
        self.plot_update_interval = 1.0
        self.plot_duration_recent = 5

        # Rules Engine and simulation related
        self.simulation_time = 0
        self.simulation_start_time = 0
        self.decision = None
        self.decision_outcome = None
        self.assessment_history = []
        self.showAssessmentField(False)
        self.enable_realtime_pattern = AppWithParams.getParam('enable_realtime_pattern')

        if platform.system() == 'Windows':
            self.common_graphspec['line_width'] = 1.01
            self.graphspec_no_x['line_width'] = 1.01
            self.graphspec_no_y['line_width'] = 1.01
            self.graphspec_no_y_no_x['line_width'] = 1.01

        # Recording data
        self.data = {
            'version':2,
            'fhr_source': None,
            'uc_source': None,

            # FHR  Signal Data
            'combined': {},    # includes: 'hr', 'valid', 'pos'
            'envelope': {},    # includes: 'hr', 'valid', 'pos', 'raw', 'cor'
            'pitch': {},       # includes: 'hr', 'valid', 'pos', 'raw', 'cor'

            # UC Signal Data
            'uc': {},    # includes:   'raw', 'filtered', 'uc', 'alt_uc', 'posSec'

            # Manual annotation of UC
            'uc_ann': [],   # includes

            # Results from FHR Analysis
            'annotations': {}}  # includes 'decels', 'baseline',  'variability' ## was 'deltaLocal', 'deltaProlonged',
        if not self.ucEnableAnnotate:
            self.data['uc_ann'] = None

        if mode in ['record']:
            if not self.enable_realtime_pattern:
                print 'enable_realtime_pattern:', self.enable_realtime_pattern
                self.dashboard_button.disabled = True
                self.analysis_button.disabled = True
                self.decel_button.disabled = True
                self.dashboard_button.opacity = 0
                self.analysis_button.opacity = 0
                self.decel_button.opacity = 0

            self.restart_button.disabled = False
            self.restart_button.opacity = 1
            self.update_button_states()
            self.show_uc_annotation_controls(makeVisible=self.ucEnableAnnotate)
            self.perform_recording()

        elif mode in ['view', 'simulate', 'simulate_ia']:
            self.load_data()
            self.current_plot_state = {'view': 'combined', 'scale': 'full', 'scale_limits': None,
                                       'hr_updated': 'combined' in self.data,
                                       'uc_updated': 'uc' in self.data or self.data['uc_ann'] is not None,
                                       }
            self.cancel_button.disabled = True
            self.cancel_button.opacity = 0
            self.show_uc_annotation_controls(makeVisible=False)
            if self.data['fhr_source'] is None:
                self.dashboard_button.disabled = True
                self.fhr_detail_button.disabled = True
                self.analysis_button.disabled = True
                self.decel_button.disabled = True
                self.current_plot_state ['view']= 'uc_detail'
            if self.data['uc_source'] is None:
                self.uc_detail_button.disabled = True
            self.update_button_states()

            if mode == 'view':
                self.dashboard_button.disabled = True
                if self.data['fhr_source'] is not None:
                    self.data['annotations'] = self.detectPatternsHR()
                Clock.schedule_once(lambda x: self.update_plot_display(), 0)
            elif mode in ['simulate', 'simulate_ia']:
                self.current_plot_state['view'] = 'dashboard'
                self.update_button_states()
                self.showAssessmentField(True)
                self.assessment_history = []
                self.repurpose_uc_annotation_controls(mode)
                self.initialize_clone_data()
                self.update_simulation_title()
                if mode == 'simulate':
                    self.decision = Decision()
                    self.advance_simulation(1)
                elif mode == 'simulate_ia':
                    self.decision = Decision(ruleset='ia')

        elif mode == 'analyze':
            self.cancel_button.disabled = True
            self.cancel_button.opacity = 0
            self.update_button_states()
            self.show_uc_annotation_controls(makeVisible=False)
            self.reanalyze_raw_recording_data()


    def cleanup_on_stop(self):
        print 'PlotPopup: called cleanup_on_stop'
        self.completion_status = 'cancel'
        self.stop_all_recording_threads(isCancelled=True)


    def do_gc(self):
        """Proactive garbage collection to preserve realtime performance"""
        gc.collect()


    #
    # Data management routines
    #

    def load_data(self):
        try:
            with open(self.metadata_file, 'rb') as fd:
                data = pickle.load(fd)
        except Exception:
            with open(self.metadata_file, 'r') as fd:
                data = pickle.load(fd)

        if 'combined' not in data:
            self.data = self.transform_legacy_data(data)
        else:
            self.data = data

        if 'uc_source' not in self.data and 'uc' not in self.data:
            self.data['uc_source'] = None

        if 'uc_ann' not in self.data:
            self.data['uc_ann'] = None

        print 'start_time:{} end_time: {}  recording_duration: {}'.format(
            self.data['start_time'], self.data['end_time'], self.data['recording_duration'])


    def initialize_clone_data(self):
        """Stashes recorded data away and reinitialized data for incremental playback"""
        self.reference_data = self.data

        for k in ['pitch', 'envelope', 'combined']:
            if k in self.reference_data:
                for kk, vv in self.reference_data[k].items():
                    if not isinstance(vv, np.ndarray):
                        self.reference_data[k][kk] = np.array(vv)

        # Duplicate basic structure
        self.data = {}
        for k, v in self.reference_data.items():
            if isinstance(v, dict):
                self.data[k]  = {}
            elif isinstance(v, list):
                self.data[k]  = []
            else:
                self.data[k]  = v


    def clone_subset_data(self):
        """Presents recorded data up to specified minutes of recording time"""

        tStartSec = int(self.simulation_start_time * 60)
        tEndSec = int(self.simulation_time * 60)
        if 'uc_ann' in self.reference_data and isinstance(self.reference_data['uc_ann'], list):
            uc_ann = self.reference_data['uc_ann']
            self.data['uc_ann'] = [ann for ann in uc_ann if ann['time'] >= tStartSec and ann['time'] <= tEndSec]

        for k in ['pitch', 'envelope', 'combined']:
            if k in self.reference_data:
                pos = self.reference_data[k]['pos']
                mask = np.logical_and(pos >= tStartSec, pos <= tEndSec)
                for kk, vv in self.reference_data[k].items():
                    self.data[k][kk] = vv[mask]

        if ('uc' in self.reference_data and isinstance(self.reference_data['uc'], dict)
                and len(self.reference_data['uc']) > 0):
            pos = self.reference_data['uc']['pos']
            mask = np.logical_and(pos >= tStartSec, pos <= tEndSec)
            for kk, vv in self.reference_data['uc'].items():
                self.data['uc'][kk] = vv[mask]

        self.current_plot_state['hr_updated'] = 'combined' in self.data
        self.current_plot_state['uc_updated'] = 'uc' in self.data or self.data['uc_ann'] is not None


    def transform_legacy_data(self, data):
        print 'transform_legacy_data:', data.keys()

        if 'hr' not in data and 'envelope' not in data:
            data['fhr_source'] = None
            return data

        if 'version' not in data or data['version'] == 1:
            subset = copy.copy(data)
            for k in subset.keys():
                if k not in ['hr', 'raw', 'valid','pos', 'cor']:
                    del subset[k]

            data['envelope'] = copy.copy(subset)
            data['pitch'] = copy.copy(subset)
            for k in data.keys():
                if k in ['hr', 'raw', 'valid','pos', 'cor']:
                    del data[k]

        if 'combined' not in data:
            print 'creating combined data'
            N = min(len(data['envelope']['hr']), len(data['pitch']['hr']))
            combinedHR, combinedMask = combineExtractionResults(data['envelope']['hr'][:N],
                                                                data['pitch']['hr'][:N])
            pos = data['envelope']['pos'][:len(combinedHR)]
            data['combined'] = {'hr': combinedHR, 'valid': combinedMask, 'pos': pos}

        if 'fhr_source' not in data:
            data['fhr_source'] = 'LowCostCTG'

        return data


    def reanalyze_raw_recording_data(self):
        # performs signal analysis on raw audio and tocopatch files

        # TODO:  Implement analysis function
        # self.metadata_file
        # self.audio_file
        # self.toco_file
        pass


    #
    # Simulation code
    #

    def skip_simulation(self, count):
        self.simulation_start_time += count
        self.simulation_time = self.simulation_start_time
        self.update_simulation_title()

    def update_simulation_title(self):
        if self.mode == 'simulate_ia':
            self.title = 'Intermittent Auscultation Simulation: {}-{} min'.format(self.simulation_start_time, self.simulation_time)
        else:
            self.title = 'Continuous Monitoring Simulation: {}-{} min'.format(self.simulation_start_time, self.simulation_time)


    def advance_simulation(self, count):
        """Advanced recording specified minutes and processes data"""
        if self.mode == 'simulate_ia':
            self.hide_skip_button()

        self.simulation_time += count
        self.update_simulation_title()
        self.clone_subset_data()

        if self.data['fhr_source'] is not None:
            try:
                self.data['annotations'] = self.detectPatternsHR()
                if self.data['annotations'] == {}:
                    # detect patterns failed to produce results
                    return
                tStart = self.data['combined']['pos'][0] / 60.0
                tEnd = self.data['combined']['pos'][-1] / 60.0
                self.decision_outcome = self.decision.executeRules(self.data['annotations'], self.allUC, tEnd, tStart=tStart)
                if 'fetus' in self.decision_outcome['assessment']:
                    self.assessment_history.append([tEnd, self.decision_outcome['assessment']['fetus']])
                self.revise_assessment()
                self.current_plot_state['assessment_updated'] = True
            except Exception, e:
                print 'Exception during detectPatternsHR:', e


        Clock.schedule_once(lambda x: self.update_plot_display(), 0)


    #
    # Recording Management
    #

    def perform_recording(self):
        self.perform_audio_recording()
        self.perform_toco_recording()

    def end_recording(self):
        assert self.mode in ['record']          # only called for recordings

        status = self.completion_status
        print 'completion_after_confirmation', status

        self.stop_all_recording_threads(isCancelled=(status in ['restart', 'cancel']))

        if status in ['done']:
            self.recording_postprocessing()
            if self.completion_callback:
                self.completion_callback({
                    'start_time': self.data['start_time'],
                    'recording_duration': self.data['recording_duration']})

        elif status in ['restart', 'cancel']:
            # discard any new database files
            if self.audio_file and os.path.exists(self.audio_file):
                os.remove(self.audio_file)
            if self.metadata_file and os.path.exists(self.metadata_file):
                os.remove(self.metadata_file)

        if status  == 'restart':
            self.dismiss()
            if self.restart_callback:
                # try again
                self.restart_callback()
        else:
            self.dismiss()


    def stop_all_recording_threads(self, isCancelled):
        if self.audio_thread is not None:
            self.audio_thread.stop(isCancelled=isCancelled)

        if self.toco_listener is not None:
            self.toco_listener.stop(isCancelled=isCancelled)

        if self.audio_thread is not None:
            self.audio_thread.wait()

        if self.toco_listener is not None:
            self.toco_listener.wait()
        pass


    def recording_postprocessing(self):
        if self.enable_realtime_pattern:
            try:
                # TODO:  Update to use UC information as well
                self.data['annotations'] = self.detectPatternsHR()
            except Exception:
                print 'recording_finished - exception during combineExtractionResults'
                pass

        if self.metadata_file is not None:
            print 'recording_finished'
            print 'writing metadata file:', self.metadata_file
            with open(self.metadata_file, 'wb') as fd:
                pickle.dump(self.data, fd)

    #
    # Audio code
    #

    def perform_audio_recording(self, fname=None):
        self.data['fhr_source'] = 'LowCostCTG'

        self.audio_config = audio_detect()
        preferred_audio_input, preferred_audio_output = select_preferred_io(self.audio_config)
        print 'Recording Preferred I/O -- input: {}  output: {}'.format(preferred_audio_input, preferred_audio_output)

        self.audio_thread = audio_recorder(fname, outfile=self.audio_file,
                                          update_callback=self.audio_recording_update,
                                          completion_callback=self.audio_recording_finished,
                                          enable_playback=preferred_audio_output is not None,
                                          audio_in_chan=preferred_audio_input,
                                          audio_out_chan=preferred_audio_output,
                                          extractor_params = AppWithParams.getParam('extractor'),
                                          tachycardia = AppWithParams.getParam('tachycardia'),
                                          bradycardia = AppWithParams.getParam('bradycardia')
        )


    def audio_recording_update(self, extractor_instance, extractor_name, current_pos):
        # Reduce plot update rate when in analysis mode

        results = extractor_instance.get_results(asNumpy=False)
        if self.audio_start_time is None:
            self.audio_start_time = time.time()-len(results['pos']) - EXTRACTOR_ARGS['corrWidth']/2000.0
            # time of first result
            # minus number of samples (at 1 sec each)
            # minus 50% of corrWidth is lag due to offset from center of autocorrelation window.

        self.data[extractor_name] = results

        print '{}: {:0.0f} bpm @ {:0.0f} sec -- cor: {:0.2f}  rel: {:0.2f}'.format(
            extractor_name,
            results['hr'][-1], results['pos'][-1],
            results['cor'][-1], results['rel'][-1])
        sys.stdout.flush()

        try:
            if 'hr' in self.data['envelope'] and 'hr' in self.data['pitch']:
                N = min(len(self.data['envelope']['hr']), len(self.data['pitch']['hr']))
                combinedHR, combinedMask = combineExtractionResults(np.array(self.data['envelope']['hr'][:N]),
                                                                    np.array(self.data['pitch']['hr'][:N]))
                pos = self.data['envelope']['pos'][:len(combinedHR)]
                self.data['combined'] = {'hr': combinedHR, 'valid': combinedMask, 'pos':pos}
            elif 'hr' in self.data['envelope']:
                self.data['combined'] = self.data['envelope']
            else:
                self.data['combined'] = self.data['pitch']

            if self.enable_realtime_pattern and current_pos != 0 and current_pos % 60 == 0:
                self.data['annotations'] = self.detectPatternsHR()

        except Exception, e:
            print 'Exception during combineExtractionResults', e

            print '-' * 60
            traceback.print_exc(file=sys.stdout)
            print '-' * 60

        self.current_plot_state['hr_updated'] = True

        #print 'audio_recording_update scheduling update_plot_display'
        Clock.schedule_once(lambda x: self.update_plot_display(), 0)
        if current_pos != 0 and current_pos % 60 == 1:
            Clock.schedule_once(lambda x: self.do_gc, 0)


    def audio_recording_finished(self, results):
        self.data['envelope'] = results['envelope']
        self.data['pitch'] = results['pitch']

        start_time = self.audio_thread.get_start_time()
        self.data['start_time'] = int(start_time)
        self.data['end_time'] = int(time.time())
        self.data['recording_duration'] = (self.data['end_time'] - self.data['start_time'])/60.0
        print self.data['recording_duration'], self.data['end_time'], self.data['start_time']

        try:
            combinedHR, combinedMask = combineExtractionResults(np.array(self.data['envelope']['hr']),
                                                                np.array(self.data['pitch']['hr']))
            pos = self.data['envelope']['pos'][:len(combinedHR)]
            self.data['combined'] = {'hr': combinedHR, 'valid': combinedMask, 'pos': pos}
        except Exception:
            print 'recording_finished - exception during combineExtractionResults'
            pass

        self.audio_thread = None


    #
    # TocoPatch Routines (including listener callbacks)
    #

    def perform_toco_recording(self):
        if not self.useTocopatch:
            self.toco_listener = None
            return

        print 'called perform_toco_recording'

        self.data['uc_source'] = 'tocopatch'
        recording_file = None if self.readonly else self.toco_file
        self.toco_listener = HeartyPatch_Listener(host=self.host, max_packets=-1, max_seconds=-1,
                                         outfile=recording_file, warmup_sec=0,
                                         connection_callback=self.toco_listener_connection_callback,
                                         update_callback=self.toco_listener_update_callback,
                                         #update_interval=16*5,
                                         update_interval=16*1,
                                         completion_callback=self.toco_listener_completion_callback)
        self.toco_listener.go()


    def toco_listener_connection_callback(self, *args):
        """Dummy callback -- currentlyu unused"""
        pass


    def toco_listener_update_callback(self, listener, abort, min_samples=128*5):
        print 'called toco_listener_update_callback'

        if self.toco_start_time is None:
            self.toco_start_time = self.toco_listener.get_start_time()
        if self.toco_skew is None and self.audio_start_time is not None and self.toco_start_time is not None:
            self.toco_skew = self.toco_start_time - self.audio_start_time

        sigIn, ts, seqID = self.toco_listener.getData()

        print 'update', len(sigIn), len(ts), len(seqID), 'sample rate:', self.toco_listener.sample_rate
        if len(sigIn) < min_samples:
            return

        sigIn = np.array(sigIn)
        self.processUC.updateFS(self.toco_listener.get_sample_rate())
        skew = self.toco_skew if self.toco_skew is not None else 0
        ts, sigD, sigRel, sigUC, sigAltUC = self.processUC.processData(sigIn, skew=skew)

        self.data['uc'] = {'posMin': ts/60.0, 'pos': ts,
                          'filtered': sigRel, 'raw':sigD, 'uc':sigUC, 'alt_uc':sigAltUC}

        self.current_plot_state['uc_updated'] = True
        Clock.schedule_once(lambda x: self.update_plot_display(), 0)


    def toco_listener_completion_callback(self, listener, abort):
        sigIn, ts, seqID = self.toco_listener.getData()
        print 'completion', len(sigIn), len(ts), len(seqID)
        sigIn = np.array(sigIn)

        self.processUC.updateFS(self.toco_listener.get_sample_rate())

        skew = self.toco_skew if self.toco_skew is not None else 0
        ts, sigD, sigRel, sigUC, sigAltUC = self.processUC.processData(sigIn, skew=skew)
        self.data['uc'] = {'posMin': ts/60.0, 'pos': ts,
                           'filtered': sigRel, 'raw':sigD, 'uc':sigUC, 'alt_uc':sigAltUC}
        self.toco_listener = None


    #
    # Signal Analysis
    #

    def detectPatternsHR(self, **kwargs):
        """wrapper for computeAnnotations"""
        try:
            if self.data['uc_source'] is None:
                # use manual annotations
                if self.data['uc_ann'] is not None:
                    allUC = [ann['time']/60.0 for ann in self.data['uc_ann'] if ann['annotation'] == 'acme']
                else:
                    allUC = []
            else:
                posMin = self.data['uc']['posMin']
                _, allUC = findUC(self.data['uc']['uc'], posMin)
            self.allUC = allUC  # save for simulation

            sigHR = self.data['combined']['hr']
            mask = self.data['combined']['valid']
            ts = np.array(self.data['combined']['pos']) / 60.0

            result = extractAllDecels(sigHR, mask, ts, allUC=allUC, allExtractorParams=FEATURE_EXTRACT_PARAMS)
            if result == {}:
                print 'extractAllDecels returned empty result'
                return result
            result['log'] = summarizeDecels(result['decels'], shouldPrint=False)
            result['uc_acme'] = allUC

            return result
        except Exception, e:
            print 'Exception during detectPatternsHR', e

            print '-' * 60
            traceback.print_exc(file=sys.stdout)
            print '-' * 60
            return {}


    # Support for Manual UC Annotations
    def ucFilterAnnotations(self, raw_annotations, ignoreMultipleAcme=False):
        start_time = self.audio_start_time

        filtered = []
        last_start = None
        for raw in raw_annotations:
            cmd = raw['annotation']
            ann = {'annotation': cmd, 'time': raw['time'] - start_time}
            # print ann

            if cmd == 'ignore':
                if last_start is not None:
                    filtered = filtered[:last_start]
                    last_start = None
                else:
                    filtered = filtered[:-1]
            elif cmd == 'onset':
                if filtered and filtered[-1]['annotation'] == 'onset':
                    # back-to-back onset
                    filtered = filtered[:-1]
                last_start = len(filtered)
                filtered.append(ann)
            elif cmd == 'release':
                if filtered and filtered[-1]['annotation'] == 'release':
                    # back-to-back release
                    filtered = filtered[:-1]
                filtered.append(ann)
            elif ignoreMultipleAcme and cmd == 'acme':
                if filtered and filtered[-1]['annotation'] == 'acme':
                    # back-to-back release
                    filtered = filtered[:-1]
                filtered.append(ann)
            else:
                filtered.append(ann)

        return filtered


    #
    # Button and Visibility Management
    #

    def touched_entity(self, val):
        global ENTITY_TO_VIEW
        if val in ENTITY_TO_VIEW and ENTITY_TO_VIEW[val] is not None:
            self.current_plot_state['view'] = ENTITY_TO_VIEW[val]
            Clock.schedule_once(lambda x: self.update_plot_display(), 0)


    def showAssessmentField(self, visible=False):
        if visible:
            self.assessment_text.opacity = 1
            self.assessment_text.size_hint = (1, 0.0725)
        else:
            self.assessment_text.opacity = 0
            self.assessment_text.size_hint = (1, 0.01)



    # used as replacement for uc_annotate_button_pressed
    def simulate_intercept_uc_annotate_button_pressed(self, val):
        if val == 'release':
            return self.advance_simulation(1)
        else:
            return self.advance_simulation(10)

    def simulate_ia_intercept_uc_annotate_button_pressed(self, val):
        if val == 'release':
            return self.advance_simulation(1)
        else:
            return self.skip_simulation(5)


    def do_pan_zoom(self, val):
        assert val in ['left', 'right', 'zoom_in', 'zoom_out']
        #print 'pan_zoom:', val
        self.update_scale_limits(val)
        Clock.schedule_once(lambda x: self.update_plot_display(), 0)


    def show_pan_zoom_controls(self,val):
        if val:
            self.pan_zoom_area.disabled = False
            self.pan_zoom_area.opacity = 1
            self.pan_zoom_area.size_hint = (1, 0.125)
        else:
            self.pan_zoom_area.disabled = True
            self.pan_zoom_area.opacity = 0
            self.pan_zoom_area.size_hint = (1, 0.01)


    def do_completion(self, status):
        print 'completion:', status, self.mode
        if self.mode in ['view', 'simulate', 'simulate_ia']:
            self.dismiss()
        else:
            self.completion_status = status
            if status in ['done']:
                msg = 'Are you sure you want to finish this recording?'
            else:
                msg = 'Are you sure you want to ' + status + ' this recording?'

            popup = ConfirmRecordingPopup(callback=self.end_recording, msg=msg)
            popup.open()


    def select_plot_view(self, mode):
        #print 'select_plot_view:', mode
        if mode is not None:
            self.current_plot_state['view'] = mode
        # else:
        #     print 'select_plot_view current:', self.current_plot_state['view']


        self.dashboard_button.state = 'normal'
        self.analysis_button.state = 'normal'
        self.combined_button.state = 'normal'
        self.fhr_detail_button.state = 'normal'
        self.uc_detail_button.state = 'normal'
        self.decel_button.state = 'normal'

        if self.current_plot_state['view'] == 'dashboard':
            self.dashboard_button.state = 'down'
        elif self.current_plot_state['view'] == 'analysis':
            self.analysis_button.state = 'down'
        elif self.current_plot_state['view'] =='combined':
            self.combined_button.state = 'down'
        elif self.current_plot_state['view'] =='fhr_detail':
            self.fhr_detail_button.state = 'down'
        elif self.current_plot_state['view'] =='uc_detail':
            self.uc_detail_button.state = 'down'
        elif self.current_plot_state['view'] =='decel':
            self.decel_button.state = 'down'
        else:
            print 'unknown  view', self.current_plot_state['view']

        #print 'select_plot_view scheduling update_plot_display for', mode, self.current_plot_state['view']
        Clock.schedule_once(lambda x: self.update_plot_display(), 0)


    def select_plot_duration(self, mode):

        #print 'select_plot_duration:', mode
        if mode is not None:
            self.current_plot_state['scale'] = mode
            self.current_plot_state['scale_limits'] = None

        self.recent_button.state = 'normal'
        self.full_button.state = 'normal'
        self.pan_zoom_button.state = 'normal'

        if self.current_plot_state['scale'] == 'recent':
            self.recent_button.state = 'down'
            self.show_pan_zoom_controls(False)
        elif self.current_plot_state['scale'] == 'full':
            self.full_button.state = 'down'
            self.show_pan_zoom_controls(False)
        elif self.current_plot_state['scale'] == 'pan_zoom':
            self.pan_zoom_button.state = 'down'
            self.show_pan_zoom_controls(True)

        #print 'select_plot_duration scheduling update_plot_display'
        Clock.schedule_once(lambda x: self.update_plot_display(), 0)


    def show_plot_duration_controls(self, val):
        if val:
            self.recent_button.opacity = 1
            self.full_button.opacity = 1
            self.pan_zoom_button.opacity = 1
        else:
            self.recent_button.opacity = 0
            self.full_button.opacity = 0
            self.pan_zoom_button.opacity = 0


    def update_button_states(self):
        #print 'called update_button_states', self.current_plot_state['view'], self.current_plot_state['scale']
        self.select_plot_view(None)
        self.select_plot_duration(None)


    def uc_annotate_button_pressed(self, status):
        print 'uc_annotate_button_pressed:', status
        self.rawAnnotations.append({'annotation': status, 'time': time.time()})
        self.data['uc_ann'] = self.ucFilterAnnotations(self.rawAnnotations)
        pprint(self.data['uc_ann'])
        self.current_plot_state['uc_updated'] = True   # trigger update of plots


    def show_uc_annotation_controls(self, makeVisible=True):
        if makeVisible:
            self.uc_onset_button.disabled = False
            self.uc_acme_button.disabled = False
            self.uc_release_button.disabled = False
            self.uc_ignore_button.disabled = False

            self.uc_onset_button.opacity = 1
            self.uc_acme_button.opacity = 1
            self.uc_release_button.opacity = 1
            self.uc_ignore_button.opacity = 1
        else:
            self.uc_onset_button.disabled = True
            self.uc_acme_button.disabled = True
            self.uc_release_button.disabled = True
            self.uc_ignore_button.disabled = True

            self.uc_onset_button.opacity = 0
            self.uc_acme_button.opacity = 0
            self.uc_release_button.opacity = 0
            self.uc_ignore_button.opacity = 0


    def hide_skip_button(self):
        self.uc_ignore_button.disabled = True
        self.uc_ignore_button.opacity = 0

    def repurpose_uc_annotation_controls(self, mode):
        # HACK:  Re-use annotation buttons for simulation controls
        # HACK: overwrite handler
        if mode == 'simulate':
            self.uc_annotate_button_pressed = self.simulate_intercept_uc_annotate_button_pressed
            self.uc_release_button.text = 'Step'
            self.uc_ignore_button.text = 'Step 10'
        else:
            self.uc_annotate_button_pressed = self.simulate_ia_intercept_uc_annotate_button_pressed
            self.uc_release_button.text = 'Step'
            self.uc_ignore_button.text = 'Skip 5'

        # show Step buttons
        self.uc_release_button.opacity = 1
        self.uc_ignore_button.opacity = 1
        self.uc_release_button.disabled = False
        self.uc_ignore_button.disabled = False

        # hide unused buttons
        self.uc_onset_button.disabled = True
        self.uc_acme_button.disabled = True
        self.uc_onset_button.opacity = 0
        self.uc_acme_button.opacity = 0


    #
    # Plot Creation Routines
    #

    def create_dashboard_view_plots(self):
        dashboard = Dashboard(self.touched_entity)

        dashboard.size_hint = (1, 0.8)
        self.allGraphs['dashboard'] = dashboard
        self.plot_area.add_widget(dashboard)

        lab = Label(text='Assessment History', size_hint=(1, 0.05))
        self.plot_area.add_widget(lab)

        graph = SimpleLineGraph(ymin=0, ymax=ASSESSMENT_DISPLAY_MAX_ROWS, plot_type='ScatterPlot',
                                pointsize=5, **self.graphspec_no_y)

        for name, v in ASSESSMENT_DISPLAY.items():
            assert 'row' in v
            if v['row'] is not None:
                color = v['color']
                graph.add_another_plot(name, color=color, plot_type='ScatterPlot', pointsize=5)
                #print 'creating scatter', name, color


        graph.size_hint = (1, 0.2)
        self.allGraphs['assessment_history'] = graph
        self.plot_area.add_widget(graph)


    def create_decel_view_plots(self):
        log = ScrollableLabel(text='')
        self.allGraphs['log'] = log
        self.plot_area.add_widget(log)
        pass


    def create_analysis_view_plots(self):
        # Basal HR Plot
        box = BoxLayout(orientation='horizontal')
        lab = Label(text='BasalHR', size_hint=(0.1, 1))
        box.add_widget(lab)

        graph = SimpleLineGraph(ymin=50, ymax=200, y_ticks_major=10, y_ticks_minor=1, plot_type='ScatterPlot',
                                pointsize=5, **self.common_graphspec)
        graph.add_another_plot('minute', color=COLORS['cyan'], plot_type='ScatterPlot', pointsize=3)
        for i in [AppWithParams.params['bradycardia'], AppWithParams.params['tachycardia']]:
            graph.add_horizontal_annotations(i, color=COLORS['red'], line_width=1.5)
        self.allGraphs['baseline'] = graph
        graph.size_hint=(0.9, 1)
        box.add_widget(graph)
        box.size_hint = (1, 1)
        self.plot_area.add_widget(box)

        # Variability Plot
        box = BoxLayout(orientation='horizontal')
        lab = Label(text='Var', size_hint=(0.1, 1))
        box.add_widget(lab)

        graph = SimpleLineGraph(ymin=0, ymax=40, y_ticks_major=10, y_ticks_minor=1, plot_type='ScatterPlot',
                                pointsize=5, **self.common_graphspec)
        for i in [5.0, 25.0]:
            graph.add_horizontal_annotations(i, color=COLORS['red'], line_width=1.25)

        self.allGraphs['variability'] = graph
        graph.size_hint=(0.9, 1)
        box.add_widget(graph)
        box.size_hint = (1, 0.5)
        self.plot_area.add_widget(box)

        # Annotation plot - accelerations and decelerations
        box = BoxLayout(orientation='horizontal')
        lab = Label(text='Decel', size_hint=(0.1, 1))
        box.add_widget(lab)

        graph = SimpleLineGraph(ymin=0, ymax=1, **self.graphspec_no_y)
        self.allGraphs['artifacts'] = graph
        graph.size_hint=(0.9, 1)
        box.add_widget(graph)
        box.size_hint = (1, 0.4)
        self.plot_area.add_widget(box)


    def create_combined_view_plots(self):
        # FHR Plot
        box = BoxLayout(orientation='horizontal')
        lab = Label(text='FHR', size_hint=(0.1, 1))
        box.add_widget(lab)

        graph = SimpleLineGraph(ymin=50, ymax=200, y_ticks_major=10, y_ticks_minor=1, **self.common_graphspec)
        graph.add_another_plot('baseline', color=COLORS['fuchia'], line_width=2)
        graph.add_another_plot('baseline+15', color=COLORS['green'], line_width=1.25)
        graph.add_another_plot('baseline-15', color=COLORS['green'], line_width=1.25)
        for i in [AppWithParams.params['bradycardia'], AppWithParams.params['tachycardia']]:
            graph.add_horizontal_annotations(i, color=COLORS['red'], line_width=1.5)
        graph.size_hint=(0.9, 1)
        self.allGraphs['hr'] = graph
        box.add_widget(graph)
        box.size_hint = (1, 1)
        self.plot_area.add_widget(box)

        # spacer
        w = Widget(size_hint=(1, 0.1))
        self.plot_area.add_widget(w)

        # Valid Plot
        box = BoxLayout(orientation='horizontal', size_hint=(1, 0.3))
        lab = Label(text='Invalid', size_hint=(0.1, 1))
        box.add_widget(lab)

        graph = SimpleLineGraph(ymin=-0.05, ymax=0.005, ylabel=' ', **self.graphspec_no_x)
        self.allGraphs['valid'] = graph
        graph.size_hint = (0.9, 1)
        box.add_widget(graph)
        box.size_hint = (1, 0.1)
        self.plot_area.add_widget(box)

        # UC Plot
        box = BoxLayout(orientation='horizontal')
        lab = Label(text='UC', size_hint=(0.1, 1))
        box.add_widget(lab)

        graph = SimpleLineGraph(**self.graphspec_no_y)
        self.allGraphs['uc'] = graph
        graph.size_hint = (0.9, 1)
        box.add_widget(graph)
        box.size_hint = (1, 0.3)
        self.plot_area.add_widget(box)


    def create_fhr_detail_view_plots(self):
        if self.data['fhr_source'] is None:
            return

        # Plots for Envelope
        lab = Label(text='Envelope', bold=True, color=COLORS['yellow'], size_hint=(1, 0.1))
        lab.bind(size=lab.setter('text_size'))
        self.plot_area.add_widget(lab)

        # Envelope FHR Plot
        box = BoxLayout(orientation='horizontal')
        lab = Label(text='FHR', size_hint=(0.1, 1))
        box.add_widget(lab)

        graph = SimpleLineGraph(ymin=50, ymax=200, y_ticks_major=20, y_ticks_minor=2, **self.common_graphspec)
        self.allGraphs['envelope_fhr'] = graph
        graph.size_hint = (0.9, 1)
        box.add_widget(graph)
        self.plot_area.add_widget(box)

        # spacer
        w = Widget(size_hint=(1, 0.05))
        self.plot_area.add_widget(w)

        # Envelope Valid Plot
        box = BoxLayout(orientation='horizontal', size_hint=(1, 0.2))
        lab = Label(text='Invalid', size_hint=(0.1, 1))
        box.add_widget(lab)

        #graph = SimpleLineGraph(ymin=-0.05, ymax=0.05, y_ticks_major=0.05, y_ticks_minor=1, **self.graphspec_no_x)
        graph = SimpleLineGraph(ymin=-0.05, ymax=0.005, ylabel=' ', **self.graphspec_no_x)
        self.allGraphs['envelope_valid'] = graph
        graph.size_hint = (0.9, 1)
        box.add_widget(graph)
        self.plot_area.add_widget(box)

        # Envelope Corr Plot
        box = BoxLayout(orientation='horizontal', size_hint=(1, 0.4))
        lab = Label(text='Corr', size_hint=(0.1, 1))
        box.add_widget(lab)

        graph = SimpleLineGraph(ymin=0, ymax=2, y_ticks_major=1, y_ticks_minor=2, **self.graphspec_no_x)
        self.allGraphs['envelope_corr'] = graph
        graph.size_hint = (0.9, 1)
        box.add_widget(graph)
        self.plot_area.add_widget(box)

        # Plots for Pitch
        lab = Label(text='Pitch', bold=True, color=COLORS['yellow'], size_hint=(1, 0.1))
        lab.bind(size=lab.setter('text_size'))
        self.plot_area.add_widget(lab)

        # Pitch FHR Plot
        box = BoxLayout(orientation='horizontal')
        lab = Label(text='FHR', size_hint=(0.1, 1))
        box.add_widget(lab)

        graph = SimpleLineGraph(ymin=50, ymax=200, y_ticks_major=20, y_ticks_minor=2, **self.common_graphspec)
        self.allGraphs['pitch_fhr'] = graph
        graph.size_hint = (0.9, 1)
        box.add_widget(graph)
        self.plot_area.add_widget(box)

        # spacer
        w = Widget(size_hint=(1, 0.05))
        self.plot_area.add_widget(w)

        # Pitch Valid Plot
        box = BoxLayout(orientation='horizontal', size_hint=(1, 0.2))
        lab = Label(text='Invalid', size_hint=(0.1, 1))
        box.add_widget(lab)

        # Hack:  use of ylabel=' ' to force alignment
        graph = SimpleLineGraph(ymin=-0.05, ymax=0.005, ylabel=' ', **self.graphspec_no_x)
        self.allGraphs['pitch_valid'] = graph
        graph.size_hint = (0.9, 1)
        box.add_widget(graph)
        self.plot_area.add_widget(box)

        # Pitch Corr Plot
        box = BoxLayout(orientation='horizontal', size_hint=(1, 0.4))
        lab = Label(text='Corr', size_hint=(0.1, 1))
        box.add_widget(lab)

        graph = SimpleLineGraph(ymin=0, ymax=2, y_ticks_major=1, y_ticks_minor=2, **self.graphspec_no_x)
        self.allGraphs['pitch_corr'] = graph
        graph.size_hint = (0.9, 1)
        box.add_widget(graph)
        self.plot_area.add_widget(box)


    def create_uc_detail_viewplots(self):

        box = BoxLayout(orientation='horizontal')
        lab = Label(text='Raw', size_hint=(0.1, 1))
        box.add_widget(lab)

        graph = SimpleLineGraph(**self.graphspec_no_y_no_x)
        self.allGraphs['uc_raw'] = graph
        graph.size_hint = (0.9, 1)
        box.add_widget(graph)
        self.plot_area.add_widget(box)

        box = BoxLayout(orientation='horizontal')
        lab = Label(text='Filt', size_hint=(0.1, 1))
        box.add_widget(lab)

        graph = SimpleLineGraph(**self.graphspec_no_y)
        graph.add_another_plot('alt_uc', color=COLORS['fuchia'], line_width= 2)
        self.allGraphs['uc_filtered'] = graph
        graph.size_hint = (0.9, 1)
        box.add_widget(graph)
        self.plot_area.add_widget(box)

        box = BoxLayout(orientation='horizontal')
        lab = Label(text='UC', size_hint=(0.1, 1))
        box.add_widget(lab)

        graph = SimpleLineGraph(**self.graphspec_no_y_no_x)
        self.allGraphs['uc_extract'] = graph
        graph.size_hint = (0.9, 1)
        box.add_widget(graph)
        self.plot_area.add_widget(box)


    #
    # Plot Update Routines
    #

    def update_plot_display(self):
        # print
        # print 'update_plot_display', self.mode
        # print
        # #self.show_plot_state()
        # print

        if self.mode in ['simulate', 'simulate_ia']:
            self.showAssessmentField(True)

        if self.current_plot_state['view'] == 'dashboard':
            self.showAssessmentField(False)
            self.show_plot_duration_controls(False)
            self.show_pan_zoom_controls(False)
        else:
            self.show_plot_duration_controls(True)
            if self.current_plot_state['scale'] == 'pan_zoom':
                self.show_pan_zoom_controls(True)
            else:
                self.show_pan_zoom_controls(False)

        if self.plot_is_current():
            return

        if self.plot_view_changed():
            # remove previous view
            self.plot_area.clear_widgets()
            self.allGraphs = {}

        if self.current_plot_state['view'] == 'dashboard':
            self.revise_dashboard_view()
        elif self.current_plot_state['view'] == 'decel':
            self.revise_decel_view()
        elif self.current_plot_state['view'] == 'analysis':
            self.revise_analysis_view()
        elif self.current_plot_state['view'] =='combined':
            self.revise_combined_view()
        elif self.current_plot_state['view'] =='fhr_detail':
            self.revise_fhr_detail_view()
        elif self.current_plot_state['view'] =='uc_detail':
            self.revise_uc_detail_view()

        self.reset_plot_state()


    def revise_dashboard_view(self):
        global ASSESSMENT_DISPLAY
        if self.allGraphs == {}:
            self.create_dashboard_view_plots()
        elif not self.current_plot_state['assessment_updated']:
            return

        if self.decision_outcome is None:
            return

        dashboard = self.allGraphs['dashboard']

        dashboard.assessment.text = 'Assessment: {}'.format(self.decision_outcome['assessment']['fetus'])
        dashboard.recommendations_area.text = '\n'.join(self.decision_outcome['firings_log'])

        entity_to_field = {
            'fetalAccelerations': {'name':'Accelerations', 'display': dashboard.accelerations},
             'fetalDecelerations': {'name':'Decelerations', 'display': dashboard.decelerations},
             'fetalHR': {'name':'Baseline HR', 'display': dashboard.baseline_hr},
             'fetalVariability': {'name':'Variability', 'display': dashboard.variability},
             'fetus': {'name':'Assessment', 'display': dashboard.assessment},
             'maternalContractions': {'name':'Contractions', 'display': dashboard.contractions},
             }

        for k, v in self.decision_outcome['assessment'].items():
            if k in entity_to_field:
                field = entity_to_field[k]['display']
                name = entity_to_field[k]['name']

                if v in ASSESSMENT_DISPLAY:
                    val = ASSESSMENT_DISPLAY[v]['text']
                    color = ASSESSMENT_DISPLAY[v]['color']
                else:
                    val = v
                    color = None

                field.text = '{}: {}'.format(name, val)
                if color is not None:
                    field.color = color

        #dashboard.assessment.text = 'Assessment: {}'.format(self.decision_outcome['assessment']['fetus'])
        #dashboard.recommendations_area.text = '\n'.join(self.decision_outcome['firings_log'])
        dashboard.recommendations_area.text = '\n'.join(self.decision_outcome['recommendations'])


        if self.assessment_history:
            hist = self.assessment_history
            tStart = 0
            tStart = max(math.floor(hist[0][0])-1, 0)
            tEnd = math.ceil(hist[-1][0])
            graph = self.allGraphs['assessment_history']
            # updatre scatter plot associated with this assessment
            for name, v in ASSESSMENT_DISPLAY.items():
                if 'row' not in ASSESSMENT_DISPLAY[name]:
                    continue
                row  = ASSESSMENT_DISPLAY[name]['row']
                if row is not None:
                    row =  ASSESSMENT_DISPLAY[name]['row']
                    self.update_individual_plot_display(graph,
                                                        [t for t, x in hist if x == name],
                                                        [row for t, x in hist if x == name],
                                                        tStart, tEnd, line_name=name)
            #graph.update_x_scale(self.simulation_start_time, max(self.simulation_time, self.simulation_start_time+1))
            graph.update_x_scale(tStart, tEnd)

    def revise_assessment(self):
        global ASSESSMENT_DISPLAY
        val = self.decision_outcome['assessment']['fetus']
        self.assessment_text.text = 'Assessment: {}'.format(val)

        if val in ASSESSMENT_DISPLAY:
            color = ASSESSMENT_DISPLAY[val]['color']
            self.assessment_text.color = color



    def revise_decel_view(self):
        if self.allGraphs == {}:
            self.create_decel_view_plots()

        if 'annotations' in self.data and 'log' in self.data['annotations']:
            #print 'found annotations'
            self.allGraphs['log'].text = self.data['annotations']['log']
        else:
            print 'no annotations'
            self.allGraphs['log'].text = ''


    def revise_analysis_view(self):
        if self.allGraphs == {}:
            self.create_analysis_view_plots()

        pos = self.data['combined']['pos']
        posMin = self.convertTimescaleToMin(pos)
        tStart, tEnd = self.compute_time_limits(posMin)
        idxStart, idxEnd = self.findIndexLimits(posMin, tStart, tEnd)

        if idxStart is not None and 'annotations' in self.data and self.data['annotations'] != {}:
            posMin = posMin[idxStart:idxEnd]
            graph = self.allGraphs['baseline']
            basalHR = self.data['annotations']['basalHR']
            self.update_individual_plot_display(graph,
                                                [t for x, t in basalHR if x is not None],
                                                [x for x, t in basalHR if x is not None],
                                                tStart, tEnd, is_fixed_scale=True)

            minuteHR = self.data['annotations']['minuteHR']
            self.update_individual_plot_display(graph,
                                                [t for x, t in minuteHR if x is not None],
                                                [x for x, t in minuteHR if x is not None],
                                                tStart, tEnd, line_name='minute')

            # if ('baseline' in self.data['annotations'] and len(self.data['annotations']['baseline']) > 0):
            #     self.update_individual_plot_display(self.allGraphs['baseline'],
            #                                         posMin, self.data['annotations']['baseline'][idxStart:idxEnd],
            #                                         tStart, tEnd, line_name='baseline')


            if 'variability' in self.data['annotations'] and 'varSeg' in self.data['annotations']:
                #print 'updating varSeg', tStart, tEnd
                self.update_individual_plot_display(self.allGraphs['variability'],
                                                    [t for t, v in self.data['annotations']['varSeg']],
                                                    [v for t, v in self.data['annotations']['varSeg']],
                                                    tStart, tEnd, is_fixed_scale=True)
                self.allGraphs['variability'].update_x_scale(tStart, tEnd)   # hack for bug in simple_graph

            graph = self.allGraphs['artifacts']
            self.plot_show_decel_annotations(graph)
            graph.update_x_scale(tStart, tEnd)
            self.update_ticks(graph, tStart, tEnd)

        return


    def revise_combined_view(self):
        if self.allGraphs == {}:
            #print 'calling create_combined_view_plots'
            self.create_combined_view_plots()

        #print 'called revise_combined_view'

        if self.data['fhr_source'] is None:
            self.allGraphs['hr'].opacity = 0
            self.allGraphs['valid'].opacity = 0
        elif not self.data['combined']:
            # Data not yet available
            pass
        elif not self.plots_should_update(update_on_hr=True):
            # already current
            pass
        else:
            pos = self.data['combined']['pos']
            posMin = self.convertTimescaleToMin(pos)
            tStart, tEnd = self.compute_time_limits(posMin)
            idxStart, idxEnd = self.findIndexLimits(posMin, tStart, tEnd)

            if idxStart is not None:
                posMin = posMin[idxStart:idxEnd]
                self.update_individual_plot_display(self.allGraphs['hr'],
                                                    posMin, self.data['combined']['hr'][idxStart:idxEnd],
                                                    tStart, tEnd,is_fixed_scale=True, remove_zero_values=True)

                if ('annotations' in self.data  and 'fastBaseline' in self.data['annotations']
                        and len(self.data['annotations']['fastBaseline']) > 0):
                    self.update_individual_plot_display(self.allGraphs['hr'],
                                                        posMin, self.data['annotations']['baseline'][idxStart:idxEnd],
                                                        tStart, tEnd, line_name='baseline')
                    self.update_individual_plot_display(self.allGraphs['hr'],
                                                        posMin, np.array(self.data['annotations']['baseline'][idxStart:idxEnd])+15.0,
                                                        tStart, tEnd, line_name='baseline+15')
                    self.update_individual_plot_display(self.allGraphs['hr'],
                                                        posMin, np.array(self.data['annotations']['baseline'][idxStart:idxEnd])-15.0,
                                                        tStart, tEnd, line_name='baseline-15')
                self.plot_show_decel_annotations(self.allGraphs['hr'], offset=190)

                self.update_individual_plot_display(self.allGraphs['valid'],
                                                    posMin, self.data['combined']['valid'][idxStart:idxEnd],
                                                    tStart, tEnd, is_fixed_scale=True)

        if self.data['uc_source'] is None and self.data['uc_ann'] is None:
            self.allGraphs['uc'].opacity = 0
        elif not self.plots_should_update(update_on_uc=True):
            # already current
            pass
        elif self.data['uc_source'] is None:
            # Plotting annotations only

            if 'combined' in self.data and 'pos' in self.data['combined'] and len(self.data['combined']['pos']) >= 2:
                pos = self.data['combined']['pos']
                posMin = self.convertTimescaleToMin(pos)
                tStart, tEnd = self.compute_time_limits(posMin)

                graph = self.allGraphs['uc']
                self.plot_show_manual_uc_annotations(graph)
                self.plot_update_limits(graph, tStart, tEnd, ymin=0, ymax=1)

        elif not self.data['uc']:
            # data not yet available
            pass
        elif not self.plots_should_update(update_on_uc=True):
            # already current
            pass
        else:
            posMin = self.data['uc']['posMin']
            tStart, tEnd = self.compute_time_limits(posMin)
            idxStart, idxEnd = self.findIndexLimits(posMin, tStart, tEnd)

            if idxStart is not None:
                posMin = posMin[idxStart:idxEnd]

                self.update_individual_plot_display(self.allGraphs['uc'],
                                                    posMin, self.data['uc']['uc'][idxStart:idxEnd],
                                                    tStart, tEnd)

            if self.data['uc_ann'] is not None and len(self.data['uc_ann']) > 0:
                self.plot_show_manual_uc_annotations(self.allGraphs['uc'])
            else:
                self.plot_show_uc_timing(self.allGraphs['uc'])


    def revise_fhr_detail_view(self):
        if self.data['fhr_source'] is None:
            return

        if not self.plots_should_update(update_on_hr=True):
            return

        if self.allGraphs == {}:
            self.create_fhr_detail_view_plots()

        for group in ['envelope', 'pitch']:
            if not self.data[group]:
                continue

            pos = self.data[group]['pos']
            posMin = self.convertTimescaleToMin(pos)
            tStart, tEnd = self.compute_time_limits(posMin)
            idxStart, idxEnd = self.findIndexLimits(posMin, tStart, tEnd)

            if idxStart is None:
                continue

            posMin = posMin[idxStart:idxEnd]
            plot_name = '{}_fhr'.format(group)
            self.update_individual_plot_display(self.allGraphs[plot_name],
                                                posMin, self.data[group]['raw'][idxStart:idxEnd],
                                                tStart, tEnd,is_fixed_scale=True)
            plot_name = '{}_valid'.format(group)
            self.update_individual_plot_display(self.allGraphs[plot_name],
                                                posMin, self.data[group]['valid'][idxStart:idxEnd],
                                                tStart, tEnd, is_fixed_scale=True)
            plot_name = '{}_corr'.format(group)
            self.update_individual_plot_display(self.allGraphs[plot_name],
                                                posMin, self.data[group]['cor'][idxStart:idxEnd],
                                                tStart, tEnd, is_fixed_scale=True)


    def revise_uc_detail_view(self):
        if self.data['uc_source'] is None or not self.data['uc']:
            return

        if not self.plots_should_update(update_on_uc=True):
            return

        if self.allGraphs == {}:
            self.create_uc_detail_viewplots()

        posMin = self.data['uc']['posMin']
        tStart, tEnd = self.compute_time_limits(posMin)
        idxStart, idxEnd = self.findIndexLimits(posMin, tStart, tEnd)

        if idxStart is  None:
            return

        posMin = posMin[idxStart:idxEnd]
        self.update_individual_plot_display(self.allGraphs['uc_raw'],
                                            posMin, self.data['uc']['raw'][idxStart:idxEnd],
                                            tStart, tEnd)

        self.update_individual_plot_display(self.allGraphs['uc_filtered'],
                                            posMin, self.data['uc']['filtered'][idxStart:idxEnd],
                                            tStart, tEnd)

        self.update_individual_plot_display(self.allGraphs['uc_extract'],
                                            posMin, self.data['uc']['uc'][idxStart:idxEnd],
                                            tStart, tEnd)
        self.plot_show_manual_uc_annotations(self.allGraphs['uc_extract'])


    #
    # Plotting State Management Routines
    #

    def show_plot_state(self):
        print 'last_plot_state:', self.last_plot_state
        print 'current_plot_state:', self.current_plot_state


    def plot_is_current(self):
        ret = self.last_plot_state == self.current_plot_state
        #print 'plot_is_current returned', ret
        return ret


    def reset_plot_state(self):
        self.current_plot_state['hr_updated'] = False
        self.current_plot_state['uc_updated'] = False
        self.current_plot_state['assessment_updated'] = False
        self.last_plot_state = copy.deepcopy(self.current_plot_state)


    def plots_should_update(self, update_on_hr=False, update_on_uc=False):
        if self.current_plot_state['view'] != self.last_plot_state['view']:
            return True
        if self.current_plot_state['scale'] != self.last_plot_state['scale']:
            return True
        if (self.current_plot_state['scale'] == 'pan_zoom'
            and self.current_plot_state['scale_limits'] != self.last_plot_state['scale_limits']):
            return True

        ret = (self.current_plot_state['hr_updated'] and update_on_hr
               or  self.current_plot_state['uc_updated'] and update_on_uc)
        #print 'plots_should_update returns', ret
        return ret


    def plot_view_changed(self):
        ret = self.current_plot_state['view'] != self.last_plot_state['view']
        #print 'plot_view_changed returns', ret
        return ret


    #
    # Plotting Helper Routines
    #


    def plot_show_decel_annotations(self, graph, offset=None, lw=8):
        global ARTIFACT_RENDERING
        graph.remove_segment_annotations()
        if 'decels' in self.data['annotations']:
            for decel in self.data['annotations']['decels']:
                if decel['classification'] in ARTIFACT_RENDERING:
                    color = ARTIFACT_RENDERING[decel['classification']]['color']
                    if offset is None:
                        row = ARTIFACT_RENDERING[decel['classification']]['row']
                        ypos = row/float(ARTIFACT_MAX_ROWS+1)
                    else:
                        ypos = offset
                    graph.add_segment_annotation(ypos, decel['tStart'], decel['tEnd'],
                                                 color=color, line_width=lw)


    def plot_update_limits(self, graph, tStart, tEnd, ymin=0, ymax=1):
        graph.update_x_scale(tStart, tEnd)
        graph.update_y_scale(ymin, ymax)


    def plot_show_manual_uc_annotations(self, graph):
        global UC_RENDERING
        if self.data['uc_ann'] is None:
            return
        graph.remove_vertical_annotations()
        for ann in self.data['uc_ann']:
            print ann
            ann_type = ann['annotation']
            color = UC_RENDERING[ann_type]['color']
            lw = UC_RENDERING[ann_type]['lw']
            ann_time = ann['time']/60.0
            print ann_type, color, ann_time
            graph.add_vertical_annotations(ann_time, color=COLORS[color], line_width=lw)


    def plot_show_uc_timing(self, graph):
        global UC_TIMING_RENDERING
        graph.remove_vertical_annotations()
        if 'annotations' not in self.data or 'annotatedUC' not in self.data['annotations']:
            return

        for entry in self.data['annotations']['annotatedUC']:
            color = UC_TIMING_RENDERING['uc']['color']
            line_width = UC_TIMING_RENDERING['uc']['lw']
            t = float(entry['tAcme'])
            graph.add_vertical_annotations(t, color=COLORS[color], line_width=line_width)

            if entry['decel'] is not None:
                t = float(entry['decel']['tNadir'])
                color = UC_TIMING_RENDERING['decel']['color']
                line_width = UC_TIMING_RENDERING['decel']['lw']
                graph.add_vertical_annotations(t, color=COLORS[color], line_width=line_width)


    def compute_time_limits(self, posMin):
        if len(posMin) == 0:
            return None, None

        # compute plot timespan
        tEnd = math.ceil(posMin[-1])
        if self.current_plot_state['scale'] == 'full':
            tStart = math.floor(posMin[0])
        elif self.current_plot_state['scale'] == 'recent':
            tStart = max(0, tEnd - self.plot_duration_recent)
        elif self.current_plot_state['scale'] == 'pan_zoom':
            if self.current_plot_state['scale_limits'] is not None:
                tStart, tEnd = self.current_plot_state['scale_limits']
            else:
                tStart = math.floor(posMin[0])
                self.current_plot_state['scale_limits'] = [tStart, tEnd]

        #print 'compute_time_limits', tStart, tEnd
        return tStart, tEnd


    def update_scale_limits(self, val, widthMin=1.0, zoomFactor=1.5, panFactor=0.5):
        assert val in ['left', 'right', 'zoom_in', 'zoom_out']

        if self.data['fhr_source'] is not None:
            if ('combined' not in self.data or 'pos' not in self.data['combined']
                    or len(self.data['combined']['pos']) < 2):
                return
            pos = self.data['combined']['pos']
        elif self.data['uc_source'] is not None:
            if ('uc' not in self.data or 'pos' not in self.data['uc']
                    or len(self.data['uc']['pos']) < 2):
                return
            pos = self.data['uc']['pos']

        posMin = self.convertTimescaleToMin(pos)
        tMax = math.ceil(posMin[-1])
        tMin = math.floor(posMin[0])
        widthMax = tMax -tMin
        if self.current_plot_state['scale_limits'] is None:
            self.current_plot_state['scale_limits'] = [tMin, tMax]

        tStart, tEnd = self.current_plot_state['scale_limits']
        width = tEnd - tStart
        tMid = (tEnd + tStart)/2.0

        if val =='left':
            newStart = math.floor(tStart - panFactor * width)
            newStart = max(newStart, tMin)
            newEnd = newStart + width
        elif val =='right':
            newEnd = math.ceil(tEnd + panFactor * width)
            newEnd = min(newEnd, tMax)
            newStart = newEnd - width
        elif val == 'zoom_in':
            newWidth = max(width/zoomFactor, widthMin)
            newStart = math.floor(tMid-newWidth/2.0)
            newEnd = math.ceil(tMid+newWidth/2.0)
        elif val =='zoom_out':
            newWidth = min(width*zoomFactor, widthMax)
            if newWidth == widthMax:
                newStart = tMin
                newEnd = tMax
            else:
                newStart = math.floor(tMid-newWidth/2.0)
                newEnd = math.ceil(tMid+newWidth/2.0)

                if newStart < tMin:
                    newStart = tMin
                    newEnd = math.ceil(newStart + newWidth)
                    newEnd = min(newEnd, tMax)
                elif newEnd > tMax:
                    newEnd = tMax
                    newStart = math.floor(newEnd - newWidth)
                    newStart = max(newStart, tMin)
        else:
            print 'unknown update_scale_limits op:', val

        self.current_plot_state['scale_limits'] = [newStart, newEnd]
        #print 'new scale_limits', val, newStart, newEnd


    def convertTimescaleToMin(self, pos):
        """Converts timescale in seconds to minutes"""
        return [x/60.0 for x in pos]


    def shiftTimescale(self, pos, delta):
        """Adds offset to timescale"""
        return [x+delta for x in pos]


    def findIndexLimits(self, pos, tStart, tEnd):
        """Compute index range where timescale within time limits"""
        if len(pos) == 0 or tStart is None or tEnd is None:
            return None, None

        if pos[-1] < tStart or pos[0] > tEnd:
            return None, None

        idxStart = 0
        while pos[idxStart] < tStart:
            idxStart += 1

        idxEnd = len(pos)
        while pos[idxEnd-1] > tEnd:
            idxEnd -= 1

        return idxStart, idxEnd


    def update_individual_plot_display(self, graph, pos, val, tStart, tEnd,
                                       is_zero_based=False, is_fixed_height=False, is_fixed_scale=False,
                                       remove_zero_values=False, line_name=None,
                                       maxPoints=2000):
        if len(pos) == 0 or len(val) == 0:
            return

        # align lengths
        if len(pos) != len(val):
            N = min(len(pos), len(val))
            pos = pos[:N]
            val = val[:N]

        # convert from numpy to list format, if needed, to keep graph package happy
        if isinstance(pos, np.ndarray):
            pos = pos.tolist()
        if isinstance(val, np.ndarray):
            val = val.tolist()

        points = zip(pos, val)

        # downsample, if needed, to0 keep within total points limit
        if len(pos) > maxPoints:
            stride = int(math.ceil(float(len(pos)) / maxPoints))
            points = points[::stride]

        # interpolate missing data (interpolation happens at plotting time)
        if remove_zero_values:
            points = [x for x in points if x[1] != 0]


        if line_name is None or line_name == 'default':
            #graph.add_points(points, tEnd)
            graph.update_x_scale(tStart, tEnd)
            graph.add_points(points, False)

            # if primary plot line, then adjust Y and X axis span accordingly
            #graph.update_x_scale(tStart, tEnd)
            # graph.xmax = tEnd
            # graph.xmin = tStart
            # graph.update_horizontal_annotations()

            if is_fixed_scale:
                pass
            elif is_fixed_height:
                graph.ymax = 1
                graph.ymin = 0
            elif is_zero_based:
                ylim = float(np.max(val))
                graph.ymax = ylim
                graph.ymin = 0
            else:
                ylimH = float(min(np.max(val), np.percentile(val, 98)*1.1))
                ylimL = float(max(np.min(val), np.percentile(val, 2) * 1.1))
                #ylimL = float(np.min(val))
                graph.ymax = ylimH
                graph.ymin = ylimL
        else:
            # additional plot line
            graph.add_points({line_name:points}, tEnd, update_xmax=False)

        self.update_ticks(graph, tStart, tEnd)


    def update_ticks(self, graph, tStart, tEnd):

        actual_duation = tEnd - tStart

        if actual_duation <= 10:
            graph.x_ticks_minor = 3
            graph.x_ticks_major = 1
        elif actual_duation <= 20:
            graph.x_ticks_minor = 1
            graph.x_ticks_major = 1
        elif actual_duation <= 60:
            graph.x_ticks_minor = 5
            graph.x_ticks_major = 5
        elif actual_duation > 60:
            graph.x_ticks_minor = 2
            graph.x_ticks_major = 10
