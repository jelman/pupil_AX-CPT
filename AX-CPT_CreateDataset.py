# -*- coding: utf-8 -*-
"""
Created on Fri Jul 10 15:43:18 2015

@author: jaelman

Script to calculate metrics from AX-CPT and create a dataset. These 
calculations should be identical as those used in VETSA 1.
"""

import pandas as pd
import os
import numpy as np
from sas7bdat import SAS7BDAT

    
def filter_trialproc(df):
    """Filter dataframe for TrialProc procedure. This gets rid of InitialPause 
    and Break slides that occurred at beginning and end of each block."""
    return df[df['Procedure[Trial]']=='TrialProc']

def filter_theBlock(df):
    """Filter out initial practice block of trials."""
    return df[df['TheBlock'].astype('int')!=1]

def filter_RT(df, minRT=200, maxRT=1300):
    """ Set trials with an RT below 200ms or above 1300ms to 
    missing """
    idx = (df['TargetSlide.RT']<minRT)|(df['TargetSlide.RT']>maxRT)
    df.ix[idx,'TargetSlide.ACC'] = 0    
    df.ix[idx,'TargetSlide.RESP'] = np.nan   
    return df

def apply_filters(df):
    """
    Apply all filter functions to dataframe. Filters for:
    1. Only TrialProc procedures, gets rid of breaks and pauses.
    2. Excludes first block of practice trials.
    3. Excludes trials with RTs below min or above max.
    """
    df = filter_trialproc(df)
    df = filter_theBlock(df)
    df = filter_RT(df)    
    return df

def set_miss_RT(df):
    """ Set any trial with inaccurate response to a missing RT. """    
    df.ix[df['TargetSlide.ACC']==0,'TargetSlide.RT'] = np.nan 
    return df
    
def calc_hits(trialdf):
    """ Calculate hits (correct responses) """
    return (trialdf['TargetSlide.ACC']==1).sum()  
    
def calc_errors(trialdf):
    """ Calculate errors (incorrect response made) """
    misses = ((trialdf['TargetSlide.ACC']==0) & 
                (trialdf['TargetSlide.RESP'].notnull())).sum()
    return misses
    
def calc_NR(trialdf):
    """ Calculate no responses """
    NR = ((trialdf['TargetSlide.ACC']==0) & 
                (trialdf['TargetSlide.RESP'].isnull())).sum()
    return NR

def calc_medianRT(trialdf):
    """ Calculate median RT for correct trials. """
    return trialdf.ix[trialdf['TargetSlide.ACC']==1,'TargetSlide.RT'].median()    

def calc_meanRT(trialdf):
    """ Calculate mean RT for correct trials. """
    return trialdf.ix[trialdf['TargetSlide.ACC']==1,'TargetSlide.RT'].mean()    

def calc_stdRT(trialdf):
    """ Calculate standard deviation of RT for correct trials. """
    return trialdf.ix[trialdf['TargetSlide.ACC']==1,'TargetSlide.RT'].std()    

def calc_trim_meanRT(trialdf, meanRT, stdRT):
    """ Calculate trimmed mean of RT for correct trials. Excludes any 
    trials that fall outside of 3 standard deviations of the mean. """
    idx = ((trialdf['TargetSlide.ACC']==1) &
            (trialdf['TargetSlide.RT'] > meanRT-(3*stdRT)) &
            (trialdf['TargetSlide.RT'] < meanRT+3*(stdRT)))
    return trialdf.ix[idx,'TargetSlide.RT'].mean()

def calc_cvRT(meanRT, stdRT):
    """ Calculate coefficient of variation of RT for correct trials. 
    Divides the standard deviation of RT by mean RT. """
    return meanRT / stdRT


def calc_trial_scores(trialdf):
    """ 
    Calculates summary scores for a given trial type. 
    Input is a dataframe containing trials of one trial type from
    one subject.
    Output is a series where each observation is named by the 
    summary score.
    """
    hits =  calc_hits(trialdf)
    errors =  calc_errors(trialdf)
    NR = calc_NR(trialdf)
    misses = errors + NR
    meanRT = calc_meanRT(trialdf)
    medianRT = calc_medianRT(trialdf)
    stdRT = calc_stdRT(trialdf)
    trim_meanRT = calc_trim_meanRT(trialdf, meanRT, stdRT)
    cvRT = calc_cvRT(meanRT, stdRT)
    summary_scores = pd.Series({'hits': hits, 'misses': misses, 
                                'errors': errors, 'NR': NR,
                                'meanRT': meanRT, 'trim_meanRT': trim_meanRT,
                                'medianRT': medianRT, 'stdRT': stdRT, 
                                'cvRT': cvRT})
    return summary_scores

def calc_subject_scores(subjectdf):
    """
    Calculates summary scores for each subject, iterating over trial types. 
    Input is a dataframe containing all trial types for one subject. 
    Output contains one row per trial type and one column per summary score.
    """
    return subjectdf.groupby('Type').apply(calc_trial_scores)    

