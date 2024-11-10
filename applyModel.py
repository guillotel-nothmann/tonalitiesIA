'''
Created on Oct 26, 2024

@author: christophe
'''
from music21 import converter
from pitchCollections import PitchCollectionSequence
from tensorflow import keras
import numpy as np


if __name__ == '__main__':
    pass


### load model
 
       
model = keras.models.load_model("model/cadenceModel.h5")
model.compile(optimizer="adam",  loss='sparse_categorical_crossentropy',metrics=['accuracy'])
model.summary()


observationDictionary = {0:None, 
                         1: "Simplex",
                         2: "Formalis"}


### read and create pitchcoll sequence 

work = converter.parse("/Users/christophe/Documents/GitHub/tonalities-pilot/scores/Dufay/029.mei")    #parseURL(workURI, forceSource = True)
pitchCollSequence = PitchCollectionSequence(work)

xmlIdList = []
       
for pitchCollection in pitchCollSequence.explainedPitchCollectionList:
    ''' loop over all analyzed pitches ''' 
    for analysedPitch in pitchCollection.analyzedPitchList:
        
    
        observationArray = np.array(pitchCollSequence.getObservationsForElementId(analysedPitch.id, 5, pitchCollection.offset))
        feature = np.array([observationArray])
                    
        ''' make prediction from observation list '''
        predictions = model.predict(feature)
        
        ''' get highest score identifiy index '''
        highestScore = max(predictions[0]) 
        for index in range (0, len(predictions[0])):
            if predictions[0][index] == highestScore:
                break
            
        analysedPitch.concept = observationDictionary[index]
        analysedPitch.probability = highestScore
        
        if index != 0:
            try:
                element = work.recurse().getElementById(analysedPitch.id)
                element.style.color = "red"
            except:
                print ("Cannot identify element")
                
        
        
        
        if index != 0:
            print ("cadence")

work.show()
    
   