# -*- coding: utf-8 -*-
"""
Created on Fri Jul 24 11:53:55 2015

@author: jaelman

Create dataset for analysis. Combines data from AX-CPT, cognitive tasks, 
and pupillometry.
"""

import pandas as pd
import numpy as np
from sas7bdat import SAS7BDAT
import os

###############################
datadir = 'K:/Projects/Pupil_AX-CPT/data'
outdir = 'K:/Projects/Pupil_AX-CPT/data'
pupil_fname = 'K:/data/Pupillometry/pupilDS_long.csv'
cogv2_fname = 'K:/data/VETSA2_April2015/vetsa2merged_1dec2015_edits.sas7bdat'
cogv1_fname = 'K:/data/VETSA1_Aug2014/vetsa1merged_21aug2014.sas7bdat'
cogVars_fname = 'K:/Projects/Pupil_AX-CPT/data/AX-CPT_CogVariables.csv'
demo_fname = 'K:/data/VETSA_demo_vars.csv'
axcpt_fname = 'K:/data/AX-CPT/AX-CPT_V2_processed.csv'
mci_fname = 'K:/data/VETSA2_MCI.csv'
cog_outname = 'AX-CPT_cogData.csv'
final_outname = 'pupil_AX-CPT.csv'
###############################


### Get cognitive and demographic data ###

# Load demographic data
demodf = pd.read_csv(demo_fname)

# Load vetsa2merged dataset to get head injury data
with SAS7BDAT(cogv2_fname) as f:
    cogdf = f.to_data_frame()
    
cogdf = cogdf[['vetsaid','DSFMAX_v2','afqtpcttran_v2','HADSHINJ_v2',
               'NUMHINJ_v2']]

# Set missing missing values in head injury variables
cogdf.ix[cogdf['HADSHINJ_v2']==9,'HADSHINJ_v2'] = None
cogdf.ix[cogdf['NUMHINJ_v2']==99,'NUMHINJ_v2'] = None

# Merge demographic and cognitive data
cogdf = demodf.merge(cogdf, how='right', on='vetsaid')
      
# Save out cognitive data
cog_outfile = os.path.join(datadir, cog_outname)
cogdf.to_csv(cog_outfile, index=False)

## Load pupil data
pupildf = pd.read_csv(pupil_fname)
pupildf = pupildf.drop(['case','twin','zyg14'], axis=1)
## Load AX-CPT data
axcptdf = pd.read_csv(axcpt_fname)

# Load MCI data
MCIdf = pd.read_csv(mci_fname)

#Filter out subjects who were given a Z score of 2 or were not completed
axcptdf = axcptdf.loc[(axcptdf['ZAXCPT_v2']!=2) & 
                      (axcptdf['CPTCOMPLETE_v2']==0)]

## Merge datasets
axcpt_cog = pd.merge(axcptdf, cogdf, left_on='vetsaid', 
                   right_on='vetsaid', how='left')        
pupil_axcpt = pd.merge(pupildf, axcpt_cog, left_on='vetsaid', 
                   right_on='vetsaid', how='inner')                  
pupil_axcpt = pd.merge(pupil_axcpt, MCIdf[['vetsaid','rMCI_cons_v2']], 
                         left_on='vetsaid',right_on='vetsaid', how='left') 
                                                
# Save out files
outfile = os.path.join(outdir,final_outname)
pupil_axcpt.to_csv(outfile, index=False)                                                