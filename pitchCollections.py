# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# 
#
# Copyright:    Christophe Guillotel-Nothmann Copyright © 2017
#-------------------------------------------------------------------------------

from music21 import tree, note, chord, stream, pitch, interval, expressions
from music21.tree.spans import PitchedTimespan
from music21.tree.verticality import VerticalitySequence, Verticality
from _operator import and_
from tkinter.constants import VERTICAL, END
from copy import deepcopy
from music21.pitch import Pitch
import numpy, logging, copy
from setuptools.dist import sequence 
from music21.stream import Score
from python_log_indenter import IndentedLoggerAdapter
from music21.chord import Chord
from music21.tree.timespanTree import TimespanTree
from music21.languageExcerpts.instrumentLookup import transposition
from email.charset import SHORTEST
from music21.figuredBass import notation 
from itertools import combinations
from music21.note import Note, Rest
import math
from builtins import isinstance
 

    
class PitchCollectionSequence (object):
    
    def __init__(self, work=None):
        self.work = work 
        self.id = id(self)
        self.endTimeList = []
        self.duration = None
        self.totalPitches = 0
        #self.idDictionary = {}  # ## maps note or chord id to analyzedPitches (one note or chord can have several analytical interpretations according to offset) 
        self.name = None 
        self.finalisRoot = None
           
        ''' Create AnalyzedPitchCollectionSequence  '''
        self.explainedPitchCollectionList = []
        
        
        if work != None:
            logging.info ('Creating pitch collections...')  
            
            ''' correct symbolic measure numbers '''
            self.correctSymbolicMeasureNumbers()
            
            self.stream = work
            self.semiFlatStream = self.stream.semiFlat
            self.scoreTree = tree.fromStream.asTimespans(self.stream, flatten=True, classList=(note.Note, chord.Chord, Rest))
            self.measureOffsetList = self.getMeasureOffsets()
            
            
            
           
            for verticality in self.scoreTree.iterateVerticalities():
                #print (round(verticality.offset/work.duration.quarterLength,2))
                
                ''' check if next event is not general break  '''
                generalRestPitchColl = self.getGeneralRestNextEvent(verticality) 
                
                ''' create pitch collection '''
                pitchCollection = self.createPitchCollection (verticality)
                self.explainedPitchCollectionList.append(pitchCollection)
                
                ''' adjust offset and duration if general rest exists '''
                if generalRestPitchColl != None:
                    self.explainedPitchCollectionList.append(generalRestPitchColl)
                    pitchCollection.duration = pitchCollection.duration - generalRestPitchColl.duration 
                    
                ''' add relative offsets (i.e. offsets within a measure) '''
                    
                pitchCollection.relativeOffset = self.getRelativeOffset(verticality)
           
        
        ''' set section endTimes '''
        self.explainedPitchCollectionList= self.setSectionStartAndEndTimes(self.explainedPitchCollectionList) 
        self.analyzedPitches = self.getAnalyzedPitches()
      
    def addAnalyzedPitch(self, analyzedPitch):
        self.analyzedPitches.append(analyzedPitch)
        pitchColl = self.getAnalyzedPitchCollectionAtOffset(analyzedPitch.offset)
        pitchColl.analyzedPitchList.append(analyzedPitch)
        
        
    def getAnalysedPitchesFromXML_ID(self, xmlId):
        analyzedPitchList = []
        for analyzedPitch in self.analyzedPitches:
            if analyzedPitch.id == xmlId:
                analyzedPitchList.append(analyzedPitch)
        if len(analyzedPitchList) == 0: 
            print ("XML:id not found: " + xmlId)
        return analyzedPitchList
                
            
    
    def addConceptToAnalyzedPitches (self, concept, xmlIdList):
        for element in xmlIdList:
            for analyzedPitch in self.getAnalysedPitchesFromXML_ID(element):
                analyzedPitch.concept = concept
    
    def updatePitchCollSequence(self):
        ''' this is used to update general information about sequence (duration, total pitches, ) '''
        self.duration = 0
        
        for pitchColl in self.explainedPitchCollectionList:
            self.duration = self.duration + pitchColl.duration
        
        self.totalPitches = len (self.analyzedPitches)
        
        
        ''' sort pitch coll list according to offsets '''
        self.explainedPitchCollectionList.sort(key=lambda pitchColl: pitchColl.offset)
        
        
    def getNextPitchColl(self, pitchColl):
        for element in self.explainedPitchCollectionList:
            if element.offset > pitchColl.offset:
                return element
        return None
    
    def getElementsAtOffset (self, offset, classList = [Note, chord.Chord]):
        elementList = []
        
        
        pitchColl = self.getAnalyzedPitchCollectionAtOffset(offset)
        if not hasattr(pitchColl, "analyzedPitchList"):
            print ("no pitches")
        for explainedPitch in pitchColl.analyzedPitchList:
            for element in self.getElementsContainingPitch(pitchColl.verticality, explainedPitch.pitch):
                if type (element) in classList : 
                    elementList.append(element)
        return elementList
        
        
 
        
        
#         nextPitchColl = self.getNextPitchColl(pitchColl)
#         
#         
#         
#         if nextPitchColl != None:
#             for element in self.work.flat.getElementsByOffset(offset, nextPitchColl.offset, mustBeginInSpan= False, includeEndBoundary = False):
#                 print (str (type (element)))
#                 
#                 if type (element) in classList :
#                     if element.offset == nextPitchColl.offset:continue
#                     print (element.offset)
#                     elementList.append(element)
#                 
#         else:
#             for element in self.work.flat.getElementsByOffset(offset):
#                 if type (element) in classList :
#                     elementList.append(element)
#                 
#         return elementList

            
                
            
    
    
    def getRealBassPatterns(self):
        realBassList = []
        
        for pitchColl in self.explainedPitchCollectionList:
            degree = pitchColl.bassScaleDegree + "^" + pitchColl.getSimpleFilteredContinuoSigns()
            
            if pitchColl.isSectionStart: 
                degree = "*" + degree
            if pitchColl.isSectionEnd : 
                degree = degree + "|"   
                  
            if len (realBassList) > 0 :
                if degree == realBassList[-1] + "|":  
                    realBassList[-1] = realBassList[-1]+ "|"
                    continue
                
                elif "*" + degree == realBassList[-1]:
                    continue
                
                elif degree == realBassList[-1]:
                    continue
                
            
            realBassList.append(degree)
        
        return realBassList
    
    def getRealBassSubPatterns (self, bassPatterns, minLength = 3, maxLength = 10):
        patternList = []
    
        for x, y in combinations(range(len(bassPatterns) + 1), r = 2):
            subList = bassPatterns[x:y] 
            
            if len (subList) < minLength: continue
            if len (subList) > maxLength: continue
            
            hasInterruption = False
            for degree in subList[0:len(subList)-1]: 
                if "|" in degree : 
                    hasInterruption = True
                    break 
            
            if subList not in patternList and hasInterruption== False: 
                patternList.append(subList)
                
        return patternList
    
    def getSubPatternOccurrences (self):
        subPatternOccurrenceList = []
        
        bassPatterns = self.getRealBassPatterns()
        bassPatternStr = str(bassPatterns)
        
        bassSubPatternList = self.getRealBassSubPatterns(bassPatterns)
        
        for bassSubPattern in bassSubPatternList:
        
            subPatternOccurrenceList.append ([bassPatternStr.count(str(bassSubPattern)[1:-1]), bassSubPattern])
            
        subPatternOccurrenceList.sort(key=lambda x: x[0], reverse=True)
        
        return subPatternOccurrenceList
        
        
    
    def analyzeRealBassMovements (self):
        '''  used to retrieve scale degree successions with figured bass '''
        self.continuoSuccessionDict = {} 
        self.motionDictionary = {
            "step_5=>5": [],
            "step_6=>6": [],
            "step_6<=>5": [],
            "leep_5=>5": [],
            "leep_6=>6": [],
            "leep_6<=>5": [], 
            "+m2_6=>5": [],
            "+m2_other":[],
            "-m2_5=>6": [],
            "-m2_other": []
            }
        
        
        pitchCollCounter = 0  
        while pitchCollCounter < len(self.explainedPitchCollectionList)-1:
            pitchCollA = self.explainedPitchCollectionList[pitchCollCounter]
            pitchCollB = self.explainedPitchCollectionList[pitchCollCounter + 1]
            
            if pitchCollA.bassScaleDegree == pitchCollB.bassScaleDegree: 
                pitchCollCounter = pitchCollCounter + 1
                continue  
            
            if pitchCollA.verticality == None or  pitchCollB.verticality == None:
                pitchCollCounter = pitchCollCounter + 1
                continue  
                 
            
            ''' continuo successions '''
            
            pitchCollASign = pitchCollA.getSimpleFilteredContinuoSigns()
            pitchCollBSign = pitchCollB.getSimpleFilteredContinuoSigns()
            
            continuoNotationA = pitchCollA.bassScaleDegree + "_" + pitchCollASign
            continuoNotationB = pitchCollB.bassScaleDegree + "_" + pitchCollBSign
            degreeSuccession = pitchCollA.bassScaleDegree + "_" + pitchCollB.bassScaleDegree
            
            
            successionKey = continuoNotationA + "=>" + continuoNotationB
            
            if not degreeSuccession in self.continuoSuccessionDict: self.continuoSuccessionDict[degreeSuccession] ={
                "name" : degreeSuccession,
                "firstScaleDegreeName": pitchCollA.bassScaleDegree,
                "secondScaleDegreeName" : pitchCollB.bassScaleDegree,
                "pitchCollectionPairs": [],
                "harmonizations": {}
                } 
            
            continuoSuccessionDictEntry = self.continuoSuccessionDict[degreeSuccession]
            continuoSuccessionDictEntry["pitchCollectionPairs"].append([pitchCollA, pitchCollB]) 
            
            continuoSuccessionHarmonization = continuoSuccessionDictEntry["harmonizations"]
            
            if not successionKey in continuoSuccessionHarmonization: continuoSuccessionHarmonization[successionKey] = {
                "name": successionKey,
                "firstHarmonizationName": pitchCollASign,
                "secondHarmonizationName": pitchCollBSign, 
                "pitchCollectionPairs": [] 
                }
            
            harmonizationSuccession = continuoSuccessionHarmonization[successionKey]
            harmonizationSuccession["pitchCollectionPairs"].append([pitchCollA, pitchCollB])
            
            ''' motion analysis ''' 
            ''' check if step '''
            bassInterval = interval.Interval(pitchCollA.bass, pitchCollB.bass)
            
            if bassInterval.directedSimpleName in ["m2", "M-7"]:  #
            
                if pitchCollASign  in ["6", "64", "65"] and pitchCollBSign == "":
                    self.motionDictionary["+m2_6=>5"].append([pitchCollA, pitchCollB])
                else: 
                    self.motionDictionary["+m2_other"].append([pitchCollA, pitchCollB])
                    
            elif bassInterval.directedSimpleName in ["m-2", "M7"]:
                if pitchCollASign == "" and pitchCollBSign in ["6", "64", "65"]:
                    self.motionDictionary["-m2_5=>6"].append([pitchCollA, pitchCollB])
                else: 
                    self.motionDictionary["-m2_other"].append([pitchCollA, pitchCollB])  
                
            
            
            
           
            
            motion = "leep"
            if bassInterval.simpleName in ["M2", "m2", "M7", "m7"]: motion = "step"
            
            continuoSign = ""
            ''' check continuo signs '''
            
           
            
            
            if pitchCollASign == "" and pitchCollBSign == "": continuoSign = "5=>5"
            elif pitchCollASign in ["6", "64", "65"] and pitchCollBSign in ["6", "64", "65"]: continuoSign = "6=>6"            
            elif pitchCollASign == ""  and pitchCollBSign in ["6", "64", "65"]: continuoSign = "6<=>5"
            elif pitchCollASign in ["6", "64", "65"] and pitchCollBSign == "" : continuoSign = "6<=>5"
            else:
                pitchCollCounter = pitchCollCounter + 1 
                continue 
            
            
            self.motionDictionary[motion + "_" + continuoSign].append([pitchCollA, pitchCollB])
            
 
            
            pitchCollCounter = pitchCollCounter + 1 
    
    
    def createPitchCollection (self, verticality):
         
        analyzedPitchList = []
        verticalities = VerticalitySequence([None, verticality, None])
        
         
         
        ''' check if verticality is consonant '''
        #=======================================================================
        # element = verticality.makeElement()
        # 
        # if isinstance(element, chord.Chord) :
        #     if element.isConsonant(): isConsonant = True
        #     
        # if isinstance (element, note.Note): isConsonant = True
        #=======================================================================
         
        ''' extract all pitches (not only pitch sets but also every instance of same pitch) '''
        ''' 1. get everything in start and overlap timespans '''
        elementList = []
        for element in verticality.startTimespans:
            elementList.append(element)
         
        for element in verticality.overlapTimespans:
             
            if round (element.endTime, 6) == round (verticality.offset, 6):continue
            elementList.append(element)
        
        
        
        ''' 2. loop over these elements  '''
        for element in elementList:
            ''' 2.1. extract part '''
          
            elementPart = element.getParentageByClass(classList=(stream.Part,))
         
            ''' 2.2. extract voice '''
            elementVoice = element.getParentageByClass(classList=(stream.Voice,))
         
            ''' 2.3a if element is note '''
            if isinstance(element.element, note.Note):
                ''' get id for this specific note '''
                elementId = element.element.id 
                ''' create analyzed pitch, add information append to pitchList'''
                analyzedPitch = Pitch(element.element.pitch, verticalities)
                analyzedPitch.id = elementId
                analyzedPitch.part = elementPart
                analyzedPitch.voice = elementVoice
                analyzedPitch.attack = True if element in verticality.startTimespans else False
                analyzedPitchList.append(analyzedPitch)
                 
                  
                 
                 
                if verticality.nextVerticality != None:
                    analyzedPitch.segmentQuarterLength = verticality.nextVerticality.offset - verticality.offset
                else:
                    analyzedPitch.segmentQuarterLength = verticality.startTimespans[0].quarterLength
                 
            if isinstance(element.element, chord.Chord):
                 
                ''' loop over every note in chord and create analyzed pitch '''
                for chordNote in element.element._notes:
                    analyzedPitch = Pitch(chordNote.pitch, verticalities)
                    analyzedPitch.id = chordNote.id
                    analyzedPitch.part = elementPart
                    analyzedPitch.voice = elementVoice
                    analyzedPitch.attack = True if element in verticality.startTimespans else False
                    analyzedPitchList.append(analyzedPitch) 
                    
            if isinstance(element.element, Rest):
                    analyzedPitch = Pitch(None, verticalities)
                    analyzedPitch.id = element.element.id
                    analyzedPitch.part = elementPart
                    analyzedPitch.voice = elementVoice
                    analyzedPitch.attack = True if element in verticality.startTimespans else False
                    analyzedPitchList.append(analyzedPitch)
            
        return PitchCollection(verticality, analyzedPitchList)
    

    
