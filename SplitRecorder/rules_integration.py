
# coding: utf-8


import copy
from pprint import pprint
from libRules import RulesEngine

from rules_constants import *
import rules_config
import ruleset_cm
import ruleset_ia
from rules_message_digest import ALL_DIAGNOSTIC_MESSAGES


EPISODIC_MAP = {
    'variable': VARIABLE_DECELERATION,
    'acceleration':  ACCELERATION,
}

PERIODIC_MAP = {
    'variable_periodic': PERIODIC_VARIABLE_DECELERATION,
    'late_decel': LATE_DECELERATION,
    'early_decel':  EARLY_DECELERATION,
}



class Decision:
    def __init__(self, verbose=False, ruleset='cm'):
        assert ruleset in ['cm', 'ia']
        self.refEngine = RulesEngine(rules_config.rulesEngineConfig, verbose=verbose)
        if ruleset == 'cm':
            self.refEngine.injestRuleset(ruleset_cm)
        elif ruleset == 'ia':
            self.refEngine.injestRuleset(ruleset_ia)
        
    def executeRules(self, extractorResults, allUC, tEnd, tStart=0, verbose=False):
        self.rulesEngine = copy.deepcopy(self.refEngine)
        self.addMeasurements(extractorResults, allUC, tEnd, tStart=tStart)

        #rulesEngine.verbose = True
        status, rules_log = self.rulesEngine.applyAllRules(tEnd)
        status['recommendations'] = self.computeRecommendations(status)

        status['injest_log'] = None         # ignore for now
        if verbose:
            print
            pprint(status)
        return status


    def computeRecommendations(self, status):

        known = []
        recommendations = []
        if FETUS in status['current_diagnosis']:
            unsorted_reecommendations = []
            for diag in status['current_diagnosis'][FETUS]:
                if diag not in known and diag in ALL_DIAGNOSTIC_MESSAGES:
                    unsorted_reecommendations.append(ALL_DIAGNOSTIC_MESSAGES[diag])
                    known.append(diag)
            recommendations = [x['text'] for x in sorted(unsorted_reecommendations, key=lambda x:-x['order'])]

        unsorted_reecommendations = []
        for entity, allDiag in status['current_diagnosis'].items():
            if entity == FETUS:
                continue
            for diag in allDiag:
                if diag not in known and diag in ALL_DIAGNOSTIC_MESSAGES:
                    unsorted_reecommendations.append(ALL_DIAGNOSTIC_MESSAGES[diag])
                    known.append(diag)
        recommendations = recommendations + [x['text'] for x in sorted(unsorted_reecommendations, key=lambda x:-x['order'])]
        return recommendations

    
    def addMeasurements(self, extractorResults, allUC, tEnd, tStart=0):
        tStart = round(tStart * 100)/100.0
        self.rulesEngine.updateMeasurement(RECORDING_DURATION, tStart, tStart)
        time = round(tEnd * 100)/100.0 
        self.rulesEngine.updateMeasurement(RECORDING_DURATION, time, time)

        for entry in extractorResults['minuteHR']:
            if entry is not None and None not in entry:
                hr = int(round(entry[0]))
                time = round(entry[1] * 100)/100.0
                self.rulesEngine.updateMeasurement(FETAL_HEART_RATE_MINUTE, hr, time)

        for entry in extractorResults['basalHR']:
            if entry is not None and None not in entry:
                hr = int(round(entry[0]))
                time = round(entry[1] * 100)/100.0
                self.rulesEngine.updateMeasurement(FETAL_HEART_RATE, hr, time)

        for entry in extractorResults['varSeg']: 
            if entry is not None and None not in entry:
                var = int(round(entry[1]))
                time = round(entry[0] * 100)/100.0 
                self.rulesEngine.updateMeasurement(FHR_VARIABILITY, var, time)        
    
        for entry in extractorResults['decels']:
            classification = entry['classification']
            if classification =='prolonged':
                if entry['duration'] < 5*50:
                    val = PROLONGED_DECELERATION
                else:
                    mag = round(entry['mag'])
                    if mag <= 80:
                        val = LONGER_MARKED_PROLONGED_DECELERATION
                    else:
                        val = LONGER_PROLONGED_DECELERATION
            elif classification in EPISODIC_MAP:
                val = EPISODIC_MAP[classification]
            else:
                continue

            time = round(entry['tNadir'] * 100)/100.0 
            self.rulesEngine.updateMeasurement(EPISODIC_FHR_PATTERNS, val, time)

        for entry in extractorResults['annotatedUC']:
            #pprint(entry)
            if entry['decel'] is None:
                time = round(entry['tAcme'] * 100)/100.0 
                self.rulesEngine.updateMeasurement(PERIODIC_PATTERNS, STANDALONE_CONTRACTION, time)
            else:
                entry = entry['decel']
                classification = entry['classification']
                if classification in PERIODIC_MAP:
                    val = PERIODIC_MAP[classification]
                    time = round(entry['tNadir'] * 100)/100.0
                    self.rulesEngine.updateMeasurement(PERIODIC_PATTERNS, val, time)
     
        #self.rulesEngine.verbose = True
        if allUC is not None:
            for time in allUC:
                time = round(time * 100)/100.0
                self.rulesEngine.updateMeasurement(CONTRACTIONS, CONTRACTION, time)
        #self.rulesEngine.verbose = False
    
    
