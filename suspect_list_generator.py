# -*- coding: utf-8 -*-
"""
Created on Wed Apr  3 09:27:52 2024

@author: SGeorgiou
"""
import numpy as np
import json
import os
import csv
import pandas as pd
from tqdm import tqdm
from dodgyextract_v2 import thes_class_extract
from bypass_checker import bypass_checker

def get_prefix(indtype): #this is just for the file name prefix depending on the indexing type
    if indtype == "INSPEC Thesaurus":
        prefix = "CT_"
    else:
        prefix = "CC_"
    return prefix

def csv_writer(path, lines, indtype): #this function is to be used within the ind_extract function to write the item indexing output to a csv file
    #first write a line for the csv headers
    headers = "ID" + ',' + "Suggested" + ',' + "Rejected" + ',' + "Accepted" + ',' + "Added" + ',' + "CES" + ',' + "SuggCount" + ',' + "RejCount" + ',' + "AccCount" + ',' + "AddCount" + ',' + "CESCount" + ',' + "Subject"
    
    #generate file prefix
    prefix = get_prefix(indtype)       
    
    #create and write the file
    
    with open(path + f'indexing_docs\\{prefix}indexing.csv', 'w', encoding='utf-8') as f:
        f.write(str(headers)+ '\n')
        for line in lines:
            f.write(line)
        f.close()

def ind_extract(path, indtype): #this uses the dodgyextract function to extract all CTs/CCs and their state and outputs the indexing (which is saved by csv_writer) and individual term statistics
    
    lines, ind_df = thes_class_extract(indtype, path + "files//") #call the function to generate initial outputs
    print (ind_df)
    ind_df = ind_df.set_index("Term") # this resets the index of the dataframe so the to_dict() function outputs correctly
    
    term_dict = ind_df.to_dict('index') # convert term stats into a dictionary
    
    #here I add CES total and precision values to the term dictionary 
    
    for term in term_dict:
        entry = term_dict[term]
        entry['CESTotal'] = entry['Correct'] + entry['Rejected']
        if entry['CESTotal'] != 0: # avoiding div0 errors
            entry['Precision'] = entry['Correct'] / entry['CESTotal']
        else:
            entry['Precision'] = "NaN"
            
    #use csv_writer to save indexing output
    csv_writer(path,lines,indtype)
    
    #convert dict object to JSON, indent is a visual indent in the output file
    json_dict = json.dumps(term_dict,indent=2)
    
    #generate file prefix
    prefix = get_prefix(indtype)
    
    #write JSON file
    with open(path + f'indexing_docs\\{prefix}stats.json', 'w', encoding= 'utf-8') as f:
        f.write(json_dict)
    
    return lines, term_dict


def suspect_terms_generator(indtype, ind_df, ind_stats, bypass_cutoff, max_precision = 0, desired_bypass = 0):

    #first cut down dataframe to the relevant columns, we only need ID and CES indexing    
    indexing = ind_df[["ID","CES"]]
    
    
    ind_dict = {i.ID:{"indexing":i.CES.split(":")} for i in indexing.itertuples() if isinstance(i.CES,str)}
    
    #create a dictionary for the indexing terms, {ID:{indexing:[term1, term2, term3, ... ,termN]}} which serves as test area for creating a suspect list
    
    
    if max_precision != 0: # if we are creating a suspect list based on a given precision limit this part of the function will run
        bypass_count = 0
        sus_list = []
        for term in ind_stats: #loop through indexing statistics dictionary to generate a suspect list based on precision limit
            entry = ind_stats[term] 
            if  isinstance(entry['Precision'],float) and entry['Precision'] <= max_precision and entry['CESTotal'] >= 10: #this selects the correct terms based on desired values
                sus_list.append(term)
        for item in ind_dict: # loop through item indexing
            
            indexing = ind_dict[item]["indexing"]
            output, susterms = bypass_checker(sus_list,indexing,bypass_cutoff) # use bypass checker to determine whether or not each item would bypass using the list created above
            ind_dict[item]["output"], ind_dict[item]["suspect terms"] = output, susterms # populate dictionary with the output and suspect terms in the item for checking
            if output == "bypassed":
                bypass_count += 1
        bypass_pctage = 100 * bypass_count / len(ind_dict)
        
        print (f'{int(bypass_pctage)}% ({bypass_count}) items bypassed with a suspect list of {len(sus_list)} terms.')
        print (f'{(len(ind_dict)-bypass_count)} sent to QA')
        return sus_list, ind_dict, bypass_pctage
        
    
    if desired_bypass != 0: # if we are creating a suspect list based on a desired bypass value this part of the function will run
        precision_values = []
        bypass_pctage = 0
        prec_range = np.arange(0.05,0.85,0.05)[::-1] # create a basic range of precision values to test
        prec_range = np.round(prec_range,2) # this negates any float issues from numpy
        #print (prec_range)
        for prec in prec_range: # loop through precision values in the range
            bypass_count = 0
            print ("="*80)
            print (f"Trying suspect list with term precision: {prec}")
            sus_list = []
            for term in ind_stats: 
                entry = ind_stats[term] 
                if  isinstance(entry['Precision'],float) and entry['Precision'] <= prec and entry['CESTotal'] >= 10: # creating a suspect list based on current precision value in the range
                    sus_list.append(term)
            print ("Suspect list lenght = ", len(sus_list))
            for item in ind_dict: # test current suspect list against items in dictionary
                indexing = ind_dict[item]["indexing"]
                output, susterms = bypass_checker(sus_list,indexing,bypass_cutoff)
                ind_dict[item]["output"], ind_dict[item]["suspect terms"] = output, susterms
                if output == "bypassed":
                    bypass_count += 1
            bypass_pctage = bypass_count / len(ind_dict) 
            print (f"This yields a bypass percentage of {bypass_pctage}, desired bypass is {desired_bypass}")
            print (f'{bypass_pctage}% ({bypass_count}) items bypassed with a suspect list of {len(sus_list)} terms.')
            print (f'{(len(ind_dict)-bypass_count)} sent to QA')
                        
            precision_values.append((prec, bypass_pctage)) # append test values to a list to display different variations
            if bypass_pctage >= 0.99 * desired_bypass: # if the bypass rate is within 95% of your desired bypass then break the loop and output this configuration
                break
            
        print ("="*80)
        print (f'Ideal precision cutoff is {prec} with a bypass rate of {bypass_pctage}')
        print ('Other values: ', precision_values)
        return sus_list, ind_dict, bypass_pctage
    
    
    