#     def setRootDegreeFromReferencePitch (self, referencePitch):
#         
#         stepDictionary = {}
#         
#         ''' associate final chord to I and and create dictionary of all other scale steps'''
#         
#         if isinstance(referencePitch, str):
#             rootPitch = pitch.Pitch(referencePitch)
#         
#         referenceStep = rootPitch.step
#         
#         diatonicSteps = ["A", "B", "C", "D", "E", "F", "G"]
#         referenceIndex = None
#         
#         for counter, diatonicStep in enumerate(diatonicSteps):
#             if diatonicStep == referenceStep: referenceIndex = counter
#                 
#         stepDictionary[diatonicSteps [referenceIndex]] = "I" 
#         stepDictionary[ diatonicSteps [(referenceIndex + 1) % 7]] = "II"
#         stepDictionary [diatonicSteps [(referenceIndex + 2) % 7]] = "III"
#         stepDictionary [diatonicSteps [(referenceIndex + 3) % 7]] = "IV"
#         stepDictionary [diatonicSteps [(referenceIndex + 4) % 7]] = "V"
#         stepDictionary [diatonicSteps [(referenceIndex + 5) % 7]] = "VI"
#         stepDictionary [diatonicSteps [(referenceIndex + 6) % 7]] = "VII"
#        
#         
#          
#         ''' given a root, this deduces the roman numeral from a given finalis Root '''
#         for pitchColl in self.explainedPitchCollectionList:
#             if pitchColl.rootPitch != None:
#                 pitchColl.romanNumeral = stepDictionary[pitchColl.rootPitch.step]
                
    def getDiatonicDegreesDictionary(self):
        ''' returns a dictionary with scale degrees and the occurrences '''
        ''' SCALE DEGREES ARE NOT COMPUTED IN RELATION TO THE FINAL BUT TO THE UNTERLYING SCALE '''
        
        
        self.diatonicDegreesDictionary = {}
        
        for pitchColl in self.explainedPitchCollectionList:
            if not pitchColl.bassDiatonicDegree in self.diatonicDegreesDictionary: self.diatonicDegreesDictionary[pitchColl.bassDiatonicDegree] = {
                "name": pitchColl.bassDiatonicDegree,
                "pitchCollections": [],
                "harmonizations": {},
                "duration": 0
                } 
            
            diatonicDegreeDictionaryEntry = self.diatonicDegreesDictionary[pitchColl.bassDiatonicDegree]
            
            diatonicDegreeDictionaryEntry["pitchCollections"].append(pitchColl)
            diatonicDegreeDictionaryEntry["duration"] = diatonicDegreeDictionaryEntry["duration"] +  pitchColl.duration
            
            continuoSigns = pitchColl.getSimpleFilteredContinuoSigns()
            if continuoSigns == "": continuoSigns = "[None]"
            
            harmonizationDictionary = diatonicDegreeDictionaryEntry["harmonizations"]
            
            if not continuoSigns in harmonizationDictionary:
                harmonizationDictionary[continuoSigns] = {
                    "name": continuoSigns,
                    "pitchCollections": [],
                    "duration": 0
                    }
            harmonization = diatonicDegreeDictionaryEntry["harmonizations"][continuoSigns]
            harmonization["duration"] = harmonization["duration"] + pitchColl.duration
            harmonization["pitchCollections"].append (pitchColl)
                
        return self.diatonicDegreesDictionary
    
    def getDissonancesAtOffset (self, offset):
        ''' returns identified dissonances starting before current offset and resolving after this offset '''
        analyzedDissonancesList = []
        
        for pitchCollection in self.explainedPitchCollectionList:
            
            ''' break if collection offset > as current offset ''' 
            if pitchCollection.verticality.offset > offset:
                break
            
            ''' check if collection has dissonances resolving after current offset '''
            if pitchCollection.getHighestResolutionOffest() > offset:
                
                for analyzedPitch in pitchCollection.getExplainedPitches(['PN', 'NN', 'AN', 'EN', 'SU']):
                    if analyzedPitch.resolutionOffset != None:
                        analyzedDissonancesList.append(analyzedPitch)
        return analyzedDissonancesList  
    
    def setRealBassDiatonicDegree (self, scale):
        stepDictionary = {}
        
        diatonicSteps = [scalePitch.name for scalePitch in scale.pitches]
        
        for stepCounter, diatonicStep in enumerate(diatonicSteps):
            if diatonicStep in stepDictionary: continue
            
            stepDictionary[diatonicStep ] = str(stepCounter + 1)
            
            dimU = interval.Interval("d1")
            augU = interval.Interval("a1")
            
            dimU.noteStart = note.Note(diatonicStep)
            augU.noteStart = note.Note(diatonicStep)
        
            flatDegree = dimU.noteEnd 
            sharpDegree = augU.noteEnd
            
            stepDictionary[flatDegree.name] = str(stepCounter + 1)+"-"
            stepDictionary[sharpDegree.name] = str(stepCounter + 1)+"#"
            
        for pitchColl in self.explainedPitchCollectionList:
            realBassPitch = pitch.Pitch(pitchColl.bass) 
            
            if realBassPitch.name in stepDictionary:
                pitchColl.bassDiatonicDegree = stepDictionary[realBassPitch.name]
            else: 
                pitchColl.bassDiatonicDegree = "?" 
                
                    
    
    
    def setRealbassScaleDegreeFromReferencePitch (self, scale, referencePitch):  
        
        
        ''' given a reference pitch (final) and a scale, add information about scale degrees and continuo signs to pitch colls '''
        
        stepDictionary = {}
        
        if isinstance(referencePitch, str):
            rootPitch = pitch.Pitch(referencePitch)
        
        referenceStep = rootPitch
        
        diatonicSteps = [scalePitch.name for scalePitch in scale.pitches]
        referenceIndex = None
        
        for counter, diatonicStep in enumerate(diatonicSteps):
            if diatonicStep == referenceStep.name: referenceIndex = counter
                
        stepDictionary[diatonicSteps [referenceIndex]] = "1" 
        stepDictionary[ diatonicSteps [(referenceIndex + 1) % 7]] = "2"
        stepDictionary [diatonicSteps [(referenceIndex + 2) % 7]] = "3"
        stepDictionary [diatonicSteps [(referenceIndex + 3) % 7]] = "4"
        stepDictionary [diatonicSteps [(referenceIndex + 4) % 7]] = "5"
        stepDictionary [diatonicSteps [(referenceIndex + 5) % 7]] = "6"
        stepDictionary [diatonicSteps [(referenceIndex + 6) % 7]] = "7"
        
        ''' add chromatic steps ''' 
        chomaticDictionary = {}
        alterationDictionary ={}
        
        for diatonicStepKey, diatonicStep in  stepDictionary.items():
            dimU = interval.Interval("d1")
            augU = interval.Interval("a1")
            
            dimU.noteStart = note.Note(diatonicStepKey)
            augU.noteStart = note.Note(diatonicStepKey)
        
            flatDegree = dimU.noteEnd 
            sharpDegree = augU.noteEnd
            
            chomaticDictionary[flatDegree.name] = diatonicStep + "-"
            chomaticDictionary[sharpDegree.name] = diatonicStep + "#"
            
            alterationDictionary[flatDegree.name] =  "-"
            alterationDictionary[sharpDegree.name] = "#"
            
            
            
        ''' add items to step dict ''' 
        for degreeKey, degree in  chomaticDictionary.items():
            stepDictionary[degreeKey]= degree 
        
         
        ''' set real bass degrees accordingly to dic '''
        for pitchColl in self.explainedPitchCollectionList:
            
            realBassPitch = pitch.Pitch(pitchColl.bass) 
            if realBassPitch.name in stepDictionary: 
                pitchColl.bassScaleDegree = stepDictionary[realBassPitch.name]
        
                
            ''' loop over intervals '''
            for pitchCollInt in pitchColl.intervalsToBass:
                genericSimpleName = str(pitchCollInt.generic.simpleUndirected)
                pitchColl.simpleContinuoSigns.append(genericSimpleName)
                
                 
                
                endNote=  pitchCollInt.noteEnd
                
                ''' if  end note is not diatonic step, add alteration or ?  '''
                if endNote.name in diatonicSteps: 
                    pass
                elif endNote.name in alterationDictionary:
                    genericSimpleName = str(genericSimpleName) + alterationDictionary[endNote.name]
                else: 
                    genericSimpleName = str(genericSimpleName) + "?"
                
                if genericSimpleName not in pitchColl.continuoSigns:
                    pitchColl.continuoSigns.append(genericSimpleName)
                    
            pitchColl.continuoSigns.sort()
                
                
                    
         
         
        
    
    def getContinuoDictionary (self):
        self.continuoDictionary = {}
        
        for pitchColl in self.explainedPitchCollectionList:
            
            if not pitchColl.bassScaleDegree in self.continuoDictionary: self.continuoDictionary[pitchColl.bassScaleDegree] = {
                "name": pitchColl.bassScaleDegree,
                "pitchCollections": [],
                "harmonizations": {},
                "duration": 0
                }
            
            self.continuoDictionary[pitchColl.bassScaleDegree]["pitchCollections"].append(pitchColl) 
            self.continuoDictionary[pitchColl.bassScaleDegree]["duration"] = self.continuoDictionary[pitchColl.bassScaleDegree]["duration"] + pitchColl.duration
            
            continuoSigns = pitchColl.getSimpleFilteredContinuoSigns()
            if continuoSigns == "": continuoSigns = "[None]"
            
            
            
            if not continuoSigns in self.continuoDictionary[pitchColl.bassScaleDegree]["harmonizations"]:
                self.continuoDictionary[pitchColl.bassScaleDegree]["harmonizations"][continuoSigns] = {
                    "name": continuoSigns,
                    "pitchCollections": [],
                    "duration": 0
                    }
            harmonization = self.continuoDictionary[pitchColl.bassScaleDegree]["harmonizations"][continuoSigns]
            harmonization["duration"] = harmonization["duration"] + pitchColl.duration
            harmonization["pitchCollections"].append (pitchColl)
             
                
        return self.continuoDictionary
            
            
        
        
       
    
    def getAnalyzedCollections (self, startOffset=None, stopOffset=None, templateRepresentation=None, probabilityThreshold=None):
        pitchCollList = []
        
        for pitchCollection in self.explainedPitchCollectionList:
            
            if startOffset != None:
                if pitchCollection.verticality.offset < startOffset: continue
                
            if stopOffset != None:
                if pitchCollection.verticality.offset > stopOffset: break
            
            if probabilityThreshold != None:
                if pitchCollection.probability < probabilityThreshold: continue
            
            if templateRepresentation != None:
                if len (pitchCollection.template.representation) != len (templateRepresentation) : continue  # check if same size
                comparison = True
                for pitchSetCounter in range (0, len(pitchCollection.template.representation)):  # check if match
                    if pitchCollection.template.representation[pitchSetCounter] != templateRepresentation[pitchSetCounter] :
                        comparison = False
                        break
                if comparison == False: continue 
                
            pitchCollList.append(pitchCollection)
        return pitchCollList
    
    def getAnalyzedPitches(self, elementID=None, offset=None):
        if elementID != None:
            return self.getAnalyzedPitchCorrespondingToId(elementID)
        elif offset != None:
            return self.getExplainedPitchesAtOffset(offset)
            
        else:
            analyzedPitchList = []
            
            for analyzedPitchCollection in self.explainedPitchCollectionList:
                analyzedPitchList = analyzedPitchList + analyzedPitchCollection.analyzedPitchList
        
        return analyzedPitchList
    
    def getAnalyzedPitchCorrespondingToId (self, elementID, offset=None):
        analyzedPitchList = []
        for analyzedPitchCollection in self.explainedPitchCollectionList:
            analyzedPitchesCorrespondingToId = analyzedPitchCollection.getAnalyzedPitchesCorrespondingToId(elementID)
            if  analyzedPitchesCorrespondingToId != None:
                if offset != None:
                    if offset == analyzedPitchesCorrespondingToId.offset:
                        return [analyzedPitchesCorrespondingToId]
                else:
                    analyzedPitchList.append (analyzedPitchesCorrespondingToId)
        return analyzedPitchList
    
    def getAnalyzedPitchCollectionAtOffset (self, offset):
        for explainedPitchCollection in self.explainedPitchCollectionList:
            if explainedPitchCollection.offset == offset:
                return explainedPitchCollection 
            
        return None
    
    def getElementsContainingPitch (self, nhVerticality, pitch): 
        elementList = []
        allElements = []
        
        for element in nhVerticality.startTimespans:
            allElements.append(element.element)
            
        for element in nhVerticality.overlapTimespans:
            allElements.append(element.element)
        
        for element in allElements:
            if isinstance(element, note.Note):
                if element.pitch == pitch:
                    elementList.append(element)
            if isinstance(element, chord.Chord):
                if pitch in element.pitches:
                    elementList.append(element)
        return elementList
    
    def getExplainedPitchesAtOffset (self, offset):
        ''' get pitch collection '''
        pitchCollection = self.getAnalyzedPitchCollectionAtOffset(offset)
                
        ''' get explained pitches '''   
        pitchList = pitchCollection.analyzedPitchList
        return pitchList
    
    def getExplainedPitchAtOffset (self, offset, pitch):
        ''' returns a list of explained pitch instances which correspond to the pitch at specified offset ''' 
        
        ''' get all pitches at offset '''
        explainedPitchList = self.getExplainedPitchesAtOffset(offset)
        explainedPitchSubList = []
        
        for analyzedPitch in explainedPitchList:
            if analyzedPitch.pitch == pitch:
                explainedPitchSubList.append(analyzedPitch)
        
        return explainedPitchSubList
    
    def getExplainedPitchesFromTo (self, startOffset, stopOffset, filterPitch=None):
        pitchList = []
        
        for explainedPitchCollection in self.explainedPitchCollectionList:
            if explainedPitchCollection.verticality.offset < startOffset: continue 
            if explainedPitchCollection.verticality.offset >= stopOffset: continue
            
            if filterPitch == None:
                pitchList = pitchList + explainedPitchCollection.analyzedPitchList
            else :
                pitchList = pitchList + self.getExplainedPitchAtOffset(explainedPitchCollection.verticality.offset, filterPitch)
            
        return pitchList
    
    def getExplainedPitchCollectionBeforeOffset (self, offset):
        ''' get index number of explained collection'''
        
        for x in range (0, len (self.explainedPitchCollectionList)):
            if self.explainedPitchCollectionList[x].verticality.offset == offset:
                if x > 0: return self.explainedPitchCollectionList[x - 1]
        
        return None
    
    def getGeneralRestNextEvent (self, vert):
        ''' checks if next event is a general rest and returns empty pitch coll if so  ''' 
         
        if vert.nextVerticality == None: return None
        nextVert = vert.nextVerticality
        nextVertOverlapTS = nextVert.overlapTimespans
        nextVertStopTS = nextVert.stopTimespans
         
        if len (nextVertOverlapTS) == 0 and len (nextVertStopTS) == 0:
            highestEndtime = 0
             
            ''' get highest offset of starts and overlaps '''
            for ts in vert.startAndOverlapTimespans:
                if ts.endTime > highestEndtime: highestEndtime = ts.endTime
                 
            generalRestDuration = nextVert.offset - highestEndtime
            generalRestOffset = highestEndtime
            
            for element in self.stream.flat.getElementsByOffset(generalRestOffset):
                if hasattr(element, "measureNumber"):
                    measureNumber = element.measureNumber
                    break
             
             
        
            return PitchCollection(None, [], generalRestDuration, generalRestOffset, measureNumber)
             
         
        else:
            return None
         
        ''' if next vert has no stop and no overlaps, the event between current verticality and next one is a general silence '''
          
         
    
