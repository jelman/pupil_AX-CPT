# -*- coding: utf-8 -*-
"""
Created on Thu Jul 09 12:42:28 2015

@author: jaelman
"""

import pandas as pd
from glob import glob
from sas7bdat import SAS7BDAT
import re
import os

def get_BU_sublist(pth,globstr):
    filelist = glob(os.path.join(pth,globstr))
    sublist = [re.sub('.*[Left,Right]-','',w) for w in filelist]
    sublist = [re.sub('.txt','',w) for w in sublist]
    sublist = [re.sub('-1','A',w) for w in sublist]
    sublist = [re.sub('-2','B',w) for w in sublist]
    return sublist
#################################################################

# Get VETSA 2 data  
datapath = 'K:/data\VETSA2_April2015/vetsa2merged_23apr2015.sas7bdat'
with SAS7BDAT(datapath) as f:
    vetsa2df = f.to_data_frame()
cptinfo = vetsa2df[['vetsaid','SITE_v2','CPTCOMPLETE_v2','CPTCOMPUTER_v2',
                    'CPTTIM_v2','CPTVERS_v2','ZAXCPT_v2']]    
# Extract vetsaid numbers. This can be used as master list of subject id
vetsaid = vetsa2df.vetsaid

## Load UCSD AX-CPT data
infile = 'K:/data/AX-CPT/CPT UCSD V2/CPT UCSD V2T2 (VETSA 2 Follow-up)/AX-CPT_UCSD_V2_merged.csv'
axcptUC = pd.read_csv(infile, sep=',')
vetsaidUC = pd.Series(axcptUC.SubjectID.unique(), name='vetsaid')

######################################################
# Find duplicate and practice subjects in BU dataset #
# before re-generating and merging edat files.       #
######################################################
## Get file listings of BU data. 
# Computer 103
globstr = '*.txt'
pth = 'K:/data/AX-CPT/CPT BU V2/AX CPT 103'
vetsaidBU103 = pd.Series(get_BU_sublist(pth,globstr), name='vetsaid')
# Computer 104
pth = 'K:/data/AX-CPT/CPT BU V2/AX CPT 104'
vetsaidBU104 = pd.Series(get_BU_sublist(pth,globstr), name='vetsaid')

# Find subjects with data on both computers
# Duplicate files have been manually removed. This should not 
# find any duplicates between computers 103 and 104.
BUdups = list(set(vetsaidBU103).intersection(set(vetsaidBU104)))
BUdups = pd.Series(BUdups, name='vetsaid')

# Join lists of BU subject IDs
vetsaidBU = pd.concat([vetsaidBU103,vetsaidBU104], ignore_index=True)

# Find subjects with data in UC and BU datasets
# Duplicate files have been manually removed. This should not 
# find any duplicates between sites.
UC_BUdups = list(set(vetsaidBU).intersection(set(vetsaidUC)))

# Find BU practice subjects. These should not be included in the main dataset.
# Practice files have been manually moved to practice subfiled. This should 
# not find anymore subjects.
BUpractice = list(set(vetsaidBU).difference(set(vetsaid)))
BUpractice = pd.Series(BUpractice, name='vetsaid')

# Check that merged BU edat files contain correct IDs (ie., same as filename)
mergedBU103 = pd.read_csv('K:/data/AX-CPT/CPT BU V2/AX CPT 103/AX-CPT_BU103_V2_merged.csv')
mergedBU103 = pd.Series(mergedBU103['SubjectID'].unique(), name='vetsaid')
mergedBU104 = pd.read_csv('K:/data/AX-CPT/CPT BU V2/AX CPT 104/AX-CPT_BU104_V2_merged.csv')
mergedBU104 = pd.Series(mergedBU104['SubjectID'].unique(), name='vetsaid')
# Check for ids that are different between filenames and merged edats
# These have been corrected manually (3 edat files needed to be regenerated)
# This code should not find any discrepancies
diffBU103 = list(set(vetsaidBU103).symmetric_difference(set(mergedBU103)))
diffBU104 = list(set(vetsaidBU104).symmetric_difference(set(mergedBU104)))

####################################################
# Create AX-CPT dataset including UCSD and BU data #
####################################################
vetsaidAXCPT = pd.concat([vetsaidUC, vetsaidBU], ignore_index=True)
missingAXCPT = pd.Series(list(set(vetsaid).difference(set(vetsaidAXCPT))), 
                         name='vetsaid')
#missingAXCPT.to_csv('K:/data/AX-CPT/missingAXCPT.csv', index=False)

