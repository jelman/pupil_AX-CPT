# -*- coding: utf-8 -*-
"""
Created on Fri Jul 24 11:53:55 2015

@author: jaelman
"""

import pandas as pd
import numpy as np
from sas7bdat import SAS7BDAT
import os

datadir = 'K:/AX-CPT/data'

### Get cognitive data ###
# Load cognitive scores
fname = 'K:/pupillometry/data/cognitive/vetsa2merged_23apr2015.sas7bdat'
with SAS7BDAT(fname) as f:
    cogdf = f.to_data_frame()
    
fname = 'K:/AX-CPT/data/AX-CPT_CogVariables.csv'
cogvars = pd.read_csv(fname)
cogdf = cogdf[cogvars['NAME']]

# Create Apoe 4 carrier variable
apoeidx = cogdf.apoe2014.str.contains('4')
cogdf.ix[apoeidx, 'apoe4'] = 1
cogdf.ix[~apoeidx, 'apoe4'] = 0

# Set missing missing values in head injury variables
cogdf.ix[cogdf['HADSHINJ_v2']==9,'HADSHINJ_v2'] = None
cogdf.ix[cogdf['NUMHINJ_v2']==99,'NUMHINJ_v2'] = None

# Save out cognitive data
outfile = os.path.join(datadir, 'cogData.csv')
cogdf.to_csv(outfile, index=False)

## Load pupil data
pupildf = pd.read_csv('K:/data/Pupillometry/pupilDS_long.csv')

## Load AX-CPT data
axcptdf = pd.read_csv('K:/data/AX-CPT/AX-CPT_V2_processed.csv')