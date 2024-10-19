import os
import numpy as np

class ManipulateDataSet ():
    

    def __init__(self, dataPath):
        
        self.dataPath = dataPath
        self.observationPath = dataPath + "/observations/"
        self.labelPath = dataPath + "/labels/"
        self.idPath = dataPath + "/ids/"
        
    
    def createMainArrays(self):

        ''' loop over files in folder and sort them'''
        filenameList = []
        for filename in os.listdir(self.observationPath):
            filenameList.append(filename)
        filenameList.sort(key=None, reverse=False)
        
        
        ''' loop over filenames, load arrays and store them in meta array '''
        observationList=[]
        labelList=[]
        idList=[]
        
        
        
        for filename in filenameList:
            if filename[-3:]!='npy':continue
            observation = np.load(self.observationPath + filename)
            label = np.load(self.labelPath + filename)
            obsid = np.load(self.idPath + filename)
            
            ''' store everything in lists '''
            observationList.append(observation)
            labelList.append(label)
            idList.append(obsid)
            
            print ("Observation %s stored" %(filename) )
            
        ''' create numpy array and save it'''
        observationArray = np.array(observationList)    
        labelArray = np.array(labelList) 
        idArray = np.array(idList)  
        
        np.save(self.dataPath + "/observations.npy", observationArray, True, False)
        np.save(self.dataPath + "/labels.npy", labelArray, True, False)
        np.save(self.dataPath + "/ids.npy", idArray, True, False)
        
    
       
