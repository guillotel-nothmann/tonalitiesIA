import os
from music21 import converter, key
from pitchCollections import PitchCollectionSequence
from queries import Queries
from manipulateDataset import ManipulateDataSet
import os
import shutil


class Observations(object):
    ''' this class is used to produce observations for training the neural network '''

    
    def __init__(self, projectList, conceptList):
        self.projectList = projectList
        self.conceptList = conceptList
        self.conceptDictionary = {None: 0}
        conceptIndex = 1 
        for concept in conceptList:
            self.conceptDictionary[concept]=conceptIndex
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

projectList = [
 '1657a5df-0ba3-4673-bf41-e3ffd58ea27c', 
 '1b119899-e76b-4275-b5aa-d752b2b53ead', 
 '5d874e58-d6f8-4b8d-a472-2db834d109d4', 
 'f6e11d7f-c136-468b-87c1-cb5ba25de0ba', 
 'e6b82ba3-b8c2-4405-94e0-584fee0b24b2', 
 'a849e9e8-8c34-41d6-a919-5c0201471eaa', 
 'acb3dcb0-f1b4-4cba-b861-a193cee25ae1', 
 '5e93c8f5-c441-4e28-bb7c-1b5ffef2a16f', 
 '8186b591-0ac6-418b-b9ef-bb1149c7844a', 
 '3de8339e-1368-4789-b819-58d6b269b797', 
 '663e77bb-c15b-49d0-b41b-eebe8ba82e90', 
# 'c2fe7a86-4dd4-4ec1-8d66-46d0aebc53fa', ### P
#'30ea5ebf-8c5e-427c-bf3e-4f4910ae2e17', ### P
 'da4e8287-133a-4f39-a46e-a0529dbfa73a', 
 'c3671c8c-3f2b-4234-93c2-9f3684206cf0', 
 '63a9254b-ee85-4173-9e98-be4f1c00ebe2', 
 '65fe2512-5a1f-466a-9bec-1ff3f6db60d3', 
 #'f0156796-52b7-4dd6-976d-03eaca662073', ### P
 'eb632cad-66dd-4cb6-a1a0-94ab2830108f', 
 'cde70682-7d69-4869-a43e-74bce9804808', 
 'ddd4370e-0546-465f-aa88-8a8bff7163f3', 
 'ce21b86c-3bb5-4e99-a181-ac54d8c22bfb', 
 '10ea5653-477f-475a-824e-e0384c2ba381', 
 '94261b10-e463-4a3f-8fc1-64661577e6e5', 
 '61c531d2-9a29-4223-bbd4-287b89d94e4e', 
 '812c1e6d-aebb-4c7e-8d3a-1cc1d44b763f', 
 #'5ed46093-0702-4cba-8764-6e53db6748b3', ### PPP
 '199944f4-ad4f-4ed8-8649-59cee0f919c4', 
 '67f46582-a5e2-495e-aab9-8462caee77f2', 
 '5185d1fe-8b8d-4386-983f-58a541f1dfe5', 
 '8b53e913-d3d3-458a-aa5e-bca691264735', 
 '064b7397-d76a-4e65-a0e0-b58dcebc58d3', 
 'c998a479-2b4e-42a6-a2e7-87124b8246c8', 
 'b2cfa5d9-e233-41e5-a54a-9de71b95af26', 
 '376dd1c6-53bb-4985-b95e-25c508232aff', 
# 'fae6bd54-59ab-4512-9a53-45669795dac1', #### p
 '8f3d41bd-e79e-4853-9e8d-b9425910ecb7', 
 #'ec702e88-4d2f-4a81-8818-63f88285dab5', #### P
 '06f8caaf-fe7b-4702-b07c-316d0362da64', 
 'f86f64db-4002-495e-9261-f5cc93abe285', 
 '6ddb9ddc-29f0-4d18-9b03-bf43a8ed077f', 
 'b153b566-be5f-4248-ba27-2b67fbd15466', 
 '02859f12-5827-435d-86cc-f87952eb49ac', 
 '55d571dc-c9dd-42de-ab1c-95651d75366f', 
 '2c9e6e25-d9d0-4fb6-8ccf-e44f37fed244', 
 'a0dca7e6-fe51-46cd-af8f-24c4091f6d32', 
 '0903e37e-0336-442a-a9dd-6952648d662a', 
 '13e4b9a6-f1e2-45d5-8fff-83a246c30858', 
 '85352335-a23d-4063-a29e-51ff94e89d4a', 
 'ba80542b-bb2c-47f8-812c-94df6a67505b', 
 'cac1584b-e2de-4fa5-b2d6-ace6884ce3e1', 
 '5b1f8ad4-55a5-4bf7-861b-ff724afd782b', 
 '33588377-1af8-429b-90ec-678d9edbccb5', 
 '08d1126c-0500-40aa-9e78-2a81bb72dc05', 
 'd31e1cf9-bae2-46fe-a9d5-a41a407f53c7', 
# 'eb93d60c-8b04-4f23-9d70-848c1460ebcc', ### PPP
#'d6dfb942-2112-4edc-abd9-c30269e040e4', #### ppp
 'e0af551f-1004-4d7d-8991-ae21ed6527b2', 
 'acbdf654-b8cf-4301-8f02-9dd5d60534b9', 
 'bff0ce9d-fd36-4395-8977-f8cc975043d0', 
 '36e16f55-fd3b-4abf-b498-8b26d9de13f0', 
 '5af64b58-c086-4e35-8712-06bd25448d52', 
 'f5604b9e-f49a-454b-8db8-8d88dafdd3e1', 
 '62409bcf-6f10-4937-b7fe-5ddd493ae260', 
# 'f0156796-52b7-4dd6-976d-03eaca662073', ### P
 'fdf986e0-ac4c-4b03-9ac4-92addd0c9a79', 
# '293ef6ce-925c-4136-84d9-076719d4a84c', #### P
'5a18af1a-ea51-4f3a-b42d-122a555f3262', 
'2e88f9a1-6d04-4568-b8dc-bc7701fbc598', 
'cc4c1caf-d2b0-4794-bb80-561bd91f3e82', 
'5e3683ef-7a0d-4e73-bd9b-4b747a12dee5', 
               ]
conceptList = ["https://w3id.org/polifonia/ontology/modal-tonal/Cadences_FilaberGuillotelGurrieri_2023/Simplex",
               "https://w3id.org/polifonia/ontology/modal-tonal/Cadences_FilaberGuillotelGurrieri_2023/Formalis",
                              ]

''' delete data'''
print ("Deleting files...")
for folder in ["data/labels", "data/ids", "data/observations"]:
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))

for project in projectList :
    print ("Processing project: " + project)

    obs = Observations([project], conceptList)

manipDataSet = ManipulateDataSet("data/")
manipDataSet.createMainArrays()


