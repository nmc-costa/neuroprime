#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 22 14:11:35 2019

@author: nm.costa
"""
import os
import shutil
if __name__=="__main__":
    #---DATA DIR
    datadir="/Volumes/Seagate/e1_data_nft/data_to_process_2/rawdata_curated_1"
    out_datadir="/Users/nm.costa/Google_Drive/projects/phd/research/0_EXPERIMENTS/phd_experiments/e1_mentalstimulus_nft/data_analysis/results/python/pipeline_1/SMR_Behavioral_plots"
    true_fileid_seq = ['rest_1', 'rest_2', 'rest_3']

    #Factorial design folder analysis
    groupdir=datadir
    group_l=os.listdir(groupdir)
    groups_bands_d={}
    for g in group_l:
        subjectdir=os.path.join(datadir, g)
        if not os.path.isdir(subjectdir): continue #test if is a folder

        subject_l=os.listdir(subjectdir)
        subjects_bands_d={}
        for s in subject_l:
            taskdir=os.path.join(subjectdir, s)
            
            if not os.path.isdir(taskdir): continue #test if is a folder
            task_l=os.listdir(taskdir)
            filepath=os.path.join(taskdir, g+'_'+s+'_'+"tasks_bands_df_2"+'.xlsx')
            outfilepath=os.path.join(out_datadir, g+'_'+s+'_'+"tasks_bands_df_2"+'.xlsx')
            shutil.copyfile(filepath, outfilepath)