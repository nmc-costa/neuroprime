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
import matplotlib.pyplot as plt
import matplotlib._color_data as mcd
import numpy as np
import logging
import scipy.stats
#from scipy import stats #needed to load

# My functions
# import neuroprime.src.utils.myfunctions as my
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.info('Logger started')
logger.setLevel(logging.INFO)


def df_to_excel(DataFrame, filedir,filename):
    logger.warning("TRYING TO SAVE...")
    writer = pd.ExcelWriter(os.path.join(filedir,filename)+'.xlsx')
    DataFrame.to_excel(writer, 'Sheet1')
    writer.save()

def ttest_ind_groups(arr_1, arr_2, alpha, sample_size):
    stat, p = scipy.stats.ttest_ind(arr_1, arr_2, axis=0, equal_var=True, nan_policy='propagate')
    print('ttest_statistics=%.4f, p=%.4f' % (stat, p))
    print('N1='+str(len(arr_1)))
    print('N2='+str(len(arr_2)))
    print('df='+str(len(arr_1)+len(arr_2)-2)) #degrees of fredom
    print('confidence='+str(1-alpha)+'%')
    print('two-sided or two-tails test')
    if p > alpha:
        print('Same distributions (fail to reject H0)')
    else:
        print('Different distributions (reject H0)')

def plot_coordinates(plt,x, feat_df, group="EG", tasks_l=[("BAS_0",['rest_eo_2']), ("NFT_1",['alpha_eo_3'])], feat='ratio_power_threshold', band="alpha", color="b", uplims=True, lolims=True, plot_stats=True, alpha_stats=0.05, task_ref_stats="BAS_0", scale=1):
    scale=scale
    y=[]
    e=[]
    y_text=[]
    data_ref=np.array([])
    task_ref_stats=task_ref_stats
    for i,t in enumerate(tasks_l):
        taskid=t[1]
        df=feat_df[group+"_"+band+"_"+feat+"_"+taskid[0]]
        if len(taskid)>1: 
            for tid in taskid[1:]:
                df=df.append(feat_df[group+"_"+band+"_"+feat+"_"+tid])
        data=np.array(df)
        data=data[np.logical_not(np.isnan(data))] #REMOVE NaN
        data=data*scale#scale 
        y.append(data.mean())
        e.append(data.std())
        if plot_stats:
            if task_ref_stats==t[0]: 
                data_ref=data
            elif data_ref.any():
                x_text=x[i]
                y_text=data.mean()
                if group=="EG": y_text=data.mean()+0.2*data.mean()
                if group=="CG": y_text=data.mean()-0.2*data.mean()
                #Stats
                data_1=data_ref
                #data_1=data_1[np.logical_not(np.isnan(data_1))] #REMOVE NaN
                data_2=data
                #data_2=data_2[np.logical_not(np.isnan(data_2))] #REMOVE NaN
                stat, p = scipy.stats.ttest_ind(data_1, data_2, axis=0, equal_var=True, nan_policy='omit')
                
                #text
                text='ttest_ind={:.4f} \n>> p={:.4f}, df={}'.format(stat, p, str(len(data_1)+len(data_2)-2))
                ddof=1 #ddof=1 sample standard deviation; ddof=0 population standard deviation;
                text=text+'\n {}, N={}, mean={:.3f},\n>> std={:.3f}, var={:.3f};\n {}, N={}, mean={:.3f},\n>> std={:.3f}, var={:.3f}'.format(task_ref_stats, str(len(data_1)), data_1.mean(), data_1.std(ddof=ddof),data_1.var(ddof=ddof), t[0], str(len(data_2)), data_2.mean(), data_2.std(ddof=ddof),data_2.var(ddof=ddof))
                 

#                text=text+'\n confidence='+str(1-alpha_stats)+'%'
#                if p > alpha_stats:
#                    text=text+'\n Same distributions (fail to reject H0)'
#                else:
#                    text=text+'\n Different distributions (reject H0)'
                #plot
                plt.text(x_text, y_text, text, horizontalalignment='center',
                         verticalalignment='center', 
                         bbox=dict(boxstyle="round", 
                                   ec=color, fc=(1, 1, 1))) 
    y=np.array(y) #list to array
    e=np.array(e) #list to array
    

    logger.info('\n>> PROCESSING PLOT GROUP:  {}, {}'.format(feat, group))
    #PLOT ERROR BARS
    plt.errorbar(x, y,e,color=color, uplims=uplims, lolims=lolims, label=band+'_'+group+'_'+feat)