class suspect_list_generator:
    def __init__(self, path, extract = "n"): #initialise the object - decide whether or not you need to extract from the XML files, if running for the first time, always extract to ensure correct file setup
        self.path = path
        self.extract = extract
        self.ct_indtype = "INSPEC Thesaurus"
        self.cc_indtype = "INSPEC Classification"
        if extract.lower() == "y": # run extract codes if extraction argument is triggered

            
            ct_lines, self.ct_ind_stats = ind_extract(self.path, self.ct_indtype) 
            cc_lines, self.cc_ind_stats = ind_extract(self.path, self.cc_indtype)
            
        else: # if not then this imports the correct files assuming extraction has already been completed

            
            with open(path + "indexing_docs/CT_stats.json") as f:
                self.ct_ind_stats = json.load(f)
                f.close()
            with open(path + "indexing_docs/CC_stats.json") as f:
                self.cc_ind_stats = json.load(f)
                f.close()
                
        self.ct_indexing = pd.read_csv(path + "indexing_docs/CT_indexing.csv")
        self.cc_indexing = pd.read_csv(path + "indexing_docs/CC_indexing.csv")
        
    def generate_ct_list(self, bypass_cutoff, max_precision = 0, desired_bypass = 0): # this runs the suspect terms generator function with your given values
        if max_precision == 0 and desired_bypass == 0:
            raise ValueError("Please assign either a max_precision or desired_bypass to create suspect terms list")
        if max_precision != 0 and desired_bypass != 0:
            raise ValueError("You can only choose to create a suspect terms list based either on the max_precision or the desired_bypass, one of these must be zero")
            
        self.ct_suspect_list, self.ct_ind_dict, self.ct_bypass_pctage = suspect_terms_generator(self.ct_indtype, self.ct_indexing, self.ct_ind_stats, bypass_cutoff, max_precision, desired_bypass)
        
        #return self.ct_suspect_list, self.ct_ind_dict, self.ct_bypass_pcsage 
    
    def generate_cc_list(self, bypass_cutoff, max_precision = 0, desired_bypass = 0):
        if max_precision == 0 and desired_bypass == 0:
            raise ValueError("Please assign either a max_precision or desired_bypass to create suspect terms list")
        if max_precision != 0 and desired_bypass != 0:
            raise ValueError("You can only choose to create a suspect terms list based either on the max_precision or the desired_bypass, one of these must be zero")
        
        self.cc_suspect_list, self.cc_ind_dict, self.cc_bypass_pctage = suspect_terms_generator(self.cc_indtype, self.cc_indexing, self.cc_ind_stats, bypass_cutoff, max_precision, desired_bypass)
        
        #return self.cc_suspect_list, self.cc_ind_dict, self.cc_bypass_pcsage
    
    def save_lists(self):
        try:
            cts_df = pd.DataFrame.from_dict(self.ct_ind_dict, orient = "index")
            cts_df = cts_df.reset_index(names = "ID")
            
            ccs_df = pd.DataFrame.from_dict(self.cc_ind_dict, orient = "index")
            ccs_df = ccs_df.reset_index(names = "ID")
            
            
            cts_df.to_csv(self.path + "indexing_docs/CT_suspect_output.csv")
            ccs_df.to_csv(self.path + "indexing_docs/CC_suspect_output.csv")    
        
            pd.DataFrame(self.ct_suspect_list, columns = ["Term"]).to_csv((self.path + "indexing_docs/CT_suspect_list.csv"))
            pd.DataFrame(self.cc_suspect_list, columns = ["Term"]).to_csv((self.path + "indexing_docs/CC_suspect_list.csv"))
        
        except:
            raise ValueError("Suspect lists must be generated before you can save them")

              
