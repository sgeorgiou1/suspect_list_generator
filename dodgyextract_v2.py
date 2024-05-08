# -*- coding: utf-8 -*-
"""
Created on Tue Feb  1 10:21:07 2022

@author: SGeorgiou
"""

#indexing info extract
import xml.etree.cElementTree as ET
import pandas as pd
from collections import Counter
from tqdm import tqdm
import os

def thes_class_extract(indtype, fileloc):
    '''
    
    Function to output information on Terms/CCs for accepted/rejected index terms at indexing-qa 
    
    Parameters
    ----------
    indtype : str
        What indexing type you are trying to output. Choose from 'INSPEC Thesaurus' or 'INSPEC Classification' (written exactly)\n
    fileloc : str
        File location of xml files to analyse.
    qacheck : bool
        True or false to save the qa reasons for each paper, runs faster when ignoring qa reasons. False by default

    Returns
    -------
    lines: list of str for each paper, each line reads as; paper id, rejected terms, accepted terms (sep = tab) \n
    df: dataframe of unique CTs/CCs with their count for how many times rejected/accepted in total

    '''
    valid = ['INSPEC Thesaurus','INSPEC Classification']
    if indtype not in valid:
        raise ValueError("indtype must be one of %s" %valid)
    
    def list_str(termlist):
        return str(termlist).strip('[]"').replace(", ", ":")
    
    lines = []
    allrejected = []
    allaccepted = []
    alladded = []
    #qareasons = []
    #Loop over the files in the folder
    for i, file in enumerate(tqdm(os.listdir(fileloc))):
        #redefine file location
        file_loc = fileloc + file
        
        #This stops it trying to open files that aren't xml and will cause crashes
        if file[-3:] == "xml":
            # (file)
            #print (file)
            rejTerms = []
            accTerms = []
            addTerms = []
            suggTerms = []
            #define root of XML tree
            tree = ET.parse(file_loc)
            root = tree.getroot()      
            if len(root) != 2:  # this checks to make sure there are 2 sections in the xml (header&data; before itemqa it is just a single block)
                #print ('error', file)
                continue
            #print (file)
            data = root[1][0]
            subject = data.find('{http://data.iet.org/schemas/inspec/content}specialisationType').get('label')
            for item in data:
                if item.tag == "{http://data.iet.org/schemas/inspec/content}annotations":
                    
                    for annot in item:
                        isterm = 'n'
                        isrej = 'n'
                        isacc = 'n'
                        isadd = 'n'
                        issugg = 'n'
                        for an in annot:
                            
    
                            #Returns information about the tag
                            if an.tag == "{http://data.iet.org/schemas/annotation}references":
                                #Returns the term, some differences for Chemical
                                Term = an.attrib['label']
                                
                                
                                #Returns what type of annotation it is
                                Type = an.attrib['schemeLabel']
                                #print (Type)
                                if Type == indtype:
                                    isterm = 'y'
                                    if indtype == 'INSPEC Classification':
                                        #print (an.attrib)
                                        code = an.attrib['code']
                                        Term = code

                                
                            # if an.tag == "{http://data.iet.org/schemas/annotation}annotatedBy":
                            #     #Returns who did it last
                            #     Who = an.attrib['id']
                            
                            if an.tag == "{http://data.iet.org/schemas/annotation}state":
                                #Returns was it, suggested, added,rejected,accepted
                                sara = an.attrib['label']
                                if sara == "Suggested":
                                    issugg = "y"
                                if sara == "Rejected" or sara == "RejectedSevere":
                                    isrej = 'y'
                                if sara == "Accepted":
                                    isacc = 'y'
                                if sara == "Added" or sara == "AddedSevere":
                                    #print (file,"added terms here")
                                    isadd = 'y'
                        if isterm == 'y' and issugg == 'y':
                            suggTerms.append(Term)    
                        if isterm == 'y' and isrej == 'y':
                            rejTerms.append(Term)
                        if isterm == 'y' and isacc == 'y':
                            accTerms.append(Term)
                        if isterm == 'y' and isadd == 'y':
                            addTerms.append(Term)
                            #print (addTerms)
            
            CES_terms = suggTerms + rejTerms + accTerms
                        
            #line = (file + '\t' + str(rejTerms).strip('[]') + '\t' + str(accTerms).strip('[]') + '\t' + str(addTerms).strip('[]')).strip('"') \
            #   + '\t' + str(len(rejTerms)) + '\t' + str(len(accTerms)) + '\t' + str(len(addTerms)) + '\t' + subject + '\n' 
            line = (file + ',' +  list_str(suggTerms) + ',' + list_str(rejTerms) + ',' + list_str(accTerms) + ',' + list_str(addTerms) \
                + ',' + list_str(CES_terms) + ',' + str(len(suggTerms)) + ',' + str(len(rejTerms)) + ',' + str(len(accTerms)) + ',' + str(len(addTerms)) + ',' \
                    + str(len(CES_terms)) + ',' + subject + '\n')
            
            #print (line)
            lines.append(line) 
            "commented out the rest of this to just extract indexing data, if you want CT counts then will need to uncomment these"
            allrejected.extend(rejTerms)
            allaccepted.extend(accTerms)
            alladded.extend(addTerms)
            
            
                
                
    print ('Items analysed. Now counting...')
            
    urej = list(set(allrejected))
    ukeep = list(set(allaccepted))
    uadd = list(set(alladded))
    allterms = list(set(urej+ukeep+uadd))
    rejcount = Counter(allrejected)
    keepcount = Counter(allaccepted)
    addcount = Counter(alladded)
    rejcounts,keepcounts,addcounts = [0 for i in allterms],[0 for i in allterms],[0 for i in allterms]

    for i,term in enumerate(tqdm(allterms)):
        if term in rejcount.elements():
            rejcounts[i] = rejcount[term]
        else:
            rejcounts[i] = 0
        if term in keepcount.elements():
            keepcounts[i] = keepcount[term]
        else:
            keepcounts[i] = 0
        if term in addcount.elements():
            addcounts[i] = addcount[term]
        else:
            addcounts[i] = 0
    

    df = pd.DataFrame(list(zip(allterms,keepcounts,rejcounts,addcounts)), columns=['Term','Correct','Rejected','Added'])

    return lines ,df 