def plot_group_bands(datadir, group_l=["EG"],tasks_l=[("BAS_0",['rest_eo_2']), ("NFT_1",['alpha_eo_3'])], band_l=["alpha", "SMR"], band_df_d={"alpha":None, "SMR":None}, feat='ratio_power_threshold', file_sufix="lol", uplims=True, lolims=True, plot_stats=True, task_ref_stats="BAS_0", save=False):

    #init plot
    plt.close('all')
    plt.figure(1)
    f = plt.gcf()
    f.set_size_inches(18.5, 10.5)
    
    #init coordinates
    n_xticks=[]
    for t in tasks_l:
        n_xticks.append(t[0])
    x=np.array([0.33* (r+1) for r in range(len(n_xticks))])
    
    #init color
    color_names=[name for name in mcd.CSS4_COLORS]

    for gi,group in enumerate(group_l):    #for group
        for bi,band in enumerate(band_l):#for band
            color = mcd.CSS4_COLORS[color_names[bi+bi*gi]] #color
            if len(band_l)==1:
                if group=="EG": color="b"
                if group=="CG": color="r"
            #feat
            feat_df=band_df_d[band]
            #plot
            plot_coordinates(plt, x, feat_df, group=group,tasks_l=tasks_l,feat=feat, band=band, color=color, uplims=uplims, lolims=lolims, plot_stats=plot_stats, task_ref_stats=task_ref_stats)
        
    #bands name
    n_b='bands_'
    for b in band_l:
        s_b=list(b)
        n_b=n_b+s_b[0]
    band_n=n_b
    if len(band_l)==1: band_n=band_l[0]
    
    #plot exta defs
    plt.xlabel('Tasks')
    plt.ylabel(band_n+' Groups '+feat)
    plt.grid(True)
    plt.xticks(x,n_xticks)
    Title=group+"_"+band_n+"_"+feat+"_"+file_sufix
    plt.title(Title)

    plt.legend(loc='upper left')

#    plt.show()
    if save:
        print("!!!saving in: "+datadir)
        plt.savefig(os.path.join(datadir, Title+'.pdf'))


if __name__=="__main__":
    #---DATA DIR
    datadir='/Users/nm.costa/Google_Drive/projects/phd/research/2_THESIS_PUBLICATIONS/thesis/C3_e2_results/results/eeg/e2_study_1_pz_avgref' #'/Volumes/Seagate/e2_priming/e2_analysis_pz_avgref'#my.get_test_folder(foldername="e2_data_da")#

    
    #group
    group_l=["CG","EG"]#["EG"]
    
    #feature to plot
    feat='tBAT'
    #protocol
    protocol='eo'
    
    #tasks to present - {"name":"fileid"}
    if protocol=="eo":
        tasks_l=[("BAS_0", ['rest_eo_2']), ("NFT_1",['alpha_eo_3']), ("NFT_2",['alpha_eo_5','alpha_eo_7']), ("NFT_3",['alpha_eo_9','alpha_eo_11']), ("NFT_4",['alpha_eo_14'])]
    if protocol=="ec":
        tasks_l=[("BAS_0",['rest_ec_1']),("NFT_1",['alpha_ec_5','alpha_ec_7']), ("NFT_2",['alpha_eo_9','alpha_eo_11'])]

    #Feat DF filename sufix to use
    feat_df_file_sufix=protocol+"_alltasks_"+'allsubjects'
    
    #bands
    band_l=['alpha']#['theta','alpha','SMR','beta']
    #bands df
    band_df_d={}
    for band in band_l:
        filename=band+"_group_feat_df_"+feat_df_file_sufix+".pcl" #fead df filename
        feat_df=pd.read_pickle(os.path.join(datadir,filename))
        band_df_d[band]=feat_df
    


    #PLOT BANDS
    logger.info('PLOT GROUP')
    plot_stats=True
    task_ref_stats="BAS_0"
    save=True
    
    plot_group_bands(datadir, group_l=group_l,tasks_l=tasks_l, band_l=band_l,band_df_d=band_df_d, feat=feat, file_sufix=feat_df_file_sufix, uplims=True, lolims=True, plot_stats=plot_stats, task_ref_stats=task_ref_stats, save=save)