#     def getChordifiedStream (self, unused_filter=['CN', 'SU']):
#     
#         ''' build root stream and chordify it '''
#         rootStream = self.getFundamentalBass()
#         chordifiedStream = rootStream.chordify()
#         
#         ''' loop over chords in stream '''
#         for chordElement in chordifiedStream.flat.getElementsByClass(chord.Chord):
#             offset = chordElement.offset
#             duration = chordElement.duration.quarterLength
#             if len (chordElement.pitches) > 0:
#                 chordElement.root = chordElement.pitches[0]
#             else: chordElement.root = None
#             
#             ''' get all pitches between offset and next offset '''
#             analyzedPitchList = self.getExplainedPitchesFromTo(offset, offset + duration, None)
#             
#             subList = []
#             for analyzedPitch in analyzedPitchList:
#                 
#                 ''' filter pitches and add them '''
#                 if analyzedPitch.pitchType in unused_filter: 
#                     subList.append(analyzedPitch.pitch)
#             chordElement.pitches = subList
#         
#         return chordifiedStream            
    
    def correctSymbolicMeasureNumbers(self):
        ''' this reassigns  symbolic measure numbers: starting with 1 an numbering everything '''
        
        for part in  self.work.recurse().getElementsByClass(stream.Part):
            measureCounter = 1
            for measure in part.recurse().getElementsByClass(stream.Measure):
                measure.number = measureCounter
                measureCounter = measureCounter+1
                
                
    
    def getMeasureOffsetDictionary (self):
        measureOffsetDictionary = {}
         
        # for measure in  self.work.recurse().getElementsByClass(stream.Measure):  
        #     if measure.measureNumber in measureOffsetDictionary:
        #         if measureOffsetDictionary[measure.measureNumber]["offsetLow"] > measure.offset: 
        #             measureOffsetDictionary[measure.measureNumber]["offsetLow"] = measure.offset
        #         if measureOffsetDictionary[measure.measureNumber]["offsetHigh"] < measure.offset + measure.highestOffset : 
        #             measureOffsetDictionary[measure.measureNumber]["offsetHigh"] = measure.offset + measure.highestOffset
        #         if measure not in measureOffsetDictionary[measure.measureNumber]["elements"]: measureOffsetDictionary[measure.measureNumber]["elements"].append(measure)
        #     else :
        #         measureOffsetDictionary[measure.measureNumber] = {
        #             "offsetLow" : measure.offset,
        #             "offsetHigh": measure.offset + measure.highestOffset,
        #             "elements": [measure]
        #             }
        #
        
        for pitchColl in self.explainedPitchCollectionList:
            
            
            if pitchColl.measureNumber in measureOffsetDictionary:
                if pitchColl.offset < measureOffsetDictionary[pitchColl.measureNumber]["offsetLow"]:
                    measureOffsetDictionary[pitchColl.measureNumber]["offsetLow"] = pitchColl.offset
                if pitchColl.offset > measureOffsetDictionary[pitchColl.measureNumber]["offsetHigh"]:
                    measureOffsetDictionary[pitchColl.measureNumber]["offsetHigh"] = pitchColl.offset
            
            else:
                measureOffsetDictionary[pitchColl.measureNumber] = {
                "offsetLow" : pitchColl.offset,
                "offsetHigh": pitchColl.offset,
                "elements": [pitchColl]
                } 
                    
        

        return measureOffsetDictionary
            
            
        
       
    
    def getMeasureOffsets(self):
        measureOffsetList = []
        
        for measure in  self.work.recurse().getElementsByClass(stream.Measure):
            
            if measure.offset not in measureOffsetList:
                measureOffsetList.append(measure.offset)
        
        return measureOffsetList
            
            
        
    def getPitchSubset (self, startOffset, endOffset, includeEndOffset = True):
        pitchList = []
        
        pitchCollSubset = self.getPitchCollectionSubset(startOffset, endOffset, includeEndOffset)
        for pitchColl in pitchCollSubset:
            pitchList = pitchList + pitchColl.analyzedPitchList
            
        return pitchList
    
    
    
    def getPitchCollectionSubset (self, startOffset, endOffset, includeEndOffset = True):
        subList = []
        
        for pitchColl in self.explainedPitchCollectionList:
            if includeEndOffset == True:
                if pitchColl.offset >= startOffset and pitchColl.offset <= endOffset: 
                    subList.append(pitchColl)
            if pitchColl.offset >= startOffset and pitchColl.offset < endOffset: 
                subList.append(pitchColl)
            elif pitchColl.offset > endOffset : return subList
        
        return subList
    
    def getPitchCollectionContext (self, offset, context):
        contextList = []
        
        ''' get pitch coll index of offset'''
        v0Index = None
        for  explainedPitchCollectionCounter in range (0, len(self.explainedPitchCollectionList)):
            if self.explainedPitchCollectionList[explainedPitchCollectionCounter].offset == offset:
                v0Index = explainedPitchCollectionCounter
                break
        
        ''' loop over pitch colls from lowest index to highest index'''
        lowestIndex = v0Index - context
        highestIndex = v0Index + context
        
        for index in range (lowestIndex, highestIndex + 1):
            if index < 0: contextList.append(None)  # index out of range 
            elif index > len(self.explainedPitchCollectionList) - 1: contextList.append(None)
            else:
                contextList.append(self.explainedPitchCollectionList[index])
                
        return contextList
    
    
    def getRelativeOffset (self, verticality):
        
        ''' given a verticality, this function returns its relative offset, i.e its offset within a measure'''
        referenceMeasureOffset = None
        
        for count, value in enumerate(self.measureOffsetList):
            if len(self.measureOffsetList) > count +1 : 
                if verticality.offset >= value and verticality.offset < self.measureOffsetList[count+1]:
                    referenceMeasureOffset = value
                    break
            else:
                
                if verticality.offset >= value:
                    referenceMeasureOffset = value
                    break
                
        if referenceMeasureOffset != None:
            return verticality.offset - referenceMeasureOffset
                    
                
                    
                
        
        
        
        
        
    
    def getSectionEndTimes (self, sectionEndMarkers = ["final", "double", "fermata"]):
        '''this always takes into account the element's endTime: i.e. offset + duration in quarter length'''
         
        offsetList = [] 
        if hasattr(self, "stream")== False: return []
          
        if "final" in sectionEndMarkers or "double" in sectionEndMarkers or "repeat" in sectionEndMarkers:
            for measure in self.stream.semiFlat.getElementsByClass(stream.Measure):
                if measure.rightBarline == None : continue
                if measure.rightBarline.type in  ["final", "double"]: 
                    highestTime = measure.duration.quarterLength + measure.offset
                    if highestTime not in offsetList: 
                        offsetList.append(highestTime)
             
        if "fermata" in sectionEndMarkers:
            for noteElement in self.stream.flat.recurse().getElementsByClass (note.Note):
                for elementExpression in noteElement.expressions:
                    if elementExpression.name == "fermata":
                        endTime = noteElement.offset + noteElement.duration.quarterLength
             
                        if endTime not in offsetList: 
                            offsetList.append(endTime) 
              
        return offsetList 
        
    def getUnexplainedPitches (self, startOffset=None, stopOffset=None):
        pitchList = []
        for explainedPitchCollection in self.explainedPitchCollectionList:
            for unexplainedPitch in explainedPitchCollection.getUnexplainedPitches():
                    
                if startOffset != None and stopOffset != None:
                    if unexplainedPitch.offset >= startOffset and unexplainedPitch.offset < stopOffset:
                        pitchList.append(unexplainedPitch)
                 
                else: pitchList.append(unexplainedPitch) 
                
                ''' TODO: additionnal conditions startOffset != None, stopOffset == None etc. if needed ? '''  
        
        return pitchList   
    
    def setPitchObservations(self, dataPath, labelDictionary): 
        import numpy as np
        import os
        
        ''' get highest fileIndex in folder '''
 
        filenameList = []
        for filename in os.listdir(dataPath + "observations/"):
            if filename[-3:] != 'npy':continue
            filenameList.append(filename)

        fileIndex = len(filenameList)
        
        ''' loop over all pitch collections '''
        for pitchCollection in self.explainedPitchCollectionList:
            ''' loop over all analyzed pitches '''
            for analyzedPitch in pitchCollection.analyzedPitchList:
                
                ''' get observation list '''
                observationList = self.getObservationsForElementId(analyzedPitch.id, 5, pitchCollection.verticality.offset)
                # fileObservations.write(observationString)
        
                ''' store label in file_2'''
                labelString = analyzedPitch.concept  # + '\t' + analyzedPitch.pitchSubType
                if labelString not in labelDictionary:
                    print ("Wrong label...skip: " + str(labelString))
                    continue
                
                # fileLabel.write(labelString)
        
                ''' store id in file_3 ''' 
                if analyzedPitch.id == None or pitchCollection.verticality.offset == None:
                    print ("ID or Offset not identified... skip")
                    continue 
                idString = str(analyzedPitch.id) + '; ' + str(pitchCollection.verticality.offset)
                # fileId.write(idString)
                
                
            
                np.save(dataPath + '/observations/' + str(fileIndex).zfill(7), np.array(observationList), True, False)
                np.save( dataPath + '/labels/' + str(fileIndex).zfill(7), np.array(labelDictionary[labelString]), True, False)
                np.save(dataPath + '/ids/' + str(fileIndex).zfill(7), np.array(idString), True, False)
                
               # print ("Observation %s set" % (fileIndex))
                
                # fileObservations.close()
                # fileLabel.close()
                # fileId.close()
                
                fileIndex = fileIndex + 1
    
    
    
    def setVerticalityObservations (self, observationsDirectory):
        import numpy as np
        import os
        
        ''' get highest fileIndex in folder '''
 
        filenameList = []
        
        for filename in os.listdir(observationsDirectory + "/observations"):
            if filename[-3:] != 'npy':continue
            filenameList.append(filename)

        fileIndex = len(filenameList)
        
        ''' loop over all pitch collections '''
        for pitchCollection in self.explainedPitchCollectionList: 
                
            ''' get observation list '''
            observationList = self.getObservationsForVerticality(pitchCollection.verticality, 5)
            
             
            # fileObservations.write(observationString)
    
            ''' store label in file_2'''
            rootPitch = pitchCollection.rootPitch
            if not isinstance(rootPitch, pitch.Pitch):
                print ("Wrong label...skip: " + str(rootPitch))
                continue
            else:
                rootPitchName = rootPitch.name
            # fileLabel.write(labelString)
    
            #''' store id in file_3 ''' 
            #if pitchCollection.id == None or pitchCollection.verticality.offset == None:
            #    print ("ID or Offset not identified... skip")
            #    continue 
            #idString = pitchCollection.id + '; ' + str(pitchCollection.verticality.offset)
            # fileId.write(idString)
            
            ''' put everything in numpy array'''
            thisdict = {"C-":0, "C":1, "C#":2,"C##":2, "D-":3, "D":4, "D#":5, "E--":6, "E-":6, "E":7, "E#":8, "F-":9, "F":10, "F#":11, "F##":11, "G-":12, "G":13, "G#":14, "A-":15, "A":16, "A#":17, "B--": 18, "B-":18, "B":19, "B#":20}
            idString = str(pitchCollection.rootPitch) + '; ' + str(pitchCollection.verticality.offset)
        
            
            np.save(observationsDirectory + "/observations/" + str(fileIndex).zfill(9), np.array(observationList), True, False)
            np.save(observationsDirectory + "/labels/" + str(fileIndex).zfill(9), np.array(thisdict[rootPitchName]), True, False)
            np.save(observationsDirectory + "/ids/" + str(fileIndex).zfill(9), np.array(idString), True, False)
            
            #print ("Observation %s set" % (fileIndex))
            
            # fileObservations.close()
            # fileLabel.close()
            # fileId.close()
            
            fileIndex = fileIndex + 1
    
    
    
    def loadXMLAnalysis (self, xmlString):
        
        'extracts information about pitch colls and analysed pitches from XML'
        import xml.etree.ElementTree as ET
        tree = ET.fromstring(xmlString)
        
        ''' pitch colls '''
         
        ''' 1. loop over pitch colls '''
        for pitchCollection in self.explainedPitchCollectionList:
            
            ''' get node corresponding to pitch coll '''
            nodeList = tree.findall(".//pitchColl[@offset='%s']" % (pitchCollection.verticality.offset))
            if len(nodeList) == 0: continue
            
            print (nodeList[0].attrib["root"])
            
            if nodeList[0].attrib["root"] in ['*', '', 'None', ' ']:
                pitchCollection.rootPitch = None
            else:
                pitchCollection.rootPitch = pitch.Pitch(nodeList[0].attrib["root"])
        
        ''' 2. analyzed pitches '''
        
        analyzedPitchList = self.getAnalyzedPitches()
        
        ''' loop over analyzed pitches '''
        for analyzedPitch in analyzedPitchList:
            
            ''' get node corresponding to analyzed pitch ''' 
            nodeList = tree.findall(".//*[@id='%s']" % (analyzedPitch.id))
            node = None
            for element in nodeList:
                if element.attrib["offset"] == str(analyzedPitch.offset): 
                    node = element
                    break
            
            ''' update analyzedPitch information '''
            if node == None: continue
            
            ''' check if anything has changed '''
            changed = False
            
            if str (analyzedPitch.pitchType) != node.attrib["pitchType"] or \
            str (analyzedPitch.pitchSubType) != node.attrib["pitchSubType"] or \
            str (analyzedPitch.explained) != node.attrib["explained"]  or \
            str (analyzedPitch.hypothesesChecked) != node.attrib["hypothesesChecked"] or \
            str (analyzedPitch.probability) != float (node.attrib["probability"]) or \
            str(analyzedPitch.preparationPitchID) != node.attrib["preparationPitchID"] or \
            str(analyzedPitch.resolutionPitchID) != node.attrib["resolutionPitchID"] or \
            str(analyzedPitch.preparationOffset) != node.attrib["preparationOffset"] or \
            str(analyzedPitch.resolutionOffset) != node.attrib["resolutionOffset"] :
                analyzedPitch.preparationPitchID = node.attrib["preparationPitchID"]
                analyzedPitch.resolutionPitchID = node.attrib["resolutionPitchID"]
                # analyzedPitch.preparationOffset = float (node.attrib["preparationOffset"]) if node.attrib["preparationOffset"] != 'None' else None
                # analyzedPitch.resolutionOffset = float (node.attrib["resolutionOffset"]) if node.attrib["resolutionOffset"] != 'None' else None
                changed = True
                
            analyzedPitch.pitchType = node.attrib["pitchType"]
            analyzedPitch.pitchSubType = node.attrib["pitchSubType"]
            analyzedPitch.explained = False if node.attrib["explained"] == 'False' else True
            analyzedPitch.hypothesesChecked = False if node.attrib["hypothesesChecked"] == 'False' else True 
            analyzedPitch.probability = float (node.attrib["probability"])
            
            ''' if changes find preparation and resolution pitches'''  
            if changed == False: continue        
            
            ''' recreate horizontalities and verticalities if dissonance, else None values '''
            
            if analyzedPitch.pitchType != 'CN':
                pass
                # analyzedPitch.preparationPitch = self.getAnalyzedPitchCorrespondingToId (analyzedPitch.preparationPitchID, analyzedPitch.preparationOffset)[0]
                # analyzedPitch.resolutionPitch = self.getAnalyzedPitchCorrespondingToId (analyzedPitch.preparationPitchID, analyzedPitch.resolutionOffset)[0]  
                
                # analyzedPitch.verticalities = VerticalitySequence([analyzedPitch.preparationPitch.verticalities[0], analyzedPitch.verticalities[0], analyzedPitch.resolutionPitch.verticalities[0] ])
                # horizontalities = self.scoreTree.unwrapVerticalities(analyzedPitch.verticalities)
                # analyzedPitch.horizontalities = self._getHorizontalityContainingPitch (self, analyzedPitch.pitch, horizontalities)
                
            else:
                analyzedPitch.verticalities = VerticalitySequence([None, analyzedPitch.verticalities[1], None ])
                analyzedPitch.horizontalities = None
                analyzedPitch.preparationOffset = None
                analyzedPitch.preparationPitchID = None
                analyzedPitch.resolutionOffset = None
                analyzedPitch.resolutionPitchID = None 
                analyzedPitch.probability = 1.0
    
    def setIdDictionary (self):
        'sets number of analytical subdivisions of the element (chord or note) the analytical pitch belongs to'
        
        ''' loop over all pitches '''
        analyzedPitchList = self.getAnalyzedPitches()
        for analyzedPitch in analyzedPitchList:
            ''' test if entry exists in idDictionary if so '''
            if not analyzedPitch.id in self.idDictionary:  
                ''' get sublist of analyzed pitches which share the same id (i.e. which are part of the same note / chord )'''
                subList = self.getAnalyzedPitches(analyzedPitch.id)        
                self.idDictionary.update({analyzedPitch.id: subList})
    def getObservationsForVerticality(self, verticality, context = 5):
        ''' build list of list and fill everything with 0'''
        offset = verticality.offset
        verticalityList = []
        contextList = []
        
        note2NumDic =  {"C-":0, "C":1, "C#":2, "C##":2, "D-":3, "D":4, "D#":5, "E--":6,  "E-":6, "E":7, "E#":8, "F-":9, "F":10, "F#":11, "F##":11, "G-":12, "G":13, "G#":14, "A-":15, "A":16, "A#":17, "B--": 18,  "B-":18, "B":19, "B#":20}
        
        
        observationList = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        
        for unused_counter in range (0, 21):
            verticalityList.append(deepcopy(observationList))     
        
        for unused_counter in range (0, context * 2 + 1):
            contextList.append(deepcopy(verticalityList)) 
            
        ''' create pitchCollList i.e. context before and after reference offset'''
        pitchCollectionList = self.getPitchCollectionContext(offset, context)
        
        ''' loop over pitch colls '''
        for index in range (0, len(pitchCollectionList)):
            pitchCollection = pitchCollectionList[index]
            
            if pitchCollection == None:  continue  # in that case all values remain zero 
            if pitchCollection.verticality == None: continue # in that case all values remain zero 
            
            deepestPitchClass = pitchCollection.getBassPitch().name  # get deepest pitch class
            
            ''' loop over every analyzed pitch '''
            for analyzedPitch in pitchCollection.analyzedPitchList:
                ''' get diatonic step'''
                chromaticStep =note2NumDic[analyzedPitch.pitch.name]
                
                # print ("Observed pitch (0): %s, transposition interval: %s, current pitch: %s, transposition: %s, diatonic step: %s, alteration: %s " %(observedPitch[0].pitch, transpositionInterval, analyzedPitch.pitch.nameWithOctave, transposedPitch.nameWithOctave, diatonicStep, transposedPitch.alter))
                
                
                ''' fill list with dimension at corresponding position '''
                    
                ''' 1. chromatic pitch class '''
                contextList[index][chromaticStep][0] = 1  
                
                ''' 2. deepest pitch class '''   
                if deepestPitchClass == analyzedPitch.pitch.name: 
                    contextList[index][chromaticStep][1] = 1 
                
                
                
                ''' 3. duration '''
                contextList[index][chromaticStep][2] = pitchCollection.duration
                
                ''' 4. beat strength '''
                contextList[index][chromaticStep][3] = pitchCollection.verticality.beatStrength 
                
                ''' 5. attack '''
                contextList[index][chromaticStep][4] = 1 if analyzedPitch.attack == True else 0
                
                ''' 6. occurrence '''
                contextList[index][chromaticStep][5] = contextList[index][chromaticStep][5] + 1 
                
                ''' 7. dissonancePattern ''' 
                if hasattr(analyzedPitch, "pitchType"):
                    if analyzedPitch.pitchType == "CN" : contextList[index][chromaticStep][6] =1
                
                '''8 octave location (octaves 0 to 10) '''
                contextList[index][chromaticStep][7 + analyzedPitch.pitch.octave] = contextList[index][chromaticStep][7 + analyzedPitch.pitch.octave] + 1
                
        
        
       
        
        return contextList 
    
    def getObservationsForPitchIdChromatic(self, analyzedPitchId, context=5, offset=0):
        
        ''' build list of list and fill everything with 0'''
        pitchList = []
        contextList = []
        
      
            
            
            
        note2NumDic =  {"C-":0, "C":1, "C#":2, "C##":2, "D-":3, "D":4, "D#":5, "E--":6,  "E-":6, "E":7, "E#":8, "F-":9, "F":10, "F#":11, "F##":11, "G-":12, "G":13, "G#":14, "A-":15, "A":16, "A#":17, "B--": 18,  "B-":18, "B":19, "B#":20}
        
        
        observationList = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0] # 18 criteria
        
        for unused_counter in range (0, 21):
            pitchList.append(deepcopy(observationList))     
        
        for unused_counter in range (0, context * 2 + 1):
            contextList.append(deepcopy(pitchList))     
        
        
        ''' get transposition interval '''
        observedPitch = self.getAnalyzedPitchCorrespondingToId(analyzedPitchId, offset)
        transpositionInterval = interval.Interval(noteStart=observedPitch[0].pitch, noteEnd=pitch.Pitch('C4'))  # # reference is arbitrarily set to 'C4' could be any pitch 
        
         
        # print ('Reference pitch: ' + observedPitch[0].pitch.step + ", diatonic number: " + str(pitchDiatonicNumber) + ", diatonic vector: " + str (diatonicVector))
        
        ''' create pitchCollList i.e. context before and after reference offset'''
        pitchCollectionList = self.getPitchCollectionContext(offset, context)
        
        ''' loop over pitch colls '''
        for index in range (0, len(pitchCollectionList)):
            pitchCollection = pitchCollectionList[index]
            
            if pitchCollection == None: continue  # in that case all values remain zero
            if len(pitchCollection.analyzedPitchList) == 0: continue 
             
            
            deepestPitchClass = pitchCollection.getBassPitch().name  # get deepest pitch class
            
            ''' loop over every analyzed pitch '''
            for analyzedPitch in pitchCollection.analyzedPitchList:
                if analyzedPitch.pitch == None:
                    continue 
                
                
                ''' transpose pitch '''
                transpositionInterval.noteStart = note.Note(analyzedPitch.pitch.nameWithOctave)
                transposedPitch = transpositionInterval.noteEnd.pitch
                
                
                chromaticStep =note2NumDic[transposedPitch.name]
                
               
                
                #print ("Observed pitch (0): %s, transposition interval: %s, current pitch: %s, transposition: %s, diatonic step: %s, alteration: %s " %(observedPitch[0].pitch, transpositionInterval, analyzedPitch.pitch.nameWithOctave, transposedPitch.nameWithOctave, diatonicStep, transposedPitch.alter))
                
                ''' fill list with dimension at corresponding position '''
                    
                ''' 1.  chromatic steps '''
                contextList[index][chromaticStep][0] = 1 
                
                ''' 2. deepest pitch  '''   
                contextList[index][chromaticStep][1] = 1 if deepestPitchClass == analyzedPitch.pitch.name else 0
                
          
                
                ''' 3. duration '''
                contextList[index][chromaticStep][2] = pitchCollection.duration
                
                ''' 4. beat strength '''
                contextList[index][chromaticStep][3] =  pitchCollection.beatStrength 
                
                ''' 5. attack '''
                contextList[index][chromaticStep][4] = 1 if analyzedPitch.attack == True else 0
                
                ''' 6. occurrence '''
                contextList[index][chromaticStep][5] = contextList[index][chromaticStep][6] + 1 
                
                ''' 7. same voice - part as reference pitch ''' 
                if contextList[index][chromaticStep][6] == 0:  # the diatonic step may be instantiated by another pitch. If result is positive, leave it like this
                    if analyzedPitch.part == observedPitch[0].part and analyzedPitch.voice == observedPitch[0].voice:
                        contextList[index][chromaticStep][6] = 1 
                    else: 0 
                    
                '''8-18 octave location (octaves 0 to 10) '''
                contextList[index][chromaticStep][7 + analyzedPitch.pitch.octave] = contextList[index][chromaticStep][7 + analyzedPitch.pitch.octave] + 1
                
            
            
        return contextList   
    
    
    def getObservationsForElementId(self, analyzedPitchId, context=5, offset=0):
        ''' get transposition interval '''
        observedPitch = self.getAnalyzedPitchCorrespondingToId(analyzedPitchId, offset)[0]
        
        
      
        ''' create dics '''    
        note2NumDic =  {"C-":0, "C":1, "C#":2, "C##":2, "D-":3, "D":4, "D#":5, "E--":6,  "E-":6, "E":7, "E#":8, "F-":9, "F":10, "F#":11, "F##":11, "G-":12, "G":13, "G#":14, "A-":15, "A":16, "A#":17, "B--": 18,  "B-":18, "B":19, "B#":20, None: 21}
        
        
        partVoice2NumDic = {}
        #by default, the observed elmnt's part is 0, other parts are numbered from bottom to top, 
        #if more than 4 voices, put the rest on voice 5.  
        #if silence, use last free position before 5
        referencePitchColl = self.getAnalyzedPitchCollectionAtOffset(offset)
        pitchList = []
        silenceSubList = []
        
        for analyedPitch in referencePitchColl.analyzedPitchList:
            if analyedPitch.pitch != None:
                pitchList.append(analyedPitch)
            else:
                silenceSubList.append(analyedPitch)
                
        
        pitchList = sorted(pitchList, key=lambda x: (x.pitch.ps, x.part.partName))
        pitchList = pitchList + silenceSubList
        partVoice2NumDic [observedPitch.part.id + "_" + observedPitch.voice.id] = 0
        
        partVoiceIndex = 1
        
        for pitch in pitchList:
            if pitch == observedPitch: continue
            if partVoiceIndex <= 3:
                partVoice2NumDic [pitch.part.id + "_" + pitch.voice.id] = partVoiceIndex
            else:
                partVoice2NumDic [pitch.part.id + "_" + pitch.voice.id] = 4
            partVoiceIndex = partVoiceIndex + 1 
        partVoice2NumDic ["other"] = 4
            
      
        
        ''' build list of lists and fill everything with 0'''
        observationList = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0] # 17 criteria
        pitchList = []
        partList = []
        contextList = []    
        
        for unused_counter in range (0, 22):
            pitchList.append(deepcopy(observationList))    
            
        for unused_counter in range (0, 5):
            partList.append(deepcopy(pitchList))   
        
        for unused_counter in range (0, context * 2 + 1): # context
            contextList.append(deepcopy(partList))  
            
        
        
        
        
        
         
        # print ('Reference pitch: ' + observedPitch[0].pitch.step + ", diatonic number: " + str(pitchDiatonicNumber) + ", diatonic vector: " + str (diatonicVector))
        
        ''' create pitchCollList i.e. context before and after reference offset'''
        pitchCollectionList = self.getPitchCollectionContext(offset, context)
        
        ''' loop over pitch colls '''
        for index in range (0, len(pitchCollectionList)):
            pitchCollection = pitchCollectionList[index]
            
            if pitchCollection == None: continue  # in that case all values remain zero
            if len(pitchCollection.analyzedPitchList) == 0: continue 
             
            
            deepestPitchClass = pitchCollection.getBassPitch()
            
            if deepestPitchClass != None: deepestPitchClass = deepestPitchClass.name  # get deepest pitch class
            
            ''' loop over every analyzed pitch '''
            for analyzedPitch in pitchCollection.analyzedPitchList:
                if analyzedPitch.pitch == None:
                    continue 
                

                
                chromaticStep =note2NumDic[analyzedPitch.pitch.name]
                partVoiceIndex = partVoice2NumDic[analyzedPitch.part.id + "_" + analyzedPitch.voice.id]
                
               
                
                #print ("Observed pitch (0): %s, transposition interval: %s, current pitch: %s, transposition: %s, diatonic step: %s, alteration: %s " %(observedPitch[0].pitch, transpositionInterval, analyzedPitch.pitch.nameWithOctave, transposedPitch.nameWithOctave, diatonicStep, transposedPitch.alter))
                
                ''' fill list with dimension at corresponding position '''
                    
                ''' 1.  chromatic steps '''
                contextList[index][partVoiceIndex][chromaticStep][0] = 1 
                
                ''' 2. deepest pitch  '''   
                if analyzedPitch.pitch != None and deepestPitchClass != None:
                    contextList[index][partVoiceIndex][chromaticStep][1] = 1 if deepestPitchClass == analyzedPitch.pitch.name else 0          

                ''' 3. duration '''
                contextList[index][partVoiceIndex][chromaticStep][2] = pitchCollection.duration
                
                ''' 4. beat strength '''
                contextList[index][partVoiceIndex][chromaticStep][3] =  pitchCollection.beatStrength 
                
                ''' 5. attack '''
                contextList[index][partVoiceIndex][chromaticStep][4] = 1 if analyzedPitch.attack == True else 0
                
                ''' 6. occurrence '''
                contextList[index][partVoiceIndex][chromaticStep][5] = contextList[index][partVoiceIndex][chromaticStep][5] + 1 
                    
                '''7-17 octave location (octaves 0 to 10) '''
                if analyzedPitch.pitch != None:
                    contextList[index][partVoiceIndex][chromaticStep][6 + analyzedPitch.pitch.octave] = contextList[index][partVoiceIndex][chromaticStep][6 + analyzedPitch.pitch.octave] + 1
                
                 
            
            
        return contextList               
    
    
    def getObservationsForPitchId(self, analyzedPitchId, context=5, offset=0):
        
        ''' build list of list and fill everything with 0'''
        pitchList = []
        contextList = []
        
        observationList = [0, 0, 0, 0, 0, 0, 0, 0]
        
        for unused_counter in range (0, 7):
            pitchList.append(deepcopy(observationList))     
        
        for unused_counter in range (0, context * 2 + 1):
            contextList.append(deepcopy(pitchList)) 
        
        ''' get transposition interval '''
        observedPitch = self.getAnalyzedPitchCorrespondingToId(analyzedPitchId, offset)
        transpositionInterval = interval.Interval(noteStart=observedPitch[0].pitch, noteEnd=pitch.Pitch('C4'))  # # reference is arbitrarily set to 'C4' could be any pitch 
        
        # print ('Reference pitch: ' + observedPitch[0].pitch.step + ", diatonic number: " + str(pitchDiatonicNumber) + ", diatonic vector: " + str (diatonicVector))
        
        ''' create pitchCollList i.e. context before and after reference offset'''
        pitchCollectionList = self.getPitchCollectionContext(offset, context)
        
        ''' loop over pitch colls '''
        for index in range (0, len(pitchCollectionList)):
            pitchCollection = pitchCollectionList[index]
            
            if pitchCollection == None: continue  # in that case all values remain zero
            deepestPitchClass = pitchCollection.bass.step  # get deepest pitch class
            
            ''' loop over every analyzed pitch '''
            for analyzedPitch in pitchCollection.analyzedPitchList:
                
                ''' transpose pitch '''
                transpositionInterval.noteStart = note.Note(analyzedPitch.pitch.nameWithOctave)
                transposedPitch = transpositionInterval.noteEnd.pitch
                
                ''' get diatonic step'''
                diatonicStep = (transposedPitch.diatonicNoteNum - 1) % 7
                
                # print ("Observed pitch (0): %s, transposition interval: %s, current pitch: %s, transposition: %s, diatonic step: %s, alteration: %s " %(observedPitch[0].pitch, transpositionInterval, analyzedPitch.pitch.nameWithOctave, transposedPitch.nameWithOctave, diatonicStep, transposedPitch.alter))
                
                ''' fill list with dimension at corresponding position '''
                    
                ''' 1. vectorized diatonic steps '''
                contextList[index][diatonicStep][0] = 1 
                
                ''' 2. alteration '''
                contextList[index][diatonicStep][1] = transposedPitch.alter
                
                ''' 3. deepest pitch  '''   
                contextList[index][diatonicStep][2] = 1 if deepestPitchClass == analyzedPitch.pitch.step else 0
                
                ''' 4. duration '''
                contextList[index][diatonicStep][3] = pitchCollection.duration
                
                ''' 5. beat strength '''
                contextList[index][diatonicStep][4] = pitchCollection.beatStrength 
                
                ''' 6. attack '''
                contextList[index][diatonicStep][5] = 1 if analyzedPitch.attack == True else 0
                
                ''' 7. occurrence '''
                contextList[index][diatonicStep][6] = contextList[index][diatonicStep][6] + 1 
                
                ''' 8. same voice - part as reference pitch ''' 
                if contextList[index][diatonicStep][7] == 0:  # the diatonic step may be instantiated by another pitch. If result is positive, leave it like this
                    if analyzedPitch.part == observedPitch[0].part and analyzedPitch.voice == observedPitch[0].voice:
                        contextList[index][diatonicStep][7] = 1 
                    else: 0 
            
        return contextList         
    
    
    def getXMLRepresentation(self):
        ''' creates an xml representation of analytical information of pitch colls and analysed pitches ''' 
        
        ''' populate id dictionary '''
        self.setIdDictionary()
        
        xmlSequence = "<root>"
        
        for pitchCollection in self.explainedPitchCollectionList:
            xmlSequence = xmlSequence + '<pitchColl offset="%s" root="%s">' % (pitchCollection.verticality.offset, pitchCollection.rootPitch)
            
            for analyzedPitch in pitchCollection.analyzedPitchList:
                
                xmlSequence = xmlSequence + '<analyzedPitch accentuated="%s" pitchType="%s" pitchSubType="%s" offset="%s" pitch="%s" probability="%s" preparationPitchID="%s" preparationOffset="%s" resolutionPitchID="%s" resolutionOffset="%s" explained="%s" hypothesesChecked="%s" id="%s" analyticalDivisions="%s"/>' % (analyzedPitch.accentuated, analyzedPitch.pitchType, "", analyzedPitch.offset, analyzedPitch.pitch, analyzedPitch.probability, analyzedPitch.preparationPitchID, analyzedPitch.preparationOffset, analyzedPitch.resolutionPitchID, analyzedPitch.resolutionOffset, analyzedPitch.explained, analyzedPitch.hypothesesChecked, analyzedPitch.id, len (self.idDictionary[analyzedPitch.id]))
            
            xmlSequence = xmlSequence + '</pitchColl>'
            
        xmlSequence = xmlSequence + "</root>"
            
        return xmlSequence    
    
    

    
    def setAnnotationsToStream_Expressions(self):
        
        ''' this is used to add analytical information stored in pitch colls to the stream '''
        
        ''' loop over analyzed pitches '''
        
        for analysedPitch in self.getAnalyzedPitches():
            if analysedPitch.pitchType != None:
            
                te = expressions.TextExpression(str(analysedPitch.pitchType))
                
                for measure in analysedPitch.part.getElementsByClass(stream.Measure):
                    if analysedPitch.offset >= measure.offset and analysedPitch.offset <= measure.offset + measure.highestOffset:
                        measure.insert(analysedPitch.offset-measure.offset, te)
                        break
        
            
          
        
        ''' select part '''
            
        
        
        
        
    
    
    def setRootsFromStream(self, stream):
        
        flatRootSream = stream.flat
        
        for pitchColl in self.explainedPitchCollectionList:    
            if pitchColl.verticality == None: 
                continue
                
            
            rootNote = flatRootSream.getElementAtOrBefore(pitchColl.offset, note.Note)
            if rootNote ==None: continue
            pitchColl.rootPitch = rootNote.pitch
     
    def setRootsFromPart (self, partName): 
        
        for pitchColl in self.explainedPitchCollectionList:    
            if pitchColl.verticality == None: 
                continue
            
            for analyzedPitch in pitchColl.analyzedPitchList:
                
                if analyzedPitch.part.partName == partName:
                    pitchColl.rootPitch = analyzedPitch.pitch
                    continue
                
        
        
            
    def setSectionStartAndEndTimes (self, pitchCollList):
        ''' identify structural elements i.e.  fermata, a double bar, a final bar etc. endtimes  '''
        self.endTimeList = self.getSectionEndTimes()
        collLength = len (pitchCollList)
         
        for counter, pitchColl in enumerate(pitchCollList):
            if counter == 0: 
                pitchColl.isSectionStart = True
            
            
            if pitchColl.endTime in self.endTimeList:
                pitchColl.isSectionEnd = True
                
                if counter + 1 < collLength:
                    pitchCollList[counter +1].isSectionStart = True
                
            
                
                 
        return pitchCollList
    
                
            
            
    
    def showStatistics (self, timeElapsed):
        ''' get analyzed pitches '''
        analyzedPitchList = self.getAnalyzedPitches()
        
        explainedPitches = 0
        #=======================================================================
        unexplainedPitches = 0
        remainingHypotheses = 0
        # 
        for analyzedPitch in analyzedPitchList:
        #     
            if analyzedPitch.explained: 
                explainedPitches = explainedPitches + 1 
        #         
        #     
            else:
                unexplainedPitches = unexplainedPitches + 1
                analyzedPitch.setBestHypothesis()
                remainingHypotheses = remainingHypotheses + len (analyzedPitch.hypothesisList) 
        #=======================================================================
                
        # logging.info ('Explained pitches: ' + str( round (explainedPitches/len (analyzedPitchList)*100,2)) + '% (' + str (explainedPitches) + ')'  + ', unexplained pitches: '  + str(round (unexplainedPitches/len (analyzedPitchList)*100,2)) + '%(' + str (unexplainedPitches) + ')'  + " unresolved hypotheses :" + str(remainingHypotheses)  )
 
        self.setExplanationRatio()
        self.setIncoherenceRatio() 
        
        logging.info ('Explanation ratio: ' + str(round(self.explanationRatioList[-1], 2)) + ', incoherence ratio: ' + str(round(self.incoherenceRatioList[-1], 2)) + ", probability: " + str(round(self.probabilityRatioList[-1], 2)) + ", unresolved hypotheses :" + str(remainingHypotheses) + " Call id: " + str(self.callId) + " Time elapsed: " + str(timeElapsed))
    
    def unexplainedPitches (self):
        ''' TODO merge with getUnexplainedPitches '''
        unexplainedPitchList = []
        for pitchCollection in self.explainedPitchCollectionList:
            unexplainedPitchList = unexplainedPitchList + pitchCollection.unexplainedPitches()
        return unexplainedPitchList           
    
    def _atLeastOnePitchClassIsCommon (self, verticality1, verticality2, excludePitches=[]):
        for pitchV1 in verticality1.pitchSet:
            if pitchV1 not in excludePitches: 
                for pitchV2 in verticality2.pitchSet:
                    if pitchV1.pitchClass == pitchV2.pitchClass:
                        return True
         
        return False
    
    def _atLeastOnePitchisNotParsimonious (self, verticality1, verticality2, excludePitchesV2=[]):
        ''' build full verticality sequence '''
 
        verticalityList = []
        verticality = verticality1
        
        while verticality.offset <= verticality2.offset :
            verticalityList.append(verticality)
            verticality = verticality.nextVerticality
 
        ''' iterate pairwise over verticalities '''
        
        for verticality1, verticality2 in self._pairwise (verticalityList):
            ''' remove excluded pitches from v1 v2 ''' 
            V1num = []
            filteredV2num = []
            
            for pitch in  verticality1.pitchSet:
                V1num.append(pitch.diatonicNoteNum)
                
            for pitch in verticality2.pitchSet:
                if pitch not in excludePitchesV2: filteredV2num.append(pitch.diatonicNoteNum)
            
            ''' test that the pitches of v1 either remain in v2 or progress by step upwards or downwards ''' 
            for diatonicNoteNum in filteredV2num:
                pitchNumStepUp = diatonicNoteNum + 1
                pitchNumStepDown = diatonicNoteNum - 1 
                if diatonicNoteNum not in V1num and pitchNumStepUp not in V1num and pitchNumStepDown not in V1num:
                    return True  
        return False 
    
    def _elementListContainsPitch (self, elementList, pitch):
        for element in elementList :
            if not isinstance(element, note.Note): continue
            if element.pitch.nameWithOctave == pitch.nameWithOctave:  
                return True
        return False
    
    def _getAnalyzedContext (self, pitchList, verticalityList):
            analyzedContext = []
            
            for x in range (len (pitchList)):
                element = pitchList[x]
                if isinstance(element, pitch.Pitch):
                    verticality = verticalityList[x] 
                    if verticality != None:
                        offset = verticality.offset
                    else: offset = None
                    elementList = self.getAnalyzedPitchCorrespondingToId(element.id, offset)
                    if len (elementList) > 0:
                        analyzedContext.append(elementList[0])
                    else: analyzedContext.append(None)
                    
                else: analyzedContext.append(None)
            return analyzedContext
    
    def _getCompletePitchList(self, horizontality, verticalities):
        ''' returns pitchList organized as follows: [[v0 and elaborations][v1][elaborations v2] '''
        
        V0AndElaborations = []
        V1 = []
        ElaborationsAndV2 = []
        
        ''' V0AndElaborations '''
        verticality = verticalities[0] 
        while verticality.offset < verticalities[1].offset:
            V0AndElaborations.append(self._getPitchAtOffSetFromHorizontality(horizontality, verticality.offset))
            verticality = verticality.nextVerticality
            if verticality == None : break
            
        ''' V1 '''
        verticality = verticalities[1] 
        V1.append(self._getPitchAtOffSetFromHorizontality(horizontality, verticality.offset))
        
        ''' ElaborationsAndV2 '''
        verticality = verticalities[1].nextVerticality
        
        while verticality.offset <= verticalities[2].offset:
            ElaborationsAndV2.append(self._getPitchAtOffSetFromHorizontality(horizontality, verticality.offset))
            verticality = verticality.nextVerticality
            if verticality == None : 
                break
       
        return [V0AndElaborations, V1, ElaborationsAndV2]
            
    def _getElementAtOrBeforeInHorizontality (self, horizontality, offset, part=None):
        ''' returns a list of elements at or before offset in horizontality '''
        elementList = []
        timespans = horizontality.timespans
        
        for pitchedTimeSpan in timespans:
            if part != None : 
                if pitchedTimeSpan.part != part: continue
            
            if pitchedTimeSpan.offset == offset:
                elementList.append(pitchedTimeSpan.element)
            elif pitchedTimeSpan.offset < offset and pitchedTimeSpan.endTime > offset:
                elementList.append (pitchedTimeSpan.element)
                
        return elementList
    
    def _getHorizontalityContainingPitch(self, pitchS, horizontalities):
        for unused_part, timespanList in horizontalities.items():
            for elementTimespansCounter in range (0, len(timespanList.timespans)):
                element = timespanList.timespans[elementTimespansCounter].element
                if element.isNote:
                    if  element.pitch == pitchS:
                        return timespanList
                elif element.isChord:
                    if pitchS in element.pitches:
                        return timespanList
    
    def _getHorizontalityList (self, scoreStream):
        ''' returns trigram'''
        horizontalityList = []
        for part in scoreStream.parts:
            ''' loop through parts '''
            pitchList = []
            for element in part.elements:
                 
                if element.isNote:  
                    pitchList.append (element) 
                else:
                    pitchList.append(None)
            horizontalityList.append(pitchList)    
        return horizontalityList
    
    def _getMelodicMovementsFromPitchList (self, pitchList):
        ''' returns melodic movements, expressed as integers ''' 
        movementList = []   
        
        ''' reorganize list: if silences keep previous pitch '''
        formerPitch = pitchList [0]
        for x in range (1, len (pitchList)):
            if pitchList[x] == None: pitchList[x] = formerPitch
            formerPitch = pitchList [x]
        
        ''' iterate pairwise over pitchList '''
        for element1, element2 in self._pairwise (pitchList):
            if isinstance(element1, pitch.Pitch) and isinstance(element2, pitch.Pitch):
                movementList.append (interval.Interval (element1, element2).generic.directed) 
            else:
                movementList.append(0)
        return movementList
    
    def _getMelMovementsFromTimeSpanList(self, timeSpanList):
        movementList = []   
        
        ''' iterate pairwise over timeSpanList '''
        for element1, element2 in self._pairwise (timeSpanList):
            if element1.element.isNote and element2.element.isNote:
                movementList.append (interval.Interval (element1.element.pitch, element2.element.pitch).generic.directed) 
            else:
                movementList.append(0)
        return movementList
    
    def _getMelMovementsList (self, scoreStream):
        ''' returns melodic movements of trigram '''
        if scoreStream == None:
            pass
        
        movementList = []   
        ''' loop through scoreStream '''
        for part in scoreStream.parts:
            ''' loop through parts '''
            movement = []
            for elementCounter in range (0, len (part) - 1):
                element1 = part[elementCounter]
                element2 = part[elementCounter + 1]
                if element1.isNote and element2.isNote:
                    movement.append (interval.Interval (element1.pitch, element2.pitch).generic.directed) 
                else:
                    movement.append(0)
            movementList.append(movement)   
            
        return movementList 
    
    def _getNbOfMelMovements (self, movementList):
        nbOfMovements = 0
        
        for movement in movementList:
            if movement not in [0, 1]:
                nbOfMovements = nbOfMovements + 1
        return nbOfMovements
    
    def _getNormalizedMelStreams(self, verticalities, containsPitch):
        ''' returns a stream with one or many melodic lines corresponding to parts'''
        ''' each line has three notes '''
        ''' get offsetList '''
        
        ''' create offset list '''
        offsetList = []
        for element in verticalities._verticalities:
            offsetList.append(element.offset if element != None else None)
        
        ''' get horizontalities and loop over parts'''
        horizontalities = self.scoreTree.unwrapVerticalities(verticalities)
        scoreStream = stream.Score()
        for unused_part, timespanList in horizontalities.items():
            
            ''' check if pitch in timespanList and if so get pitchedTimeSpan '''
            pitchedTimeSpan = self._getPitchedTimeSpanContainingPitchAtOrBeforeInHorizontality(timespanList, offsetList[1], containsPitch)
            if pitchedTimeSpan == None : continue
           
            ''' check number of elements at v0, v1, v2, if vo or v2 have no elements add rest'''
            elementListV0 = self._getElementAtOrBeforeInHorizontality(timespanList, offsetList[0], pitchedTimeSpan.part)
            elementListV1 = self._getElementAtOrBeforeInHorizontality(timespanList, offsetList[1], pitchedTimeSpan.part)
            elementListV2 = self._getElementAtOrBeforeInHorizontality(timespanList, offsetList[2], pitchedTimeSpan.part)
            
            if len (elementListV0) == 0: elementListV0.append(note.Rest())
            if len (elementListV2) == 0: elementListV2.append(note.Rest())
            
            ''' create streams according to the number of elements '''        
            for elementV0 in elementListV0:
                for elementV1 in elementListV1:
                    for elementV2 in elementListV2:
                        partStream = stream.Part()
                        ''' deep copy '''
                        elementV0dC = copy.deepcopy(elementV0)
                        elementV1dC = copy.deepcopy(elementV1)
                        elementV2dC = copy.deepcopy(elementV2)
                        
                        ''' same durations '''
                        elementV0dC.duration.quarterLength = 1
                        elementV1dC.duration.quarterLength = 1
                        elementV2dC.duration.quarterLength = 1
                        
                        ''' append '''
                        partStream.append(elementV0dC)
                        partStream.append(elementV1dC)
                        partStream.append(elementV2dC) 
                        
                        ''' insert stream '''
                        scoreStream.insert(0, partStream) 
        if len (scoreStream.elements) > 0:
            return scoreStream
        else: 
            return None 

    def _getPitchAtOffSetFromHorizontality(self, horizontality, offset):
        
        for timespan in horizontality.timespans:
            if timespan.offset <= offset and timespan.endTime > offset:
                return timespan.pitches[0]
            
        return None
    
    def _getPitchesFromTimespans (self, timeSpanList):
        pitchList = []
        for timespan in timeSpanList: 
            pitchList.append(timespan.pitch)
            break
    
    def _getPitchedTimeSpanContainingPitchAtOrBeforeInHorizontality (self, horizontality, offset, pitch):
        ''' returns either pitchedTimeSpan in which the pitch appears or none '''
        timespans = horizontality.timespans
        for pitchedTimeSpan in timespans:
            if pitchedTimeSpan.offset == offset:
                if pitchedTimeSpan.element.pitch.nameWithOctave == pitch.nameWithOctave:
                    return pitchedTimeSpan
            elif pitchedTimeSpan.offset < offset and pitchedTimeSpan.endTime > offset:
                if pitchedTimeSpan.element.pitch.nameWithOctave == pitch.nameWithOctave:
                    return pitchedTimeSpan
                
        return None
    
    def _getTimeSpanContainingPitch (self, horizontality, pitch):
        ''' returns either pitchedTimeSpan in which the pitch appears or none '''
        
        timespans = horizontality.timespans
        for pitchedTimeSpan in timespans: 
            if pitchedTimeSpan.element.pitch.id in pitch.referenceIDs:
                return pitchedTimeSpan
        
        return None
    
    def _getTimespanListContainingPitch (self, containsPitch, offsetStart, offsetEnd, withStartOffset, withEndOffset):
        ''' returns the portion of the part between offsetStart and offsetEnd '''
        # from music21.tree.verticality import VerticalitySequence
        
        verticalityList = []
        
        ''' build verticality sequence'''
        verticality = self.scoreTree.getVerticalityAt(offsetStart)
        if withStartOffset == False: verticality = verticality.nextVerticality
        
        while verticality is not None :
            verticalityList.append(verticality)
            verticality = verticality.nextVerticality
            if verticality == None: break
            if withEndOffset:
                if verticality.offset > offsetEnd: break
            else:
                if verticality.offset >= offsetEnd: break
        verticalities = VerticalitySequence(verticalityList)
        
        ''' get horizontalities '''
        horizontalities = self.scoreTree.unwrapVerticalities(verticalities)
        
        for unused_part, timespanList in horizontalities.items():
            ''' check if pitch in timespanList and if so get pitchedTimeSpan '''
            pitchedTimeSpan = self._getTimeSpanContainingPitch(timespanList, containsPitch)
            if pitchedTimeSpan == None : continue
            return timespanList

        return None
    
    def _getVerticalityVector(self, verticality1, verticality2):
        rootV1 = verticality1.toChord().root()
        rootV2 = verticality2.toChord().root()
        
        rootInterval = interval.Interval(rootV1, rootV2)
        
        if rootInterval.generic.simpleUndirected > 4:
            rootInterval = rootInterval.complement
            return rootInterval.generic.directed
        else:
            return rootInterval.generic.directed
    
    def _pitchRemainsDuringTimeSpan (self, pitch, timeSpanList):
        ''' checks if pitch remains at same voice between both verticalities'''
        if timeSpanList == None: return False
        
        for timeSpan in timeSpanList:
            for tsPitch in timeSpan.pitches:
                if tsPitch.name != pitch.name:
                    return False
            
        return True
    
    def _isAccentuated (self, verticalities, chordNb): 
        accentuated = False
        
        if verticalities[1] == None or verticalities[2] == None:
            return None
        
        if verticalities[chordNb].beatStrength > verticalities[chordNb + 1].beatStrength:
            accentuated = True
        return accentuated  
    
    def _pairwise(self, iterable):
        from itertools import tee
    
        a, b = tee(iterable)
        next(b, None)
        return zip(a, b)
    
    def _pitchesAtOffsetinHorizontality(self, horizontality, offset):
        for pitchedTimeSpan in horizontality.timespans:
          
            if offset == pitchedTimeSpan.offset and offset < pitchedTimeSpan.endTime:  # starts at the beginning of span and before endtime
                return pitchedTimeSpan.pitches
            elif offset > pitchedTimeSpan.offset and offset < pitchedTimeSpan.endTime:  # starts after beginning of span
                return pitchedTimeSpan.pitches
        return None
    
    def _pitchIsDissonantAgainstAtLeastOnePitch (self, element, pitch):
        
        if isinstance(element, Verticality):
            chord = element.toChord()
            
        elif isinstance(element, PitchCollection):
            chord = element.toChord
        elif isinstance(element, Chord):
            chord = element
        else: return False
        
        bassPitch = chord.bass()
 
        fourthToBass = self._chordHasIntervalToBass(chord, ['P4', ['A4']])
        pitchBassInterval = interval.Interval (bassPitch, pitch)
        
        if fourthToBass:
            if pitch.name == bassPitch.name or pitchBassInterval.generic.simpleUndirected in [4]: return True 
        
        for pitchV in chord.pitches:
            intervalPV = interval.Interval(pitchV, pitch)
            if intervalPV.generic.simpleUndirected in [2, 7]: return True  
            
        return False
    
    def _pitchIsExplainedAfterOffset(self, analyzedPitch, offset):
        ''' get all analyzed pitches corresponding to id '''
        analyzedPitchList = self.getAnalyzedPitchCorrespondingToId (analyzedPitch.id)
        
        ''' check if analyzed pitch former to offset is explained '''
        for analyzedPitch in analyzedPitchList:
            if analyzedPitch.offset > offset and analyzedPitch.probability == 1:
                return True
        
        return False
    

