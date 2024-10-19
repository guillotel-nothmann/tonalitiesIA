import os
from music21 import converter, key
from pitchCollections import PitchCollectionSequence
from queries import Queries
from manipulateDataset import ManipulateDataSet


class Observations(object):
    ''' this class is used to produce observations for training the neural network '''
    
    def __init__(self, projectList, conceptList):
        self.projectList = projectList
        self.conceptList = conceptList
        self.conceptDictionary = {None: 0}
        conceptIndex = 1 
        for concept in conceptList:
            self.conceptDictionary[concept]:conceptIndex
            conceptIndex = conceptIndex + 1
        
        q = Queries(self.projectList, self.conceptList)
        bindings = q.processQuery()
        if bindings == None : return
        
        workURI = bindings["results"]["bindings"][0]["scoreURI"]["value"]
        work = converter.parseURL(workURI, forceSource = True)
         
        
        for transposition in ["p1"]: #transpositionList:
            
            ''' create pitch collection object for each transposition '''
            transposedWork = work.transpose(transposition)
            pitchCollSequence = PitchCollectionSequence(transposedWork)
            
            
            for item in bindings["results"]["bindings"]:
                
                pitchCollSequence.addConceptToAnalyzedPitches(item["concepts"]["value"], item["notes"]["value"].split(","))
            
            
            
            #''' generate transpositions to maximize training data '''
            # keyElement = None
            # for element in work.flat.getElementsByClass(key.KeySignature):
            #     keyElement = element
            #     break
            #
            # if keyElement == None:
            #     print ("Corrupted file")
            #     break
            #
            # transpositionList = self.getTranspositionIntervals(keyElement.sharps, 0)
            
            
            # ''' create Cadences object for the stream '''        
            # cadencesObj = Cadences(transposedWork, analysisMode = "voiceAnnotations")
            #
            #
            # ''' add analytical information to pitch coll sequence : is part of cadence, cadence element '''
            #
            # ''' cadence zones '''
            # if cadenceZone == False: 
            #     for annotation in cadencesObj.annotationList:
            #
            #         for element in annotation["elements"]:
            #
            #             for analyzedElement in pitchCollSequence.getAnalyzedPitchCorrespondingToId(element.id):
            #                 analyzedElement.pitchType = annotation["content"]
            #
            # else: 
            #     for cadence in cadencesObj.cadenceList:
            #
            #         ''' get pitchColls corresponding to offsets '''
            #         pitchCollSubSet = pitchCollSequence.getPitchCollectionSubset(cadence.offsetList[0], cadence.offsetList[-1])
            #
            #         for pitchColl in pitchCollSubSet:
            #             for analyzedPitch in pitchColl.analyzedPitchList:
            #                 analyzedPitch.pitchType = "C"
            #
            # ''' set observations for this stream '''
            pitchCollSequence.setPitchObservations("data/", self.conceptDictionary)
    
        manipDataSet = ManipulateDataSet("data/")
        manipDataSet.createMainArrays()
            
        
     
        
        
     
    
    def getTranspositionIntervals (self, sharps=0, maxSharps=0): 
    
    
        if maxSharps == 4:
            keyTranspositionsDictionary = {
            4: ['p1',  'p4', '-M2',  'm3', '-M3', 'm2', '-a4', '-a1',  'd4'], 
            3:['-p4', 'p1', 'p4', '-M2', 'm3', '-M3', 'm2', '-a4', '-a1'], 
            2:['M2', '-p4', 'p1', 'p4', '-M2', 'm3', '-M3', 'm2', '-a4'],
            1:['-m3', 'M2', '-p4', 'p1', 'p4',  '-M2', 'm3', '-M3', 'm2'],
            0:['M3', '-m3', 'M2', '-p4',  'p1', 'p4', '-M2', 'm3', '-M3'],
            -1:['M3', '-m3', 'M2', '-p4', 'p1', 'p4', '-M2', 'm3', '-M3'],
            -2:['a4', '-m2', 'M3', '-m3', 'M2', '-p4', 'p1', 'p4', '-M2'],
            -3:['a1', 'a4',  '-m2',  'M3',  '-m3', 'M2', '-p4', 'p1', 'p4'],
            -4:['-d4', 'a1', 'a4', '-m2', 'M3', '-m3', 'M2', '-p4', 'p1']
            }
            return keyTranspositionsDictionary[sharps]    
        
        else : return ['p1']
        
if __name__ == '__main__':
    pass

projectList = ["1657a5df-0ba3-4673-bf41-e3ffd58ea27c"]
conceptList = ["<https://w3id.org/polifonia/ontology/modal-tonal/Cadences_FilaberGuillotelGurrieri_2023/Simplex>"]

obs = Observations(projectList, conceptList)
print (obs)

