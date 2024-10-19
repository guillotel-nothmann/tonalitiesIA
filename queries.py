'''
Created on Sep 14, 2024

@author: christophe
'''


from SPARQLWrapper import SPARQLWrapper, JSON 
from documentation.source.conf import project


class Queries (object):
    def __init__(self, projectList, conceptList):
        self.sparql = SPARQLWrapper(" https://data-iremus.huma-num.fr/sparql")
        self.sparql.setReturnFormat(JSON)
        self.projectList = projectList
        self.conceptList = conceptList
        
        projectString = ""
        for element in projectList:
            projectString = projectString + "iremus:" + element + ", "
        projectString =   projectString[:-2]
            
        conceptString = ""
        for element in conceptList:
            conceptString = conceptString + element + ", " 
        conceptString = conceptString[:-2]
            
        try:
    
            with open("queryString.txt", 'r', encoding="utf-8") as file: self.queryString = file.read()
            self.queryString = self.queryString.replace("[projectList]", projectString)
            self.queryString = self.queryString.replace("[conceptList]", conceptString)
                       
            
        except Exception as unused_e: 
            self.request = None
                

    
    def processQuery(self):
        
        self.sparql.setQuery(self.queryString)
        try:
            self.request = self.sparql.queryAndConvert()
            
        except Exception as e:
            print(e)
            self.request = None
        
        return self.request
    

 
    
    
    