class PitchCollection():
    ''' class stores and manages information about all pitches collected in a verticality ''' 
    ''' also used to store information of general rest - in that case params offset and duration are requested '''
    
    def __init__(self, verticality=None, analyzedPitchList=[], duration = None, offset = None, measureNumber = None):
        self.id = id(self)
        self.analyzedPitchList = analyzedPitchList # really necessary ? deepcopy(analyzedPitchList)
        self.verticality = verticality
        self.chord = None
        self.rootPitch = None 
        self.isSectionEnd = False
        self.isSectionStart = False
        self.bass = None 
        self.bassScaleDegree = None
        self.bassDiatonicDegree = None
        self.rootDegree = None 
        self.intervalsToBass = []
        self.continuoSigns = [] # very simplified for now
        self.simpleContinuoSigns = []
        
        if hasattr(verticality, "measureNumber"):
            self.measureNumber = verticality.measureNumber
        else: 
            if measureNumber != None:
                self.measureNumber = measureNumber
            
            
    
        #self.romanNumeral = None
        
        if verticality != None:
        
            ''' harmonic information '''
            self.chord = verticality.toChord() 
            self.offset = verticality.offset 
            self.bass = self.chord.bass()
            if math.isnan (verticality.beatStrength):
                print ("Beat strength not identified. Will use 0 value.")
                self.beatStrength = 0
            else:
                self.beatStrength = verticality.beatStrength
            self.measureNumber = verticality.measureNumber
             
             
             
            
            
            
            if self.bass != None:
            
                bassNote = note.Note (self.bass.name)
                bassNote.octave = 0
            
            for vertPitch in verticality.pitchSet:
                vertNote = note.Note(vertPitch.name)
                vertNote.octave = 1
            
                bassNoteInt = interval.Interval(bassNote, vertNote)
                self.intervalsToBass.append(bassNoteInt) 
                
            if verticality.nextVerticality != None:
                self.duration = verticality.nextVerticality.offset - verticality.offset
            else:
                self.duration = verticality.startTimespans[0].quarterLength
        
        else:
            self.duration = duration
            self.offset = offset
            
        if self.offset != None and self.duration != None:
            self.endTime = self.offset + self.duration
            
            
        
   
