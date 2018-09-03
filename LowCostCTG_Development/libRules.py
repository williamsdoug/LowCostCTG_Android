#
#  Copyright Douglas Williams, 2017
#  All Rights Reserved
#

from rules_constants import *
import operator
from pprint import pprint
import collections
import copy

class RulesEngine:
    def __init__(self, config, researchMode=False, verbose=False):
        self.researchMode = researchMode
        self._allRules = {}

        self.lastTime = None
        self.currentTime = None
        self.verbose=verbose
        self.rules_log=[]          # used for tracking rules firing
                                   # TO DO:  treat as reformatting of structured log datya below
        # Structured Log
        self.injest_log = []
        self.firings_log = []

        if 'measurement_to_assessment' in config:
            self.measurement_to_assessment = config['measurement_to_assessment']
        else:
            self.measurement_to_assessment = {}

        if 'assessment_to_measurement' in config:
            self.assessment_to_measurement = config['assessment_to_measurement']
        else:
            self.assessment_to_measurement = {}


        # Register and initialize patient assessment for each tracked
        # entity: FETUS, MOTHER, LABOR)
        self.assessmentEntities = config['assessmentEntities']
        self.evaluationOrdering = config['evaluationOrdering']
        self.allEntities = config['assessmentEntities'].keys()
        self.lastAssessment = dict([(k, None)
                                    for k in self.allEntities])
        self.currentAssessment = dict([(k, None)
                                    for k in self.allEntities])

        self.proposedAssessment = collections.defaultdict(list)

        # Note:  These may be dupicates of above
        self.prior_resolved_entities = {}
        self.resolved_entities = {}

        # new fields associated with assessment, diagnosis, actions ...
        self.sticky_assessments = {}
        self.sticky_diagnosis = {}
        self.sticky_actions = {}
        self.sticky_reminders = {}
        self.current_reminders = {}
        self.current_diagnosis = {}
        self.current_actions = {}
        self.measurement_last_update = {}

        self.alarmLevel = None
        self.alarmToPriority = config['alarmToPriority']
        self.reminderDuration = None

        self.requestedMeasurements = []
        self.map_condition_to_measurement = {}
        assert 'measurements' in config
        self.measurements = dict([[m['name'], Measurement(self, **m)]
                                  for m in config['measurements']])


    def injestRuleset(self, rulesNamespace):
        """Loads rules from namespace, and partitions into confition rules
        and action rules based on prefix"""
        for entry in self.evaluationOrdering:
            if entry['type'] == 'rules':
                # print 'name: {}  prefix: {}'.format(entry['name'], entry['prefix'])
                if entry['name'] in self._allRules:
                    print 'Duplicate rules evaluation entry name:', entry['name']
                assert entry['name'] not in self._allRules
                self._allRules[entry['name']] = self._getRules(rulesNamespace, prefix=entry['prefix'])


    @staticmethod
    def _getRules(namespace, prefix=''):
        """Extract rules from namespace"""
        names = sorted([x for x in dir(namespace) if x.startswith(prefix)])
        return [getattr(namespace, nam) for nam in names]


    def applyAllRules(self, newTime=None):
        """Applies an iternation of ruleset for current timeslot
        Sequence:
            - Perform per-cycle initialization
            - Apply all rules related to patient assessment
            - Resolve patient assessment
            - Apply all rules related to actions
        """

        if newTime is not None:
            self.updateTimeclock(newTime)
        self.proposedAssessment = collections.defaultdict(list)
        self.proposedAction = []
        self.requestedMeasurements = []

        self.prior_resolved_entities = self.resolved_entities
        self.resolved_entities = {}

        self.current_reminders = {}
        self.current_diagnosis = {}
        self.current_actions = {}


        for entry in self.evaluationOrdering:
            if entry['type'] == 'rules':
                # print 'rules name: {}'.format(entry['name'])
                self._applyRules(self._allRules[entry['name']])

            elif entry['type'] == 'resolve':
                # print 'resolve entities: {}'.format(entry['entities'])
                for entity in entry['entities']:
                    if entity not in self.allEntities:
                        print 'missing entity:', entity
                        pprint(self.allEntities)
                    assert  entity in self.allEntities
                    self._resolveAssessment(entity)

                    #print 'resolution', entity, self.getAssessment(entity)
                    self.resolved_entities[entity] = self.getAssessment(entity)
                #pprint(self.resolved_entities)
            elif entry['type'] == 'combine':
                if self.verbose:
                    print 'Combine:', entry
                self._combine_assessments(entry['target'], entry['source'])
                self._resolveAssessment(entry['target'])
            else:
                raise Exception('Unknown evaluationOrdering type {}'.format(entry['type']))

        if self.verbose:
            print
            print '{}:  Patient Assessment:'.format(self.currentTime)
            pprint(self.currentAssessment)
            print 'Alarm: {}  Reminder: {}'.format(self.alarmLevel, self.reminderDuration)
            print

        injest_log = self.injest_log
        firings_log = self.firings_log
        rules_log = self.rules_log
        self.injest_log = []
        self.firings_log = []
        self.rules_log = []


        self.analyzeReminders()

        return ({'assessment':copy.deepcopy(self.currentAssessment),
                 'alarmLevel':self.alarmLevel,
                 'reminderDuration':self.reminderDuration,
                 'currentTime':self.currentTime,
                 'injest_log':injest_log,
                 'firings_log':firings_log,
                 'current_reminders':copy.copy(self.current_reminders),
                 'current_diagnosis':copy.copy(self.current_diagnosis),
                 'current_actions':copy.copy(self.current_actions),
                 },
                rules_log)


    # Used primarily to update OVERALL timestamp
    def updateMeasurementTimestamp(self, entity, timestamp):
        self.measurement_last_update[entity] = timestamp


    def analyzeReminders(self, verbose=False):
        current_reminders = copy.copy(self.current_reminders)
        measurement_last_update = copy.copy(self.measurement_last_update)

        time_remaining = {}
        for entity, reminder in current_reminders.items():
            if entity in self.assessment_to_measurement:
                meas_name = self.assessment_to_measurement[entity]
            else:
                # Code primarily for the OVERALL reminder
                meas_name = entity


            if meas_name in measurement_last_update:
                last_update = measurement_last_update[meas_name]
            else:
                last_update = -365*24*60   # large negative number, currently 1 year

            time_since_last_update = self.currentTime - last_update
            time_remaining[entity] = reminder - time_since_last_update

        if verbose:
            print
            print '** analyzeReminders **'
            print 'current_reminders:',
            pprint(current_reminders)
            print 'measurement_last_update:',
            pprint(measurement_last_update)
            print 'time_remaining:',
            print(time_remaining)
            print

        return time_remaining



    def updateTimeclock(self, newTime):
        """Advances timeclock"""
        assert(newTime is not None)
        self.lastTime = self.currentTime
        self.currentTime = newTime

    def generateTextLog(self):
        result = []

        for entry in self.injest_log:
            # entry = {'type': observationType, 'value': value, 'time': self.currentTime}
            if isinstance(entry['value'], str):
                txt = '{}: {} @ {:0.1f}'.format(entry['type'], entry['value'], entry['time'])
            else:
                txt = '{}:  {:0.1f} @ {:0.1f}'.format(entry['type'], entry['value'], entry['time'])
            #self.rules_log.append(txt)

            if 'classification' in entry:
                txt +=  ' [{})'.format(entry['classification'])
                #self.rules_log.append(txt)
            if 'inHistory' in entry:
                txt +=  '  ({} in history)'.format(entry['inHistory'])
                #self.rules_log.append(txt)

            self.rules_log.append(txt)

        for rule in self.firings_log:
            result.append('Rule: {}'.format(rule))


    def _applyRules(self, ruleset):
        """Applies a specific set of rules"""
        for fun in ruleset:
            if self.verbose:
                print
                print 'applying rule: {}'.format(fun.__name__)
            ret = fun(self)
            if ret:
                if self.verbose:
                    #print 'applying rule: {}'.format(fun.__name__)
                    print 'rule fired'
                self.rules_log.append('Rule: {}'.format(fun.__name__))
                self.firings_log.append(fun.__name__)


    def getAssessment(self, entity):
        if entity not in self.currentAssessment:
            raise Exception('Invalid entity for getAssessment -- {}'.format(entity))
        return self.currentAssessment[entity]


    def hasAssessment(self, entity, assessment):
        currentAssessment = self.getAssessment(entity)
        if assessment not in self.assessmentEntities[entity]['values']:
            raise Exception("Unknown assessment: {} for {}".format(
                assessment , entity))
        return currentAssessment == assessment


    def _resolveAssessment(self, entity):
        """Arbitrates proposed assessments based on predefined precedence"""

        self.lastAssessment[entity] = self.currentAssessment[entity]
        priorityEntry, similarEntries = self._getHighestProposedAssessment(entity)

        # get descriptinos of possible assessments for this entity
        priority = self.assessmentEntities[entity]['values']

        usedSticky = False
        if entity in self.sticky_assessments:
            if priorityEntry is None:
                # Use sticky assessment
                assessment = self.sticky_assessments[entity]
                similarEntries = [] # ignore any other assessments
                usedSticky = True
            else:
                currentAssessment = priorityEntry['assessment']
                if priority[self.sticky_assessments[entity]] > priority[currentAssessment]:
                    # Use sticky assessment
                    assessment = self.sticky_assessments[entity]
                    similarEntries = [] # ignore any other assessments
                    usedSticky = True
                elif priority[self.sticky_assessments[entity]] == priority[currentAssessment]:
                    # sticky assessment is at same priority as current assessment
                    assessment = self.sticky_assessments[entity]
                    usedSticky = True
                else:
                    # current priority is at higher priority than sticy assessment
                    assessment = currentAssessment
        elif priorityEntry:
            assessment = priorityEntry['assessment']
        else:
            assessment = self.assessmentEntities[entity]['default']
            similarEntries = []
        self.currentAssessment[entity] = assessment

        # Process stickiness
        # Issue: Use of both entity and entry names is very confusing and error prone
        # TODO: remane entry to something less confusing
        for entry in similarEntries:
            if not entry['isSticky']:
                continue

            # see if assessment differs from prior sticky assessment
            # if so, reinitialize sticky entries

            # print 'entity: {}'.format(entity)
            # print 'entry:',
            # pprint(entry)
            # print 'sticky_assessments:'
            # pprint(self.sticky_assessments)

            if entity not in self.sticky_assessments or assessment != self.sticky_assessments[entity]:
                self.sticky_assessments[entity] = assessment
                self.sticky_diagnosis[entity] = []
                self.sticky_actions[entity] = []
                self.sticky_reminders[entity] = None
                if ('reminders' in self.assessmentEntities[entity]
                    and assessment in self.assessmentEntities[entity]['reminders']):
                    self.sticky_reminders[entity] = self.assessmentEntities[entity]['reminders'][assessment]

            if 'reminder' in entry:
                if self.sticky_reminders[entity]:
                    self.sticky_reminders[entity] = min(self.sticky_reminders[entity], entry['reminder'])
                else:
                    self.sticky_reminders[entity] = entry['reminder']

            for d in entry['diagnosis']:
                if d not in self.sticky_diagnosis[entity]:
                    self.sticky_diagnosis[entity].append(d)

            for a in entry['actions']:
                # print 'actions:', a, 'entity:', entity
                # print 'sticky_actions:'
                # pprint(self.sticky_actions)
                # print 'self.sticky_actions[entity]'
                # pprint(self.sticky_actions[entity])
                if a not in self.sticky_actions[entity]:
                    self.sticky_actions[entity].append(a)

        if usedSticky:
            reminder = self.sticky_reminders[entity]
            diagnosis = copy.copy(self.sticky_diagnosis[entity])
            actions = copy.copy(self.sticky_actions[entity])
        else:

            reminder = None
            if ('reminders' in self.assessmentEntities[entity] and self.assessmentEntities[entity]['reminders']
                and assessment in self.assessmentEntities[entity]['reminders']):
                reminder = self.assessmentEntities[entity]['reminders'][assessment]
            actions = []
            diagnosis = []

        # Resolve new stickiness, actions and diagnosis

        for entry in similarEntries:
            if entry['isSticky']:
                continue
            if not entry['isSticky']:
                pass
            for d in entry['diagnosis']:
                if d not in diagnosis:
                    diagnosis.append(d)
            for a in entry['actions']:
                if a not in actions:
                    actions.append(a)

        if reminder:
            self.current_reminders[entity] = reminder
        if diagnosis:
            self.current_diagnosis[entity] = diagnosis
        if actions:
            self.current_actions[entity] = actions


    def _getHighestProposedAssessment(self, entity):
        if len(self.proposedAssessment[entity]) > 0:
            priorityEntry = sorted(self.proposedAssessment[entity], key=operator.itemgetter('priority'))[-1]
            similarEntries = [entry for entry in self.proposedAssessment[entity]
                              if entry['assessment'] == priorityEntry['assessment']]
            return priorityEntry, similarEntries
        else:
            return None, []


    def hasProposedAssessment(self, entity, potentialAssessment):
        """Used to filter rules, by determining whether patient already 
        recommended for proposed state"""
        return not self.isNotYetProposed(entity, potentialAssessment)


    def isNotYetProposed(self, entity, potentialAssessment):
        """Helper function for isAlreadyProposed"""
        if entity not in self.allEntities:
            raise Exception("Unknown entity: {}".format(entity))

        if potentialAssessment not in self.assessmentEntities[entity]['values']:
            raise Exception("Unknown assessment: {} for {}".format(
                potentialAssessment, entity))

        if self.researchMode:  # Support more permissive rules firings
            return False
        priorityEntry, _ = self._getHighestProposedAssessment(entity)

        if priorityEntry:
            potentialPriority = self.assessmentEntities[entity]['values'][potentialAssessment]
            currentProposedPriority = priorityEntry['priority']

            return potentialPriority > currentProposedPriority
        else:
            return True


    def proposeAssessment(self, entity, assessment, reminder=None,
                          diagnosis=[], actions=[], sticky=False):
        """Adds proposed assessment to queue"""
        if isinstance(entity, list):
            entities = entity
        else:
            entities = [entity]

        for entity in entities:
            if self.verbose:
                print '{}:  Proposing assessment {}'.format(entity, assessment)
            if entity not in self.allEntities:
                raise Exception("Unknown entity: {}".format(entity))

            if assessment not in self.assessmentEntities[entity]['values']:
                raise Exception("Unknown assessment: {} for {}".format(
                    assessment , entity))
            if entity in self.resolved_entities:
                print '** Proposing assessment after resolution', entity

            if reminder is None:
                if ('reminder' in self.assessmentEntities[entity] and
                        assessment in self.assessmentEntities[entity]['reminders']):
                    reminder = self.assessmentEntities[entity]['reminders'][assessment]

            self.proposedAssessment[entity].append(
                {'assessment': assessment,
                 'priority': self.assessmentEntities[entity]['values'][assessment],
                 'diagnosis':diagnosis,
                 'actions':actions,
                 'isSticky':sticky,
                 'reminder':reminder
                 })


    def _combine_assessments(self, target_entity, source_entities):
        """Produces new assessment by combining multiple component assessments """
        for entity in source_entities:
            proposed = self.getAssessment(entity)
            # print target_entity, ': applying assessment ', proposed, 'from', entity
            if proposed is not None:
                self.proposeAssessment(target_entity, proposed)

    def setAlarm(self, alarmLevel):
        """Used by action rules"""
        # note:  currently no conflict resolution.
        # self.alarmToPriority  available for future use
        self.alarmLevel = alarmLevel


    def setReminder(self, duration):
        """Used by action rules"""
        # note:  currently no conflict resolution
        # Any future conflict resolution use use smallest duration
        self.reminderDuration = duration

    #
    # Measurement related methods
    #

    def updateMeasurement(self, observationType, value, time=None):
        """Add new measurement to the appropriate measurement queue"""
        if time is None:
            time = self.currentTime


        entry = {'type': observationType, 'value': value, 'time': time}
        if isinstance(value, str):
            txt = '{}: {} @ {:0.1f}'.format(observationType, value, time)
        else:
            txt = '{}: {:0.1f} @ {:0.1f}'.format(observationType, value, time)

        self.rules_log.append(txt)
        self.injest_log.append(entry)

        meas = self.measurements[observationType]
        meas.addMeasurement(value, time)
        self.measurement_last_update[observationType] = time

        if self.verbose:
            print
            print 'measurement_last_update:', txt
            pprint(self.measurement_last_update)


    def getLastMeasurement(self, observationType):
        """Add new measurement to the appropriate measurement queue"""
        #print 'getLastMeasurement', observationType, observationType in self.measurements
        meas = self.measurements[observationType]
        return meas.getMeasurement()

    def getMeasurementTimestamp(self, observationType, getOldest=False):
        meas = self.measurements[observationType]
        return meas.getMeasurementTimestamp(getOldest=getOldest)


    def presenting(self, conditions):
        """Determine in condition is present either for latest measurement or
        in history, depending on specified condition"""
        if self.verbose:
            print '  Calling presenting:', conditions
        if not isinstance(conditions, list): # convert to list format if needed
            conditions = [conditions]

        for cond in conditions:
            if cond not in self.map_condition_to_measurement:
                raise Exception('Unknown condition: {}'.format(cond))

            entry = self.map_condition_to_measurement[cond]
            ret = entry['meas'].testAssessment(cond, entry['isHistory'])
            if self.verbose:
                print '    testing condition {}  returned {}'.format(cond, ret)
            if ret:
                return True
        return False


    def presentingHistory(self, condition, minCount=None, maxCount=None, inMinutes=None):
        """Check if criteria present within history of prior measurements"""

        print 'calling presentingHistory', condition, minCount, maxCount, inMinutes
        if inMinutes is None:
            raise Exception('Missing inMinutes duration')
        if minCount is None and maxCount is None:
            raise Exception('Missing count -- specify minCount and/or maxCount')
        if (isinstance(condition, list) or condition not in self.map_condition_to_measurement):
            raise Exception('Unknown or invalid condition: {}'.format(condition))

        entry = self.map_condition_to_measurement[condition]
        if entry['isHistory']:
            raise Exception('presentingHistory: Unsupported history condition: {}'.format(condition))

        return entry['meas'].testHistory(condition, minCount, maxCount, inMinutes)


    def countHistory(self, conditions, inMinutes=None):
        """Check if criteria present within history of prior measurements"""
        if inMinutes is None:
            raise Exception('Missing inMinutes duration')

        if not isinstance(conditions, list): # convert to list format if needed
            conditions = [conditions]

        #print 'countHistory', inMinutes, conditions

        # verify all conditions are valid
        for cond in conditions:
            if cond not in self.map_condition_to_measurement:
                raise Exception('Unknown condition: {}'.format(cond))
            entry = self.map_condition_to_measurement[cond]
            if entry['isHistory']:
                raise Exception('presentingHistory: Unsupported history condition: {}'.format(cond))

        entry = self.map_condition_to_measurement[conditions[0]]
        return entry['meas'].countHistory(conditions, inMinutes)


    def countAnyHistory(self, measurement, inMinutes=None):
        # Make sure we've had a chance to collect required history
        # if inMinutes == None or self.currentTime == None or self.currentTime <  inMinutes:
        #     return False

        if measurement in self.measurements:
            m = self.measurements[measurement]
            return  m.countTotalHistory(inMinutes)
        else:
            raise Exception('unknown measurement {}'.format(measurement))

    def absentHistory(self, measurement, inMinutes=None):
        return self.countAnyHistory(measurement, inMinutes) == 0


    # def absentHistory(self, measurement, inMinutes=None):
    #     # Make sure we've had a chance to collect required history
    #     # if inMinutes == None or self.currentTime == None or self.currentTime <  inMinutes:
    #     #     return False
    #
    #     if measurement in self.measurements:
    #         m = self.measurements[measurement]
    #         return  m.countTotalHistory(inMinutes) == 0
    #     else:
    #         raise Exception('unknown measurement {}'.format(measurement))


