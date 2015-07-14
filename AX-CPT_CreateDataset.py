# -*- coding: utf-8 -*-
"""
Created on Fri Jul 10 15:43:18 2015

@author: jaelman
"""

import pandas as pd
import os
import numpy as np
    
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
    idx = (df['TargetSlide.RT']>200.0)|(df['TargetSlide.RT']<1300)
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
    
def calc_misses(trialdf):
    """ Calculate misses (incorrect response) """
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

def calc_trimmed_meanRT(trialdf, meanRT, stdRT):
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
    misses =  calc_misses(trialdf)
    NR = calc_NR(trialdf)
    meanRT = calc_meanRT(trialdf)
    stdRT = calc_stdRT(trialdf)
    trimmed_meanRT = calc_trimmed_meanRT(trialdf, meanRT, stdRT)
    cvRT = calc_cvRT(meanRT, stdRT)
    summary_scores = pd.Series({'hits': hits, 'misses': misses, 'NR': NR,
                        'meanRT': meanRT, 'trimmed_meanRT': trimmed_meanRT,
                        'stdRT': stdRT, 'cvRT': cvRT})
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
    return summarydf

def calc_hitmiss_rt(hits, misses):
    """ Given the number of hits and misses for a particular trial type, 
    calculates the hit rate and miss rate. """
    hitrt = hits / (hits + misses)
    missrt = 1. - hitrt    
    return hitrt, missrt
    
def get_hitmiss_rt(summed_df, trialtypes):
    """ Loops over trial types and inserts hit and miss rate for each into 
    the passed dataframe. """
    for trial in trialtypes:
        trial = trial.lower()
        hits = summed_df[''.join([trial,'hits'])]
        misses = summed_df[''.join([trial,'misses'])]
        hitrtvarname = ''.join([trial,'hitrt'])
        missrtvarname = ''.join([trial,'missrt'])
        summed_df[hitrtvarname], summed_df[missrtvarname] = calc_hitmiss_rt(hits,misses)
    return summed_df
    
def calc_dprime(axhits, axmisses, bxhits, bxmisses):
    """ Calculates d' score from AX and BX trials. AX trials are used for 
    the hit rate and BX for the false alarm rate. These rates are adjusted 
    to avoid dividing by 0. """
    axhitrt = (axhits + 0.5)/(axhits + axmisses + .01)
    bxfart = (bxmisses + 0.5)/(bxhits + bxmisses + 1.)
    dprime = axhitrt - bxfart    
    return dprime   

def get_dprime(df_rates):
    """ Inserts d' score into a passed dataframe. """
    df_rates['dprime'] = calc_dprime(df_rates['axhits'],df_rates['axmisses'],
                                    df_rates['bxhits'],df_rates['bxmisses'])  
    return df_rates

def apply_excludes(df):
    pass
    
def main(infile, outfile, trialtypes):
    axcpt_raw = pd.read_csv(infile, sep=',')
    axcpt_filt = apply_filters(axcpt_raw)
    axcpt_filt = set_miss_RT(axcpt_filt)
    axcpt_summed = summarise_subjects(axcpt_filt)
    axcpt_rates = get_hitmiss_rt(axcpt_summed, trialtypes)
    axcpt_rates = get_dprime(axcpt_rates)
    axcpt_clean = apply_excludes(axcpt_rates)    
    axcpt_clean.to_csv(outfile, index=False)
    
    
##############################################################
############## Set paths and parameters ######################
##############################################################
datapath = 'K:/data/AX-CPT' # Specify data path of AX-CPT data
fname = 'AX-CPT_V2_merged.csv' # Name of input data file
infile = os.path.join(datapath,fname) # Input file
outname = 'AX-CPT_V2_processed.csv' # Name of file to save out
outfile = os.path.join(datapath, outname) # Output file
##############################################################

if __name__ == "__main__":
    trialtypes = ['AX','BX','AY','BY'] # These are hardcoded for now
    main(infile, outfile, trialtypes)