# alternative encoding does not handle breaks adequately     
#         if verticality != None:
#             shortestEndTime = verticality.startAndOverlapTimespans[0].endTime
#             for element in verticality.startAndOverlapTimespans:
#                 if element.endTime < shortestEndTime: shortestEndTime = element.endTime
#             self.duration = shortestEndTime - verticality.offset
            
            
            
        #else: self.duration = 0
    
    
    
    
    
    def addAnalyzedPitch (self, analyzedPitch):
        self.analyzedPitchList.append(analyzedPitch)
        self.setBestHypotheses()
    
    def clone(self):
        
        clonedPitchList = []
        for analyzedPitch in self.analyzedPitchList:
            clonedPitchList.append(analyzedPitch.clone())
        return PitchCollection(self.verticality, clonedPitchList, self.chordTemplates)
    
    def explainPitches(self):
        explanationString = ""
        for analyzedPitch in self.analyzedPitchList:
            explanationString = explanationString + '%s : %s ' % (str(analyzedPitch.pitch), str (analyzedPitch.pitchType) if analyzedPitch.pitchType != None else 'None')
            if analyzedPitch.probability < 1: explanationString = explanationString + "(" + str(analyzedPitch.probability) + ") "
                
        return explanationString    
    
    
    def getSimpleFilteredContinuoSigns(self):
        hasFourth = "4" in self.simpleContinuoSigns
        hasFifth = "5" in self.simpleContinuoSigns
        hasSixth = "6" in self.simpleContinuoSigns
        hasSecond = "2" in self.simpleContinuoSigns
        hasSeventh = "7" in self.simpleContinuoSigns
         
        ''' doubles '''
        if hasFifth == True and hasSixth == True:
            return "65"
        
        elif hasFourth == True and hasSixth == True:
            return "64"
        
        elif hasSixth == True:
            return "6"
        
        elif hasSecond == True and hasFourth:
            return "24"
        
        elif hasSeventh == True:
            return "7"
        
        else: return ""
        
        
    
    def getAnalyzedPitch (self, pitch):
        for analyzedPitch in self.analyzedPitchList:
            if analyzedPitch.pitch == pitch:
                return analyzedPitch
        return None
    
    def getAnalyzedPiches (self):
        return self.analyzedPitchList
    
    def getAnalyzedPitchFromClass (self, pitch):
        for analyzedPitch in self.analyzedPitchList:
            if analyzedPitch.pitch.name == pitch.name:
                return analyzedPitch
        return False
    
    def getAnalyzedPitchesBeloningToList (self, analyzedpitchList=[]):
        subset = []
        pitchList = []
        
        ''' get pitches from analyzed pitch '''
        for analyzedPitch in analyzedpitchList:
            pitchList.append(analyzedPitch.pitch)
            
        for analyzedPitch in self.analyzedPitchList:
            if analyzedPitch in pitchList:
                subset.append(analyzedPitch)
        
        return subset
    
    def getAnalyzedPitchesCorrespondingToLabels (self, labelList):
        subList = []
        
        for analyzedPitch in self.analyzedPitchList: 
            if analyzedPitch.pitchType in labelList:
                subList.append (analyzedPitch)
                
        return subList
    
    def getAnalyzedPitchesCorrespondingToId (self, elementID):
        for analyzedPitch in  self.analyzedPitchList:
            if analyzedPitch.id == elementID:
                return analyzedPitch
        
        return None
                
    def getAnalyzedPitchesNotBeloningToList (self, analyzedpitchList=[]):
        subset = []
        pitchList = []
        
        ''' get pitches from analyzed pitch '''
        for analyzedPitch in analyzedpitchList:
            pitchList.append(analyzedPitch.pitch)
        
        for analyzedPitch in self.analyzedPitchList:
            if analyzedPitch.pitch not in pitchList:
                subset.append(analyzedPitch)
                
        return subset
    
    def getBassPitch (self):
        if self.verticality == None:
            return None
        return self.verticality.toChord().bass()
    
    def getExplainedPitches (self, pitchTypeList=['CN']):
        pitchList = []
        for analyzedPitch in self.analyzedPitchList:
            if analyzedPitch.pitchType in pitchTypeList:
                pitchList.append(analyzedPitch)
        return pitchList
    
    def getHighestResolutionOffest (self):
        dissonantPitchList = self.getExplainedPitches(['PN', 'NN', 'AN', 'EN', 'SU'])
        highestOffset = 0
        for dissonantPitch in dissonantPitchList:
            if highestOffset < dissonantPitch.verticalities[2].offset:
                highestOffset = dissonantPitch.verticalities[2].offset
        
        return highestOffset
    
    def getHypotheses(self): 
        hypothesisList = []
        for analyzedPitch in self.analyzedPitchList:
            if len (analyzedPitch.hypothesisList) > 0:
                for hypothesis in analyzedPitch.hypothesisList:
                    hypothesisList.append(hypothesis)
        
        return hypothesisList
    
    def isExplained (self):
        for analyzedPitch in self.analyzedPitchList:
            if analyzedPitch.explained == False:
                return False
        
        return True
    
    def isNonHarmonicNote (self, pitch):
        pitchExplanation = self.getAnalyzedPitch(pitch)
         
        if not pitchExplanation == None:
            if pitchExplanation.pitchType in ['PN', 'NN', 'AN', 'EN', 'SU'] and pitchExplanation.probability == 1:
                return True
            else: 
                return False
        else: 
            return False
        
    def toChord (self):
        pitchList = []
        for analyzedPitch in self.analyzedPitchList:
            pitchList.append(analyzedPitch.pitch)
            
        return chord.Chord(pitchList)
       
    def getNumberOfConsonantAndDissonantIntervalsImpliedByPitch (self, pitch):
        consonantIntervals = 0
        dissonantIntervals = 0 
        
        bassPitch = self.verticality.toChord().bass()
        
        for analyzedPitch in self.analyzedPitchList:
            
            intervalPV = interval.Interval(analyzedPitch.pitch, pitch)
            genericUndirected = intervalPV.generic.simpleUndirected
            
            if genericUndirected in [2, 7]: 
                dissonantIntervals = dissonantIntervals + 1
                
            elif genericUndirected in [1, 3, 5, 6, 8]:
                consonantIntervals = consonantIntervals + 1
        
            elif genericUndirected in [4]: 
                if bassPitch.name in [pitch.name, bassPitch] and not intervalPV.simpleName == 'A4':
                    dissonantIntervals = dissonantIntervals + 1
                else: consonantIntervals = consonantIntervals + 1
        
        return [consonantIntervals, dissonantIntervals]
        
    def pitchIsConsonantInCollection (self, incoherentPitch):  
        ''' checks if a pitch labeled as a dissonance could be a consonance i.e - this pitch is consonant against other pitches labeled as consonance '''
        ''' make sure that all pitches are explained '''
        if self.isExplained() == False:
            return False
        
        ''' get consonant pitches '''
        consonantPitches = self.getExplainedPitches(['CN'])
        
        ''' TODO Add conditions for fourth against bass '''
        for consonantPitch in consonantPitches:
            intervalPV = interval.Interval(consonantPitch.pitch, incoherentPitch.pitch)
            if intervalPV.generic.simpleUndirected in [2, 4, 7]: 
                return False  
            
        return True
    
  
    def getIntervalsToRoot (self,rootName):
        self.morphology = []
        
        for analyzedPitch in self.analyzedPitchList:
            p1 = pitch.Pitch(rootName + ("0"))
            inversionInterval = interval.Interval(p1, analyzedPitch.pitch)
            if inversionInterval.simpleName not in self.morphology:
                self.morphology.append(inversionInterval.simpleName)
            
        self.morphology.sort()
        return self.morphology
            
            
            
            
    
    def getInversionInterval(self, rootName):
        realBass = self.getBassPitch() 
        p1 = pitch.Pitch(rootName + ("0"))
        
        self.inversionInterval = interval.Interval(p1, realBass)
        return self.inversionInterval
    
    def verticalityWithDissonanceSubstitutionsIsConsonant (self):
        ''' build chord object which contains substitutions for dissonant notes '''
        pitchList = []
        
        for pitchInVerticality in self.verticality.pitchSet:
            
            if self.isNonHarmonicNote(pitchInVerticality) == False:
                ''' if consonant append '''
                pitchList.append(pitchInVerticality) 
            else:
                ''' if dissonant get substitution '''
                substitutionPitch = self.getSubstitutionForDissonantPitch(self.getAnalyzedPitch(pitchInVerticality))
                if substitutionPitch != None: 
                    pitchList.append(substitutionPitch)
                else:
                    pitchList.append(pitchInVerticality)
                 
        chordWithoutSubstitutions = chord.Chord(pitchList)
        
        if self._chordIsConsonant(chordWithoutSubstitutions):
            return True
        else:
            return False
        
    def verticalityWithoutIdentifiedDissonancesisConsonant (self):
        ''' build chord object which contains only consonant notes '''
        pitchList = []
        
        for analyzedPitch in self.analyzedPitchList:
            if analyzedPitch.explained == True and analyzedPitch.pitchType in ['SU', 'PN', 'EN', 'NN', 'AN']:
                pass
            else: pitchList.append(analyzedPitch.pitch)
        
        chordWithoutNHN = chord.Chord(pitchList)
        
        if self._chordIsConsonant(chordWithoutNHN):
            return True
        else:
            return False
        
    def verticalityWithoutPitchListIsConsonant (self, pitch):
        ''' build chord object which contains all pitches except those in list '''
        remainingPitchList = []
        
        for pitchInVerticality in self.verticality.pitchSet:
            if pitchInVerticality != pitch:
                remainingPitchList.append(pitchInVerticality)
        
        chordWithoutNHN = chord.Chord(remainingPitchList)
         
        if chordWithoutNHN.isConsonant():
            return True
        else:
            return False    
        
    def _chordIsConsonant(self, chord):
        if chord.isConsonant():
            return True
        
        elif chord.isDiminishedTriad():
            return True
        
        elif chord.isAugmentedTriad():
            return True
        
        return False 