class Measurement:

    # Design notes:
    #     Input classification happend on injest
    #     History classification happens at lookup time

    def __init__(self, parent, name=None, vocab=[], isManual=False,
                 classify=[], classifyHistory=[], duration=None,
                 staleAfter=10):
        self.currentVal = None
        self.currentTimestamp = None
        self.history = []
        self.name = name
        self.parent = parent
        self.isManual = isManual
        self.classifyValues = {}
        self.classifyHistory = {}
        self.duration = duration
        self.minimumFreshness = staleAfter  # TODO: should we use reminder instead??

        if not duration and classifyHistory:
            # infer history based on longest duration
            upperBounds =  [x['bounds'][1] for x in classifyHistory if 'bounds' in x and x['bounds'][1] is not None]
            upperBounds += [x['duration'] for x in classifyHistory if 'duration'in x]
            sortedUpperBounds = sorted(upperBounds)
            if sortedUpperBounds:
                self.duration = sortedUpperBounds[-1] # select largest duration

        # Register Vocabulary
        for v in vocab:
            parent.map_condition_to_measurement[v] = {'meas':self, 'isHistory':False}
        for entry in classify:
            self.classifyValues[entry['name']] = entry
            parent.map_condition_to_measurement[entry['name']] = \
                {'meas':self, 'isHistory':False}
        for entry in classifyHistory:
            self.classifyHistory[entry['name']] = entry
            parent.map_condition_to_measurement[entry['name']] = \
                {'meas':self, 'isHistory':True}


    def testAssessment(self, condition, isHistory, sustainedPct=0.9):
        #print 'testAssessment - condition: {}  isHistory: {}'.format(condition, isHistory)
        if isHistory:
            criteria = self.classifyHistory[condition]
            metric = criteria['metric']
            #print criteria
            if 'bounds' in criteria and criteria['bounds']:
                return self.testHistory(metric, criteria['bounds'][0], criteria['bounds'][1], criteria['duration'])
            elif 'isSustained' in criteria and criteria['isSustained']:
                if self.parent.currentTime >= criteria['duration']:
                    count = self.countHistory(metric, criteria['duration'])
                    total = self.countTotalHistory(criteria['duration'])
                    #print 'sustained test: {} of {}'.format(count, total)
                    return count > 0 and count >= total * sustainedPct
                else:
                    False
            else:
                raise Exception('Invalid rule {}'.format(criteria))
        else:
            #print 'testAssessment - value: {}'.format(self.getMeasurement())
            return self.getMeasurement() == condition


    def OLDtestHistory(self, condition, minCount, maxCount, inMinutes):
        """Check if history contains specified range of instances of condition
        within specified duration"""
        tally = sum([1 for entry in self.history
                     if entry['val'] == condition
                     and entry['time'] >= self.parent.currentTime - inMinutes])

        if minCount and tally < minCount:
            return False
        if maxCount and tally > maxCount:
            return False
        return True

    def testHistory(self, condition, minCount, maxCount, inMinutes):
        """Check if history contains specified range of instances of condition
        within specified duration"""

        tally = self.countHistory(condition, inMinutes)
        #print 'tally', tally, 'bounds:', minCount, maxCount

        if minCount and tally < minCount:
            return False
        if maxCount and tally > maxCount:
            return False
        return True


    def countHistory(self, condition, inMinutes):
        """Returns instance count for instances of condition within specified history duration"""

        # print 'called measurement.countHistory -- {}min {}'.format(inMinutes, condition)
        # print
        # pprint(self.history)
        # print

        if not isinstance(condition, list):
            condition = [condition]
        subset =[x for x in self.history
                 if x['val'] in condition and x['time'] >= self.parent.currentTime - inMinutes]
        tally = len(subset)

        # pprint(subset)
        # print
        return tally


    def countTotalHistory(self, inMinutes):
        """Returns instance count for items in history for specified duration"""

        if inMinutes is None:
            tally = len(self.history)
        else:
            tally = sum([1 for entry in self.history
                         if entry['time'] >= self.parent.currentTime - inMinutes])

        return tally


    def addMeasurement(self, inputVal, timestamp=None):
        """Inject new measurement, and classify if needed"""
        if timestamp is None:
            timestamp = self.parent.currentTime
        if self.classifyValues:
            val = self.classifyInput(inputVal, self.classifyValues)
            txt = self.parent.rules_log[-1]
            txt +=  '  [{}]'.format(val)
            self.parent.rules_log[-1] = txt
            #self.parent.rules_log.append(txt)
            self.parent.injest_log[-1]['classification'] = val
            if self.parent.verbose:
                print txt
        else:
            val = inputVal

        self.currentVal = val
        self.currentTimestamp = timestamp

        if self.classifyHistory or self.duration:  # of maintaining history
            self.history.append({'val': val, 'time': timestamp})
            # prune older history
            while self.history and self.history[0]['time'] < timestamp - self.duration:
                self.history = self.history[1:]
            txt = self.parent.rules_log[-1]
            txt +=  '  ({} in history)'.format(len(self.history))
            self.parent.rules_log[-1] = txt
            #self.parent.rules_log.append(txt)
            self.parent.injest_log[-1]['inHistory'] = len(self.history)

            if self.parent.verbose:
                print txt

        # if self.isManual:
        #     self.addMeasurementRequest()


    def getMeasurement(self):
        """Check for valid measurement and return if available
        Returns NOne if uninitialized or stale"""
        # print 'getMeasurement:  {}  h: {}'.format(self.currentVal, self.history)
        # print 'currentTimestamp: {} currentTimestampParent: {} freshness: {}'.format(
        #     self.currentTimestamp, self.parent.currentTime, self.minimumFreshness)

        # TODO:  Freshness should based on duration and measurement timestamp

        if (self.currentTimestamp is not None
            and (not self.minimumFreshness
                 or (self.parent.currentTime - self.currentTimestamp) < self.minimumFreshness)):
            
            if len( self.history) > 0:
                return self.history[-1]['val']
            else:
                return None
        elif self.isManual:
            self.addRequestedMeasurement()
        return None


    def getMeasurementTimestamp(self, getOldest=False):
        if len(self.history) == 0:
                return None
        elif getOldest:
            return self.history[0]['time']
        else:
            return self.history[-1]['time']


    @staticmethod
    def classifyInput(val, table):
        """Classifies numerical input based on ranges specified in mapping table
        Entry format: {'name':string, 'bounds': [number, number]}
        """
        for entry in table.values():
            lowerBound = entry['bounds'][0]
            upperBound = entry['bounds'][1]
            if lowerBound is not None and val < lowerBound:
                continue
            if upperBound is not None and val > upperBound:
                continue
            return entry['name']
        return '*unknown**'


    def addRequestedMeasurement(self):
        """Flag missing measurements"""
        if self.name not in self.parent.requestedMeasurements:
            self.parent.requestedMeasurements.append(self.name)

