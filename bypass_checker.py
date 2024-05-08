# -*- coding: utf-8 -*-
"""
Created on Tue May 16 14:50:40 2023

@author: sgeorgiou
"""

#check bypassed papers

def bypass_checker(suspectlist, itemindexing, bypassrate):
    no_of_terms = len(itemindexing)
    threshold = bypassrate*no_of_terms
    suspect_terms = []
    suspect_count = 0
    for term in itemindexing:
        term = term.strip("'")
        if term in suspectlist:
            suspect_count += 1
            suspect_terms.append(term)
    
    if suspect_count >= threshold:
        return "sent to human", suspect_terms
    else:
        return "bypassed", suspect_terms
    
            
