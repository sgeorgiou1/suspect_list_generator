# -*- coding: utf-8 -*-
"""
Created on Wed May 15 08:33:28 2024

@author: SGeorgiou
"""

from suspect_list_generator import suspect_list_generator # import the object code

path = "./" # works if running from current directory

suspect_generator = suspect_list_generator(path, extract=True) # initialise the generator, if you have already extracted then set extract=False

ct_suslist = suspect_generator.generate_ct_list(0.3,desired_bypass=0.35) # run ct/cc list generator functions - example here uses default Inspec values of 30% suspect terms sent to human for CTs, 45% for CCs
cc_suslist = suspect_generator.generate_cc_list(0.45,desired_bypass=0.35) # example is using a desired bypass for the 

suspect_generator.save_lists() # save lists
