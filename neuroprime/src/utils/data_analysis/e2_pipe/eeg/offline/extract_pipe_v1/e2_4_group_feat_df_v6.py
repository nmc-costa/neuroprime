#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Sat Oct 27 11:39:15 2018

@author: nm.costa
"""
from __future__ import (absolute_import, division, print_function)
from builtins import * #all the standard builtins python 3 style

import os
import pandas as pd
import numpy as np
import logging

# My functions
#import neuroprime.src.utils.myfunctions as my
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.info('Logger started')
logger.setLevel(logging.INFO)


def df_to_excel(DataFrame, filedir,filename):
    logger.warning("TRYING TO SAVE...")
    writer = pd.ExcelWriter(os.path.join(filedir,filename)+'.xlsx')
    DataFrame.to_excel(writer, 'Sheet1')
    writer.save()
    
def count_cross_group_subjects(A, B):
    counter=0
    subjects=[]
    for a in A:
        for b in B:
            if a[0]==b[0]: 
                counter+=1
                subjects.append(a[0])
    return counter, subjects

def get_subjects_df(filepath, rows=None, columns=None):
    subjects=[]
    #open df
    df=pd.read_pickle(filepath)
    if not rows: return subjects#rows=df.index #get all
    if not columns: return subjects#columns=df.columns #get all
    #Append Rows and Columns subjects
    for r in rows: 
        for c in columns:
            sbj_l=df[c][r]
            for i in sbj_l:#df is in format[['S002', value]]
                subjects.append(i[0]) #df[col][row] chaining indexing returns copy, while df.at[row,col] is the actual cell; https://kanoki.org/2019/04/12/pandas-how-to-get-a-cell-value-and-update-it/
    
    #remove repeated
    subjects=list(set(subjects))
    #sort
    subjects.sort()
    return subjects
    

def get_feat_df(groupdir, true_fileid_seq, tasks_extract_l, band="alpha", file_sufix="e2_PSD_v1", feat_l=['tBAT'], bad_subjects_l=None,select_subjects_l=None, fileid_stop_code="."):
    #list of tasks to group
    group_task_l=true_fileid_seq #
    if tasks_extract_l:
        l=[]
        for f in true_fileid_seq:
            found=False
            for t in tasks_extract_l:
                if not f.find(t)==-1:#if task in filename
                    found=True
            l.append(found)
        l_np=np.array(l)
        t_s_np=np.array(true_fileid_seq)
        g_t_np=t_s_np[l_np]
        group_task_l=g_t_np.tolist() #chosen list

    #Factorial design folder analysis
    group_l=os.listdir(groupdir)
#    groups_bands_d={}
    #features dict
    feat_d={}
    for g in group_l:
        subjectdir=os.path.join(groupdir, g)
        if not os.path.isdir(subjectdir): continue #test if is a folder
        #add feature vars by group
        feat_d[g+"_subjects"]=[]
        for t in group_task_l:
            for feat in feat_l:
                feat_d[g+"_"+band+"_"+feat+"_"+t]=[]
        subject_l=os.listdir(subjectdir)
#        subjects_bands_d={}
        for s in subject_l:
            if bad_subjects_l and s in bad_subjects_l: continue
            if select_subjects_l and s not in select_subjects_l: continue
            taskdir=os.path.join(subjectdir, s)
            if not os.path.isdir(taskdir): continue #test if is a folder
            logger.info('\n>> PROCESSING FEATURE DF:  {}, {}'.format(g,s))
            try:
                data_df_i=pd.read_pickle(os.path.join(taskdir,g+"_"+s+"_"+band+"_"+"tasks_df"+".pcl"))
                #RECREATE DATAFRAME - choosen tasks
                if tasks_extract_l:
                    l=[]
                    for fid in data_df_i.fileid:
                        found=False
                        for t in tasks_extract_l:
                            idx_stop_code=t.find(fileid_stop_code)
                            if idx_stop_code>-1:#if stopcode, search for equal fid
                                if t[:idx_stop_code]==fid:
                                    found=True
                            else:
                                if fid.find(t)>-1:#if task in filename
                                    found=True
                        l.append(found)
                    #new df
                    data_df=data_df_i.loc[l]
                    data_df=data_df.reset_index(drop=True)#drop index
            except:
                logger.error("Subject {} must have repeated files, Check!".format(s)) 
                continue
            #add_subject if works
            feat_d[g+"_subjects"].append(s) #add subject 
            #Save Group features(like tBAT)
            for t in group_task_l:
                is_task=data_df.fileid==t #boolean, search df for task
                if is_task.any(): #got true
                    for feat in feat_l:
                        feat_d[g+"_"+band+"_"+feat+"_"+t].append(data_df[feat][data_df.fileid==t].values[0])
                else:
                    for feat in feat_l:
                        feat_d[g+"_"+band+"_"+feat+"_"+t].append(None)


    #Curate size array with None
    feat_d=dict([ (k,pd.Series(v)) for k,v in feat_d.iteritems() ])
    feat_df=pd.DataFrame(feat_d)
#    feat_df=pd.DataFrame.from_dict(feat_d, orient="index")
#    feat_df=feat_df.T
    df_to_excel(feat_df, groupdir,band+"_group_feat_df_"+file_sufix) #feat_df to excel
    feat_df.to_pickle(os.path.join(groupdir,band+"_group_feat_df_"+file_sufix+".pcl"))
    
    return feat_df




def play_group_feat_df(datadir,band="alpha", protocol="eo", profilename="test_1_profile", columns_select=['NFT_+'], columns_exclude=['EX_SUB'], file_sufix='NFT_pos'):
    #---DATA DIR
    datadir=datadir
    groupdir=datadir
    
    #band
    band=band
    
    #fileid_stop_code
    fileid_stop_code="." #code is sent to plotsuject;  use this at the end of taskname if you want just that file; for BUGs like rest_ec_1 and rest_ec_12
    
    #tasks to extract features
    protocol=protocol
    tasks_extract_l=['_'+protocol+'_'] #['_ec_']; ['_eo_'] ;just first rest ['rest_eo_1.', 'alpha_eo'] #chose tasks to extract, always put the reference baseline, 
    
    #feature to extract list
    feat_l=['ratio_power_threshold', 'tBAT', 'tonic_increase', 'tonic_increase_BAT', 'threshold', 'epoch_a', 'mean', 'std'] 


    #SELECT SUBJECTS (Manual or using subjectprofile)
    #profile df
   # p_band=band#"alpha"
    profilename=profilename#p_band+"_"+"test_1_ratio_power_threshold"+".pcl"
    profiledir=datadir
    filepath=os.path.join(profiledir,profilename)
    #subjects list
    rows=['EG_'+protocol, 'CG_'+protocol]#[]-all subjects;
    columns=columns_select#['NFT_+'] #[]-all subjects;
    select_subjects_l=get_subjects_df(filepath,rows=rows, columns=columns) #[]-all subjects; get_subjects_df(filepath,rows, columns);
    #select_subjects_l.extend(['S018','S024']) #additional responders
    #bad subjects list 
    #NOTE( you don't need to use bad_subject_l, already done in profile_df;)
    rows=rows
    columns=columns_exclude
    bad_subjects_l=get_subjects_df(filepath,rows=rows, columns=columns) #[]-no bad subjects; get_subjects_df(filepath,rows, columns);
    bad_subjects_l.extend(['S063','S064', 'S065']) #additional exclusion list , they are extra subjects
    

    #file sufix to designate the plot
    file_sufix=protocol+"_alltasks_"+file_sufix
 #title and file sufix of plots


#    for i in range(38,64):
#        bad_subjects_l.append('S'+ '{num:03d}'.format(num=i))

    
    #files seq id
    fileid_seq=["rest_ec_1.meta","rest_eo_2.meta","alpha_eo_3.meta", #b1
                "rest_ec_4.meta", "rest_eo_4.meta","breathingv6_ec_4.meta", "breathingv6_eo_4.meta","imageryv6_ec_4.meta", "imageryv6_eo_4.meta","whmv1_ec_4.meta","whmv1_eo_4.meta","alpha_ec_5.meta","alpha_eo_5.meta",#b2
                "rest_ec_6.meta", "rest_eo_6.meta","breathingv6_ec_6.meta", "breathingv6_eo_6.meta","imageryv6_ec_6.meta", "imageryv6_eo_6.meta","whmv1_ec_6.meta","whmv1_eo_6.meta","alpha_ec_7.meta","alpha_eo_7.meta",#b3
                "rest_ec_8.meta", "rest_eo_8.meta","breathingv6_ec_8.meta", "breathingv6_eo_8.meta","imageryv6_ec_8.meta", "imageryv6_eo_8.meta","whmv1_ec_8.meta","whmv1_eo_8.meta","alpha_ec_9.meta","alpha_eo_9.meta",#b4
                "rest_ec_10.meta", "rest_eo_10.meta","breathingv6_ec_10.meta", "breathingv6_eo_10.meta","imageryv6_ec_10.meta", "imageryv6_eo_10.meta","whmv1_ec_10.meta","whmv1_eo_10.meta","alpha_ec_11.meta","alpha_eo_11.meta",#b5
                "rest_ec_12.meta","rest_eo_13.meta","alpha_eo_14.meta"#b6
                ]
    #true file seq id: assuming fileid_seq as true sequence
    true_fileid_seq=[]
    for fid in fileid_seq:
        true_fileid_seq.append(fid.split(".")[0]) #removing extension
    
    get_feat_df(groupdir, true_fileid_seq, tasks_extract_l, band=band, file_sufix=file_sufix, feat_l=feat_l, bad_subjects_l=bad_subjects_l, select_subjects_l=select_subjects_l, fileid_stop_code=fileid_stop_code)
    


if __name__=="__main__":
    #---DATA DIR
    datadir='/Users/nm.costa/Google_Drive/projects/phd/research/2_THESIS_PUBLICATIONS/thesis/C3_e2_results/results/eeg/e2_study_2_150uV_pz_avgref' #'/Volumes/Seagate/e2_priming/e2_analysis_pz_avgref'#my.get_test_folder(foldername="e2_data_da")#

    #band
    band="beta"
    #protocol
    protocol="ec"
    #profile filename
    profilename=band+"_"+"test_1_ratio_power_threshold"+".pcl"
    #columns to select subjects
    columns_select=[] #[]-all subjects;
    columns_exclude=[] #[]-all subjects;
    file_sufix='allsubjects'
    
    play_group_feat_df(datadir,band=band, protocol=protocol, profilename=profilename, columns_select=columns_select, columns_exclude=columns_exclude, file_sufix=file_sufix)