class Pitch():
    ''' class stores and manages information about individual pitches'''
    ''' these pitches are grouped in a verticality (class AnalyzedPitchCollection)'''
    
    def __init__(self, pitch=None, verticalities=None, hypothesisList=None):
        #self.horizontalities = None
        #self.elementsStartingList = []
        self.accentuated = None
        self.pitchType = None
        #self.pitchSubType = None
        #self.verticalities = verticalities
        self.offset = verticalities[1].offset if verticalities != None else None
        self.pitch = pitch
        #self.harmonicNote = False
        #self.probability = -1
        self.segmentQuarterLength = 0
        # self.isConsonant = False
        #self.resolutionOffset = None
        #self.preparationOffset = None
        #self.preparationPitch = None
        #self.resolutionPitch = None 
        #self.preparationPitchID = None
        #self.resolutionPitchID = None
        #self.hypothesisList = hypothesisList
        #self.explained = False
        #self.hypothesesChecked = False
        #if len (hypothesisList) > 0:  self.setBestHypothesis()
        self.concept = None
        self.id = None
        self.XMLId = None
        self.part = None
        self.voice = None
        self.work = None
        self.attack = False
        self.verticality = verticalities[1] if verticalities != None else None
        
    def clone (self): 
        analzedPitch = Pitch(self.pitch, self.verticalities, self.hypothesisList)
        analzedPitch.horizontalities = self.horizontalities
        analzedPitch.elementsStartingList = self.elementsStartingList
        analzedPitch.accentuated = self.accentuated
        analzedPitch.pitchType = self.pitchType
        analzedPitch.pitchSubType = self.pitchSubType
        analzedPitch.verticalities = self.verticalities
        analzedPitch.offset = self.offset
        analzedPitch.pitch = self.pitch
        analzedPitch.harmonicNote = self.harmonicNote
        analzedPitch.probability = self.probability
        # analzedPitch.isConsonant = self.isConsonant
        analzedPitch.resolutionOffset = self.resolutionOffset
        analzedPitch.preparationOffset = self.preparationOffset
        analzedPitch.preparationPitch = self.preparationPitch
        analzedPitch.resolutionPitch = self.resolutionPitch 
        analzedPitch.hypothesisList = list (self.hypothesisList)
        analzedPitch.explained = self.explained
        analzedPitch.id = self.id
        analzedPitch.resolutionPitchID = self.resolutionPitchID
        analzedPitch.preparationPitchID = self.preparationPitchID
        return analzedPitch
    
    def getBestHypotheses (self):
        ''' returns list with best hypotheses '''
        bestHypothesisList = []
        
        if len (self.hypothesisList) == 0: return bestHypothesisList
        self.hypothesisList.sort(key=lambda x: x.probability, reverse=True)    
        bestProbability = self.hypothesisList[0].probability
        
        for hypothesis in self.hypothesisList:
            if hypothesis.probability == bestProbability:
                bestHypothesisList.append(hypothesis)
        
        if len (bestHypothesisList) <= 1: return bestHypothesisList 
        
        ''' for every dissonance type get longest distance between v0 and v1 ''' 
        typeHypothesisList = []
        for pitchType in ['PN', 'NN', 'AN', 'EN', 'SU']:
            distanceV0V1 = 0
            typeHypothesis = None
            for hypothesis in bestHypothesisList:
                if hypothesis.pitchType == pitchType:
                    if hypothesis.verticalities[1].offset - hypothesis.verticalities [0].offset >= distanceV0V1: typeHypothesis = hypothesis
            
            if typeHypothesis != None: typeHypothesisList.append(typeHypothesis)
            
        return typeHypothesisList       
            
    def getAnalyzedPitchTimeSpan(self):
        horizontality = self.getHorizontality()
        return horizontality.timespans[1] 
    
    def getConstitutivePitch(self):
        ''' either the resolution pitch either the preparation pitch '''        
        
        if self.pitchType in ['SU']:
            return self.resolutionPitch
        elif self.pitchType in ['PN', 'NN', 'AN', 'EN'] and self.accentuated == True:
            return self.resolutionPitch
        else:
            return self.preparationPitch
    
    def getType (self): 
        return self.nhnType
    
    def isIdenticalWithThisAnalyzedPitch (self, analyzedPitch):  
        ''' test on id and basic analytical information '''
       
        if analyzedPitch.id != self.id: return False
        if analyzedPitch.pitchType != self.pitchType: return False
        if analyzedPitch.pitchSubType != self.pitchSubType: return False   
        if analyzedPitch.probability != self.probability: return False 
         
        return True
 
    def show(self): 
        pitchString = "Offset: " + str(self.verticalities[1].offset) + ", pitch: " + str(self.pitch) + ", type: " + str(self.pitchType) + ", subtype: " + str(self.pitchSubType) + ", probability: " + str(self.probability) 
        
        return pitchString 
    
    def _getPart(self, nhVerticality, pitch):
        allElements = []
        elementContainingPitch = None
         
        for element in nhVerticality.startTimespans:
            allElements.append(element)
            
        for element in nhVerticality.overlapTimespans:
            allElements.append(element)
        
        for element in allElements:
            if element.element.id == self.id: 
                elementContainingPitch = element
                break
        
        ''' get Part '''
        if elementContainingPitch != None: 
            return elementContainingPitch.part
        else:
            return None  
        
    def _getVoice (self, nhVerticality):
        allElements = []
        elementContainingPitch = None
         
        for element in nhVerticality.startTimespans:
            allElements.append(element)
            
        for element in nhVerticality.overlapTimespans:
            allElements.append(element)
        
        for element in allElements:
            if element.element.id == self.id: 
                elementContainingPitch = element
                break
        
        ''' get all parents  '''
        if elementContainingPitch == None: return None
        parents = elementContainingPitch.parentage 
        
        ''' loop over parentage, check if included in voice '''
        for parent in parents:
            if isinstance(parent, stream.Voice):
                return parent
        
        return None
    
    def _getElementsContainingPitch (self, pitch): 
        elementList = []
        allElements = []
        
        
        
        
        for element in self.verticality.startTimespans:
            allElements.append(element.element)
            
        for element in self.verticality.overlapTimespans:
            allElements.append(element.element)
        
        for element in allElements:
            if isinstance(element, note.Note):
                if element.pitch.nameWithOctave == pitch.nameWithOctave:
                    elementList.append(element)
            if isinstance(element, chord.Chord):
                if pitch in element.pitches:
                    elementList.append(element)
        return elementList
    
    def _getId (self):
        
        ''' TODO: best solution: when creating tree, create id which allows to map id '''
        ''' set id ''' 
        if self.verticalities == None:
            return None
        
        elementsContainingPitch = self._getElementsContainingPitch(self.verticalities[1], self.pitch)
        
        for element in elementsContainingPitch:
            if isinstance(element, chord.Chord):continue
            return  element.pitch.id  # change to take chords into account
        return None
    
    def _getVerticalities (self):
        if self.verticalities != None:
            return self.verticalities
        else: 
            bestHyp = self.getBestHypotheses()
            return bestHyp[0].verticalities if bestHyp != None else None
        