def summarise_subjects(df):
    """
    Calculates summary scores for the group, iterating over subjects. 
    Input is a dataframe containing all trial types for all subjects.
    Output is transformed such that each row is a subject, and each
    column is a combination of trial type and summary score.
    """
    summarydf = df.groupby('SubjectID').apply(calc_subject_scores)
    summarydf = summarydf.unstack()
    summarydf = summarydf.reorder_levels([1,0], axis=1)
    summarydf.columns = [''.join(col).strip().lower() 
                            for col in summarydf.columns.values]
    summarydf['ntrials'] = df.groupby('SubjectID').size()
    return summarydf

def calc_hitmiss_rate(hits, fa, misses):
    """ Given the number of hits and misses for a particular trial type, 
    calculates the hit rate, false alarm rate, and miss rate. False alarm rate 
    considers number of incorrect responses. Miss rate combines incorrect 
    responses and no responses.
    Note, these are corrected hit and FA rates as defined in Corwin (1994).
    hit rate = (# hits + .5)/(targets + 1)
    false alarm rate = (# FA + .5)/(# distractors + 1)
    """
    hitrate = (hits + .5) / (hits + misses + 1.)
    farate = (fa + .5)/(hits + misses + 1.)
    missrate = 1. - hitrate  
    return hitrate, farate, missrate
    
def get_hitmiss_rate(summed_df, trialtypes=['AX','BX','AY','BY']):
    """ Loops over trial types and inserts hit, false alarm, and miss rate 
    for each into the passed dataframe."""
    for trial in trialtypes:
        trial = trial.lower()
        hits = summed_df[''.join([trial,'hits'])]
        fa = summed_df[''.join([trial,'errors'])]
        misses = summed_df[''.join([trial,'misses'])]
        hitratevarname = ''.join([trial,'hitrate'])
        missratevarname = ''.join([trial,'missrate'])
        faratevarname = ''.join([trial,'farate'])
        hitrate, farate, missrate = calc_hitmiss_rate(hits,fa,misses)
        summed_df[hitratevarname] = hitrate
        summed_df[missratevarname] = missrate
        summed_df[faratevarname] = farate
    return summed_df
    
def calc_dprime(axhitrate, bxfarate):
    """ Calculates d' score from AX and BX trials. AX trials are used for 
    the hit rate and BX for the false alarm rate. The calculation is according 
    to Corwin et al. (1994). The rates should be adjusted to avoid values of 
    0 or 1."""
    return np.log((axhitrate * (1.-bxfarate))/((1.-axhitrate) * bxfarate))

def get_dprime(df_rates):
    """ Inserts d' scores into a passed dataframe. """
    df_rates['dprime'] = calc_dprime(df_rates['axhitrate'],df_rates['bxfarate']) 
    return df_rates

def apply_excludes(df_rates):
    """ Applies excludes based on miss rates in AX, BX and BY trials. 
    Miss rates include incorrect responses (errors) and no responses
    trials to account with subjects that had very low error rate but very 
    high no response rate. """
    exclude_idx = ((df_rates['bymisses'] > 2) | 
                    (df_rates['bxmisses'] > 14) |
                    (df_rates['axmisses'] > 43) | 
                    (df_rates['ntrials'] < 120))
    return df_rates.ix[~exclude_idx]

def merge_qc(axcptdf, cog_file, qcVars):
    """ Merge AX-CPT data with metadata from core dataset. This includes 
    rater Z score, computer, version, complete and time administered."""     
    with SAS7BDAT(cog_file) as f:
        cogdf = f.to_data_frame()
    axcpt_qc = pd.merge(axcptdf, cogdf[qcVars], 
                        left_index=True, right_on='vetsaid', how='left')
    return axcpt_qc
    
def main(infile, outfile):
    axcpt_raw = pd.read_csv(infile, sep=',')
    axcpt_filt = apply_filters(axcpt_raw)
    axcpt_filt = set_miss_RT(axcpt_filt)
    axcpt_summed = summarise_subjects(axcpt_filt)
    axcpt_rates = get_hitmiss_rate(axcpt_summed)
    axcpt_rates = get_dprime(axcpt_rates)
    axcpt_clean = apply_excludes(axcpt_rates)
    axcpt_qc = merge_qc(axcpt_clean, cog_file, qcVars)    
    axcpt_qc.set_index('vetsaid').to_csv(outfile, index=True)
    
    
#########################################################################
############## Set paths and parameters #################################
#########################################################################
datapath = 'K:/data/AX-CPT' # Specify data path of AX-CPT data
fname = 'AX-CPT_V2_merged.csv' # Name of input data file
infile = os.path.join(datapath,fname) # Input file
# Core cognitive dataset and variables corresponding to session info
cog_file = 'K:/data/VETSA2_April2015/vetsa2merged_23apr2015.sas7bdat'
qcVars = ['vetsaid','ZAXCPT_v2','CPTCOMPLETE_v2','CPTTIM_v2',
          'CPTVERS_v2','CPTCOMPUTER_v2']
outname = 'AX-CPT_V2_processed.csv' # Name of file to save out
outfile = os.path.join(datapath, outname) # Output file
#########################################################################

if __name__ == "__main__":
    main(infile, outfile)


