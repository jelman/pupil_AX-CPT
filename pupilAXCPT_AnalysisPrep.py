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
datadir = '~/netshare/K/Projects/Pupil_AX-CPT/data'
outdir = '~/netshare/K/Projects/Pupil_AX-CPT/data'
pupil_fname = '~/netshare/K/data/Pupillometry/VETSA2/pupilDS_long.csv'
cog_fname = '/home/jelman/netshare/M/PSYCH/KREMEN/Practice Effect Cognition/data/V1V2_CogData_NASAdj_PE.csv'
demo_fname = '~/netshare/K/data/VETSA_Demographics/VETSA_demo_vars2.csv'
axcpt_fname = '~/netshare/K/data/AX-CPT/AX-CPT_V2.csv'
mci_fname = '~/netshare/K/data/VETSA_Demographics/VETSA2_MCI.csv'
cog_outname = 'AX-CPT_cogData.csv'
final_outname = 'pupil_AX-CPT.csv'
###############################

### Get cognitive and demographic data ###

# Load demographic data
demodf = pd.read_csv(demo_fname)
demodf.columns
# Load practice effects data to get AX-CPT and max digit span data
cogdf = pd.read_csv(cog_fname)
cols = ['VETSAID','NAS201TRAN','DSFMAX_V2_nasp','AXHITRATE_V2_nasp',
        'AXFARATE_V2_nasp','AXMISSRATE_V2_nasp','BXHITRATE_V2_nasp',
        'BXFARATE_V2_nasp','BXMISSRATE_V2_nasp','CPTDPRIME_V2_nasp']
cogdf.columns
cogdf = cogdf.loc[:,cols]
cogdf.rename(columns={'VETSAID':'vetsaid'}, inplace=True)

# Merge demographic and cognitive data
cogdf = demodf.merge(cogdf, how='left', on='vetsaid')

# Save out cognitive data
cog_outfile = os.path.join(datadir, cog_outname)
cogdf.to_csv(cog_outfile, index=False)

## Load pupil data
pupildf = pd.read_csv(pupil_fname)
pupildf.columns
pupildf = pupildf.drop(['case','twin','zyg14'], axis=1)

## Load AX-CPT data
axcptdf = pd.read_csv(axcpt_fname)

#Filter out subjects who were given a Z score of 2 or were not completed
axcptdf = axcptdf.loc[(axcptdf['ZAXCPT_v2']!=2) &
                      (axcptdf['CPTCOMPLETE_v2']==0)]
axcptdf = pd.DataFrame(axcptdf['vetsaid'])

# Load MCI data
MCIdf = pd.read_csv(mci_fname)

## Merge datasets
axcpt_cog = pd.merge(axcptdf, cogdf, left_on='vetsaid',
                   right_on='vetsaid', how='left')
pupil_axcpt = pd.merge(pupildf, axcpt_cog, left_on='vetsaid',
                   right_on='vetsaid', how='inner')
pupil_axcpt = pd.merge(pupil_axcpt, MCIdf[['vetsaid','rMCI_cons_v2pe']],
                         left_on='vetsaid',right_on='vetsaid', how='left')

# Save out files
outfile = os.path.join(outdir,final_outname)
pupil_axcpt.to_csv(outfile, index=False)
