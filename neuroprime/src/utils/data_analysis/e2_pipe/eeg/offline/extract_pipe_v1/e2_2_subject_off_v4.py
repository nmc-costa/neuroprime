#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Sat Oct 27 11:30:51 2018

@author: nm.costa
"""
from __future__ import (absolute_import, division, print_function)
from builtins import * #all the standard builtins python 3 style

#from eegpipeline_v2 import eegpipeline_v2 #use specific pipeline - to save serialization
import logging
import os
#import copy
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib._color_data as mcd
import six #string types

#from matplotlib.ticker import NullFormatter  # useful for `logit` scale

# My functions
import neuroprime.src.functions.myfunctions as my

logger = logging.getLogger(__name__)
logger.info('Logger started')



def df_to_excel(DataFrame, filedir,filename):
    logger.warning("TRYING TO SAVE...")
    writer = pd.ExcelWriter(os.path.join(filedir,filename)+'.xlsx')
    DataFrame.to_excel(writer, 'Sheet1')
    writer.save()

def df_bands(reward_bands, inhibit_bands, filedir,filename):
    df_reward_bands=pd.DataFrame(reward_bands)
    df_reward_bands_T=df_reward_bands.transpose()
    df_inhibit_bands=pd.DataFrame(inhibit_bands)
    df_inhibit_bands_T = df_inhibit_bands.transpose()
    df_result_T=pd.concat([df_reward_bands_T,df_inhibit_bands_T])
    print (df_result_T)
#    df_to_excel(df_result_T, filedir,filename)
    return df_result_T

def df_subject(bands_d, true_fileid_seq):
    data_a=[]
    for i, fid in enumerate(true_fileid_seq):
        for band in bands_d[fid]:
            if bands_d[fid][band]["epoch_a"]:
                data_a.append( {"order":i, 'fileid':fid, "band":band, "mean":bands_d[fid][band]["threshold_mean"], "std": bands_d[fid][band]["threshold_std"], "epoch_a": bands_d[fid][band]["epoch_a"]} )
            else:
                data_a.append( {"order":i, 'fileid':fid, "band":band, "mean":bands_d[fid][band]["threshold_mean"], "std": bands_d[fid][band]["threshold_std"] } )
        
    data_df= pd.DataFrame(data_a)
    return data_df

def df_band(band, bands_d, true_fileid_seq):
    data_a=[]
    for i, fid in enumerate(true_fileid_seq):
        if bands_d[fid][band]["epoch_a"]:
            data_a.append( {"order":i, 'fileid':fid, "band":band, "mean":bands_d[fid][band]["threshold_mean"], "std": bands_d[fid][band]["threshold_std"], "epoch_a": bands_d[fid][band]["epoch_a"]} )
        else:
            data_a.append( {"order":i, 'fileid':fid, "band":band, "mean":bands_d[fid][band]["threshold_mean"], "std": bands_d[fid][band]["threshold_std"] } )
    data_df =pd.DataFrame(data_a)
    return data_df

def df_tasks_bands(band, tasks_bands_d, true_fileid_seq):
    data_a=[]
    for i, fid in enumerate(true_fileid_seq):
        for task in tasks_bands_d:
            if tasks_bands_d[task]:
                if fid in tasks_bands_d[task].keys():
                    if tasks_bands_d[task][fid]:
                        if band in tasks_bands_d[task][fid].keys():
                            if tasks_bands_d[task][fid][band]["epoch_a"]:
                                data_a.append( {"task":task,"order":i, 'fileid':fid, "band":band, "mean":tasks_bands_d[task][fid][band]["threshold_mean"], "std": tasks_bands_d[task][fid][band]["threshold_std"], "epoch_a": tasks_bands_d[task][fid][band]["epoch_a"]} )
                            else:
                                data_a.append( {"task":task,"order":i, 'fileid':fid, "band":band, "mean":tasks_bands_d[task][fid][band]["threshold_mean"], "std": tasks_bands_d[task][fid][band]["threshold_std"] } )
        
    data_df =pd.DataFrame(data_a)
    return data_df

def get_bat_time(task_data, point_ts, task_threshold, task_time):
    #get bat using time - WARNING seems pointless to me
    #% time in Brain Activity Target (%BAT)
    bat=None
    counter=0
    for d in task_data:
        if d>task_threshold:
            counter+=1

    bat=round((counter*point_ts)/float(task_time), 4) #in seconds
    return bat

def get_bat(task_data, task_threshold):
    #% time in Brain Activity Target (%BAT)
    bat=None
    bat_e_nr=0
    total_e_nr=0
    bat_e_data=[]
    #define bat: 
    #Target: above threshold
    for d in task_data:
        if d>task_threshold:
            bat_e_nr+=1
            bat_e_data.append(d)
    total_e_nr=len(task_data)

    bat=round((bat_e_nr)/float(total_e_nr), 4) 
    return bat, total_e_nr, bat_e_nr, bat_e_data

def get_tonic_increase(bat, absolute_power):
    #Tonic increase instead of  rapid phasic shifts
    tonic=None
    if bat:
        tonic=bat*absolute_power #%of absolute power
    return tonic

def get_task_threshold(task, data_df,reward_level=0):
    threshold=None
    #eo or ec?
    task_type=task.rsplit("_")[-2]#rest_ec_1.meta or rest_eo_2.meta
    
    #DEFINE THRESHOLDS
    #e2 reward_level = -0.38 * std =>68% epochs above
    th_fid=None
    if task_type=="ec": th_fid='ec_1' #last fid
    if task_type=="eo": th_fid='eo_2'
    for fid in data_df.fileid:
        idx=fid.find(th_fid)
        if idx>-1:#if found
            if fid[idx:]== th_fid: #if equal
                mean=data_df.loc[data_df.fileid == fid, 'mean'].values[0] #boolean indexing
                std=data_df.loc[data_df.fileid == fid, 'std'].values[0]
                threshold=mean+reward_level*std
                break

#    threshold_ec, threshold_eo= None, None
#    if (data_df.fileid == 'rest_ec_1').any():
#        mean=data_df.loc[data_df.fileid == 'rest_ec_1', 'mean'].values[0] #boolean indexing
#        std=data_df.loc[data_df.fileid == 'rest_ec_1', 'std'].values[0]
#        threshold_ec=mean+reward_level*std
#    if (data_df.fileid == 'rest_eo_2').any():
#        mean=data_df.loc[data_df.fileid == 'rest_eo_2', 'mean'].values[0]
#        std=data_df.loc[data_df.fileid == 'rest_eo_2', 'std'].values[0]
#        threshold_eo=mean+reward_level*std
#    if task_type=="ec":threshold=threshold_ec
#    if task_type=="eo":threshold=threshold_eo

    return threshold


def add_features_df(data_df, reward_level=0):
    #creating ordered lists
    abs_power_l=[]
    ratio_power_thresh_l=[]
    tBAT_l=[]
    absolute_power_bat_l=[]
    tonic_increase_l=[]
    tonic_increase_BAT_l=[]
    threshold_l=[]
    total_e_nr_l=[]
    bat_epochs_l=[]
    for r in range(len(data_df)):
        task = data_df["fileid"][r]
        threshold=get_task_threshold(task, data_df, reward_level=0)
        threshold_l.append(threshold)
        task_data=[d[0] for d in data_df["epoch_a"][r] if d is not None]#get only mean, not STD and take out None
        
        #NEW FEATURES (Enriquez Geppert 2017)
        absolute_power=data_df["mean"][r] #1)
        abs_power_l.append(absolute_power)
        ratio_power_thresh_l.append(absolute_power/threshold)
        bat, total_e_nr, bat_e_nr, bat_e_data=get_bat(task_data, task_threshold=threshold) #2) %time on brain activity target
        absolute_power_bat=np.array(bat_e_data).mean() #4) mean of bat epochs, above threshold
        absolute_power_bat_l.append(absolute_power_bat)
        tBAT_l.append(bat)
        total_e_nr_l.append(total_e_nr)
        bat_epochs_l.append(bat_e_nr)
        tonic_increase=get_tonic_increase(bat, absolute_power) #3) is 1)*3)
        tonic_increase_l.append(tonic_increase)
        tonic_increase_BAT=get_tonic_increase(bat, absolute_power_bat) #5) is 3)*4) - absolute_power on BAT * BAT
        tonic_increase_BAT_l.append(tonic_increase_BAT)
    
    data_df["absolute_power"]= pd.Series(abs_power_l, index=data_df.index)
    data_df["threshold"]= pd.Series(threshold_l, index=data_df.index)
    data_df["ratio_power_threshold"]= pd.Series(ratio_power_thresh_l, index=data_df.index)
    data_df["tBAT"]= pd.Series(tBAT_l, index=data_df.index)
    data_df["absolute_power_BAT"]= pd.Series(absolute_power_bat_l, index=data_df.index)
    data_df["tonic_increase"]= pd.Series(tonic_increase_l, index=data_df.index)
    data_df["tonic_increase_BAT"]= pd.Series(tonic_increase_BAT_l, index=data_df.index)
    data_df["bat_epochs"]= pd.Series(bat_epochs_l, index=data_df.index)
    data_df["total_epochs"]= pd.Series(total_e_nr_l, index=data_df.index)
    return data_df


def plot_task_bands_d(group, subject, taskdir, true_fileid_seq, tasks_extract_l, band="alpha", file_sufix="e2_PSD_v1", reward_level=0, fileid_stop_code=".", show_std=False):
    ####GET DATA
    #------------------------------------
    #create array of features to plot
    tasks_bands_d=my.deserialize_object(taskdir, group+"_"+subject+"_"+"tasks_bands_d.txt", method="json")


    
    #create dataframes and save with pandas
    #band="alpha"#choose band to show
    data_df_i=df_tasks_bands(band, tasks_bands_d, true_fileid_seq)
    #sort
    data_df_i.sort_values(['order']) 
    
    
    #Calculate features and add to tasks_bands_d (ordered lists)
    data_df_i=add_features_df(data_df_i, reward_level=reward_level)
    #SAVE
    df_to_excel(data_df_i, taskdir,group+"_"+subject+"_"+band+"_"+"tasks_df")
    data_df_i.to_pickle(os.path.join(taskdir,group+"_"+subject+"_"+band+"_"+"tasks_df"+".pcl"))


    #RECREATE DATAFRAME - choosen tasks
    data_df=data_df_i
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
    #RECREATE NAMES
#    fst_name="NFT"
#    scd_name="NFT"
#    thd_name="NFT"
#    if group=="EG":
#        m=data_df_i.fileid=="mindfulness_3"
#        i=data_df_i.fileid=="imagery_3"
#        if m.any():
#            scd_name="M_NFT"
#            thd_name="I_NFT"
#        elif i.any():
#            scd_name="I_NFT"
#            thd_name="M_NFT"
#    fst=data_df.fileid=="SMR_1"
#    scd=data_df.fileid=="SMR_2"
#    thd=data_df.fileid=="SMR_3"
#    if fst.any(): data_df.at[data_df.fileid=="SMR_1",'fileid']= fst_name+"_SMR_1"
#    if scd.any(): data_df.at[data_df.fileid=="SMR_2",'fileid']= scd_name+"_SMR_2"
#    if thd.any(): data_df.at[data_df.fileid=="SMR_3",'fileid']= thd_name+"_SMR_3"

    
    ##GET COORDINATES
    ##average values:
    x_mean=np.array(range(len(data_df["mean"])))+0.5 #x coordinate of mean
    x_v_lines=x_mean-0.5 #x coordinate of vertical lines
    x_v_lines=np.append(x_v_lines, x_v_lines[-1]+1) 
    #1)band_psd_avg 
    y_mean=data_df["mean"] #y mean value = psd average
    y_std_pos=data_df["mean"]+data_df["std"]
    y_std_neg=data_df["mean"]-data_df["std"]
    #2)band_epoch_avg (TESTED - Same values as psd_avg)
    calculate_epoch_mean=False
    if calculate_epoch_mean:
        df=pd.DataFrame(columns=['mean','std'])
        for r in range(len(data_df)): #for each (r)ow
            epochs_n=len(data_df["epoch_a"][r])
            m_a=[]
            sd_a=[]
            for e in range(epochs_n):
                if not data_df["epoch_a"][r][e]: continue
                m=data_df["epoch_a"][r][e][0]
                sd=data_df["epoch_a"][r][e][1]
                m_a.append(m)
                sd_a.append(sd)
            m_a=np.array(m_a)
            sd_a=np.array(sd_a)
            df= df.append({'mean':m_a.mean(), 'std': m_a.std() }, ignore_index=True)
        e_mean=df["mean"]
#        e_std=df["std"]
        y_mean_e=e_mean #y mean value = epoch band average
#        y_std_pos_e=e_mean+e_std
#        y_std_neg_e=e_mean-e_std
    #name of x axis tasks
    n_xticks=data_df['fileid'] 
    
    
    ##get rest coordinates
#    l=[]
#    for f in data_df.fileid:
#        if "rest" in f:
#            l.append(True)
#        else:
#            l.append(False)
#    x_rest=x_mean[l]
#    y_rest=y_mean[l]
    
    ##epoch coordinates
    x_e_mean=[] #grey epochs
    y_e_mean=[] #grey epochs
    y_e_std_pos=[] #grey epochs
    y_e_std_neg=[] #grey epochs
    x_e_mean_g=[] #green epochs
    y_e_mean_g=[] #green epochs
    y_e_std_pos_g=[] #green epochs
    y_e_std_neg_g=[] #green epochs
    


    for r in range(len(data_df)): #for each (r)ow
        epochs_n=len(data_df["epoch_a"][r])
        task = data_df["fileid"][r]
        threshold=get_task_threshold(task, data_df, reward_level=reward_level)
        if not threshold: continue

        point_s=1/float(epochs_n) #between 0 and one
        for e in range(epochs_n):
            if not data_df["epoch_a"][r][e]: continue
            m=data_df["epoch_a"][r][e][0]
            sd=data_df["epoch_a"][r][e][1]
            if m >(-1)*4*threshold and m<4*threshold: #LIMITING GRAPH DATA to -4*Threshold to 4*threshold
                if m>threshold:
                    x_e_mean_g.append(r+e*point_s)
                    y_e_mean_g.append(m)
                    y_e_std_pos_g.append(m+sd)
                    y_e_std_neg_g.append(m-sd)
                x_e_mean.append(r+e*point_s)
                y_e_mean.append(m)
                y_e_std_pos.append(m+sd)
                y_e_std_neg.append(m-sd)
    

    
    
    #PLOT COORDINATES
    plt.close('all')
    plt.figure(1)
    f = plt.gcf()
#    ax=plt.gca()
    f.set_size_inches(18.5, 10.5)
    
    #plot vlines
    for xc in x_v_lines:
        plt.axvline(x=xc, color="k")
    
    #plot for each epoch
    for r in range(len(data_df)):
        epochs_n=len(data_df["epoch_a"][r])
        task = data_df["fileid"][r]
        threshold=get_task_threshold(task, data_df, reward_level=reward_level)
        #plot horizontal lines
        xmin=x_v_lines[r]
        xmax=x_v_lines[r+1]
        plt.hlines(threshold, xmin, xmax,color="r")

        #plot add features - text
        #if band in task:
#        task_data=[d[0] for d in data_df["epoch_a"][r] if d is not None]#get only mean and take out None
        #features - 
        bat=data_df.tBAT[r]
#        absolute_power=data_df["mean"][r]
#        tonic_increase=data_df.tonic_increase[r]
        nr_epo_on_target=0
        for e in range(epochs_n):
            if not data_df["epoch_a"][r][e]: continue
            m=data_df["epoch_a"][r][e][0]
            sd=data_df["epoch_a"][r][e][1]
            if m>threshold:
                nr_epo_on_target+=1
        
        
        x_text=x_mean[r]
        y_text=min(y_e_mean)

        text="%tBAT: "+str(round(100*bat,4)) #change based in feature
        text=text+"\n target/total: "+str(nr_epo_on_target)+"/"+str(epochs_n)
        plt.text(x_text, y_text, text, horizontalalignment='center', verticalalignment='center',
                 bbox=dict(boxstyle="round",
                           ec=(1., 0.5, 0.5),
                           fc=(1., 0.8, 0.8),
                           )) 
        #plt.plot(x_text, tonic_increase,'b*', label="")
            
            
    
    #plot means
    plt.plot(x_e_mean, y_e_mean,'.', color = '0.75', label='epoch_below_threshold')
#    plt.fill_between(x_e_mean, y_e_std_pos, y_e_std_neg, color='0.85', alpha=.5)
    plt.plot(x_e_mean_g, y_e_mean_g,'.', color = 'g', label='epoch_above_threshold')
#    plt.fill_between(x_e_mean_g, y_e_std_pos_g, y_e_std_neg_g, color='g', alpha=.5)
    
    #plot slope
#    for r in range(len(x_rest)):
#        plt.plot(x_mean[2*r:2*r+2],y_mean[2*r:2*r+2], 'b-', label ="")
        
    plt.plot(x_mean, y_mean,'-bo', label='task_mean_psd')
    if calculate_epoch_mean: plt.plot(x_mean, y_mean_e,'-co', label='task_mean_epoch')
    #plt.plot(x_rest, y_rest,'ro', label='absolute_rest_power')
    if show_std: plt.fill_between(x_mean, y_std_pos, y_std_neg, color='k', alpha=.5)
    
    
    
#    plt.plot(x, y_std_pos,'k-*', label='std_pos')
#    plt.plot(x, y_std_neg,'k-*', label='std_neg')

    plt.xlabel('Tasks')
    plt.ylabel(band +', 1s epoch PSD Mean')
    plt.grid(True)
    plt.xticks(x_mean,n_xticks)
    Title=group+"_"+subject+"_"+band+"_"+file_sufix
    plt.title(Title)

    plt.legend(loc='upper left')
    
#    plt.show()
    print("!!!saving in: "+taskdir)
    plt.savefig(os.path.join(taskdir,Title+'.pdf'))
    

    return data_df

def plot_task_bands_d_v2(group, subject, taskdir, true_fileid_seq, tasks_extract_l, band=None, file_sufix="e2_PSD_v1", reward_level=0, fileid_stop_code="."):
    ####GET DATA
    #------------------------------------
    #create array of features to plot
    tasks_bands_d=my.deserialize_object(taskdir, group+"_"+subject+"_"+"tasks_bands_d.txt", method="json")


    multiband=False
    if isinstance(band, six.string_types): band = [band]
    if isinstance(band, list) and len(band)>1: multiband=True
    
    #init plot
    plt.close('all')
    plt.figure(1)
    f = plt.gcf()
#    ax=plt.gca()
    f.set_size_inches(18.5, 10.5)
    color_names=[name for name in mcd.CSS4_COLORS]

    for i,b in enumerate(band):
        cn = mcd.CSS4_COLORS[color_names[i]] #color
        
        #create dataframes and save with pandas
        #band="alpha"#choose band to show
        data_df_i=df_tasks_bands(b, tasks_bands_d, true_fileid_seq)
        #sort
        data_df_i.sort_values(['order']) 
        
        #Calculate features and add to tasks_bands_d (ordered lists)
        data_df_i=add_features_df(data_df_i, reward_level=reward_level)
        #SAVE
        df_to_excel(data_df_i, taskdir,group+"_"+subject+"_"+b+"_"+"tasks_df")
        data_df_i.to_pickle(os.path.join(taskdir,group+"_"+subject+"_"+b+"_"+"tasks_df"+".pcl"))
    
    
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
    
    
        
        ##GET COORDINATES
        ##average values:
        x_mean=np.array(range(len(data_df["mean"])))+0.5 #x coordinate of mean
        x_v_lines=x_mean-0.5 #x coordinate of vertical lines
        x_v_lines=np.append(x_v_lines, x_v_lines[-1]+1) 
        #1)band_psd_avg 
        y_mean=data_df["mean"] #y mean value = psd average
        y_std_pos=data_df["mean"]+data_df["std"]
        y_std_neg=data_df["mean"]-data_df["std"]
        #name of x axis tasks
        n_xticks=data_df['fileid'] 
        
    
        
        ##epoch coordinates
        x_e_mean=[] #grey epochs
        y_e_mean=[] #grey epochs
        y_e_std_pos=[] #grey epochs
        y_e_std_neg=[] #grey epochs
        x_e_mean_g=[] #green epochs
        y_e_mean_g=[] #green epochs
        y_e_std_pos_g=[] #green epochs
        y_e_std_neg_g=[] #green epochs
        if not multiband:
            for r in range(len(data_df)): #for each (r)ow
                epochs_n=len(data_df["epoch_a"][r])
                task = data_df["fileid"][r]
                threshold=get_task_threshold(task, data_df, reward_level=reward_level)
                if not threshold: continue
        
                point_s=1/float(epochs_n) #between 0 and one
                for e in range(epochs_n):
                    if not data_df["epoch_a"][r][e]: continue
                    m=data_df["epoch_a"][r][e][0]
                    sd=data_df["epoch_a"][r][e][1]
                    if m >(-1)*4*threshold and m<4*threshold: #LIMITING GRAPH DATA to -4*Threshold to 4*threshold
                        if m>threshold:
                            x_e_mean_g.append(r+e*point_s)
                            y_e_mean_g.append(m)
                            y_e_std_pos_g.append(m+sd)
                            y_e_std_neg_g.append(m-sd)
                        x_e_mean.append(r+e*point_s)
                        y_e_mean.append(m)
                        y_e_std_pos.append(m+sd)
                        y_e_std_neg.append(m-sd)
            
    
        #PLOT COORDINATES
        #plot vlines
        for xc in x_v_lines:
            plt.axvline(x=xc, color="k")
        
        #plot for each epoch
        if not multiband:
            for r in range(len(data_df)):
                epochs_n=len(data_df["epoch_a"][r])
                task = data_df["fileid"][r]
                threshold=get_task_threshold(task, data_df, reward_level=reward_level)
                #plot horizontal lines
                xmin=x_v_lines[r]
                xmax=x_v_lines[r+1]
                plt.hlines(threshold, xmin, xmax,color="r")
        
                #plot add features - text
                #features - 
                bat=data_df.tBAT[r]
        #        absolute_power=data_df["mean"][r]
        #        tonic_increase=data_df.tonic_increase[r]
                nr_epo_on_target=0
                for e in range(epochs_n):
                    if not data_df["epoch_a"][r][e]: continue
                    m=data_df["epoch_a"][r][e][0]
                    sd=data_df["epoch_a"][r][e][1]
                    if m>threshold:
                        nr_epo_on_target+=1
                
                
                x_text=x_mean[r]
                y_text=min(y_e_mean)
        
                text="%tBAT: "+str(round(100*bat,4)) #change based in feature
                text=text+"\n target/total: "+str(nr_epo_on_target)+"/"+str(epochs_n)
                plt.text(x_text, y_text, text, horizontalalignment='center', verticalalignment='center',
                         bbox=dict(boxstyle="round",
                                   ec=(1., 0.5, 0.5),
                                   fc=(1., 0.8, 0.8),
                                   )) 
                #plt.plot(x_text, tonic_increase,'b*', label="")
                
                
        
        #plot epoch means
        if not multiband:
            plt.plot(x_e_mean, y_e_mean,'.', color = '0.75', label='epoch_below_threshold')
        #    plt.fill_between(x_e_mean, y_e_std_pos, y_e_std_neg, color='0.85', alpha=.5)
            plt.plot(x_e_mean_g, y_e_mean_g,'.', color = 'g', label='epoch_above_threshold')
        #    plt.fill_between(x_e_mean_g, y_e_std_pos_g, y_e_std_neg_g, color='g', alpha=.5)
            
        #plot slope
    #    for r in range(len(x_rest)):
    #        plt.plot(x_mean[2*r:2*r+2],y_mean[2*r:2*r+2], 'b-', label ="")
        
        #plot task means
        plt.plot(x_mean, y_mean,'-o', color=cn, label=b+'_'+'task_mean_psd')
        #plt.plot(x_rest, y_rest,'ro', label='absolute_rest_power')
        plt.fill_between(x_mean, y_std_pos, y_std_neg, color=cn, alpha=.5)
        


    plt.xlabel('Tasks')
    if multiband: 
        name='bands_'
        for b in band:
            s_b=list(b)
            name=name+s_b[0]
        band=[name]
    plt.ylabel(band[0] +', 1s epoch PSD Mean')
    plt.grid(True)
    plt.xticks(x_mean,n_xticks)
    Title=group+"_"+subject+"_"+band[0]+"_"+file_sufix
    plt.title(Title)
    plt.legend(loc='upper left')
    
#    plt.show()
    print("!!!saving in: "+taskdir)
    plt.savefig(os.path.join(taskdir,Title+'.pdf'))
    

    return data_df

def plot_subjects(groupdir, true_fileid_seq, tasks_extract_l, band="alpha", file_sufix="e2_PSD_v1", reward_level=0, bad_subjects_l=None, fileid_stop_code="."):
    #Factorial design folder analysis
    group_l=os.listdir(groupdir)
#    groups_bands_d={}
    #features dict
    for g in group_l:
        subjectdir=os.path.join(groupdir, g)
        if not os.path.isdir(subjectdir): continue #test if is a folder
        subject_l=os.listdir(subjectdir)
        for s in subject_l:
            if bad_subjects_l and s in bad_subjects_l: continue
            taskdir=os.path.join(subjectdir, s)
            if not os.path.isdir(taskdir): continue #test if is a folder
            try:
                logger.warning("\n>> PLOT {} {}".format(g, s)) 
                plot_task_bands_d(g,s, taskdir, true_fileid_seq, tasks_extract_l, band=band, file_sufix=file_sufix, reward_level=reward_level, fileid_stop_code=fileid_stop_code)
            except:
                logger.error("\n>> Subject {} must have repeated or no files, Check!".format(s)) 
                continue
            
            
def plot_subjects_v2(groupdir, true_fileid_seq, tasks_extract_l, band=None, file_sufix="e2_PSD_v1", reward_level=0, bad_subjects_l=None, fileid_stop_code="."):
    #Factorial design folder analysis
    group_l=os.listdir(groupdir)
#    groups_bands_d={}
    #features dict
    for g in group_l:
        subjectdir=os.path.join(groupdir, g)
        if not os.path.isdir(subjectdir): continue #test if is a folder
        subject_l=os.listdir(subjectdir)
        for s in subject_l:
            if bad_subjects_l and s in bad_subjects_l: continue
            taskdir=os.path.join(subjectdir, s)
            if not os.path.isdir(taskdir): continue #test if is a folder
            try:
                plot_task_bands_d_v2(g,s, taskdir, true_fileid_seq, tasks_extract_l, band=band, file_sufix=file_sufix, reward_level=reward_level, fileid_stop_code=fileid_stop_code)
            except:
                logger.error("Subject {} must have repeated files, Check!".format(s)) 
                continue


def play_subject(datadir, group="EG", subject="S016"):
    #---DATA DIR
    datadir=datadir#my.get_test_folder(foldername="e2_data")#
    
    #subject file
    group=group
    subject=subject
    subjectdir=os.path.join(group, subject)#"CG/S035"
    filedir=os.path.join(datadir,subjectdir)
    #filetype=".meta"
    taskdir=filedir
    
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
        true_fileid_seq.append(fid.split(".")[0])
    
    #tasks to extract features
    tasks_extract_l=["rest_eo", "alpha_eo"] #[]=load all;chose what files to load
    #get subject df and plot subject tasks
    data_df=plot_task_bands_d(group, subject, taskdir, true_fileid_seq,tasks_extract_l, band="alpha", file_sufix="e2_PSD_v1", reward_level=0, fileid_stop_code=".")
    print(data_df)

    
    
def play_subjects(datadir, band="alpha", protocol="eo"):
     #---DATA DIR
    datadir=datadir#my.get_test_folder(foldername="e2_data_da")#
    groupdir=datadir
    
    #band
    band=band 
    
    #fileid_stop_code
    fileid_stop_code="." #code is sent to plotsuject;  use this at the end of taskname if you want just that file; for BUGs like rest_ec_1 and rest_ec_12
    
    #tasks to extract features
    tasks_extract_l=["_"+protocol+"_"] #chose tasks to extract, always put the baseline, 
    file_sufix=protocol+"_all" #title and file sufix of plots
    
    #threshold reward_level
    reward_level=0
    
    #bad subjects list
    bad_subjects_l=[]
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
    
    
    
    #Plot Subjects 
    plot_subjects(groupdir, true_fileid_seq, tasks_extract_l, band=band, file_sufix=file_sufix, reward_level=reward_level,  bad_subjects_l=bad_subjects_l, fileid_stop_code=fileid_stop_code)


def play_subjects_v2(datadir, band=['alpha','SMR'], protocol='eo'):
     #---DATA DIR
    datadir=datadir#my.get_test_folder(foldername="e2_data_da")#
    groupdir=datadir
    
    #band
    band=band #if list len=1 or string, if list >2 then do other type of graph
    
    #fileid_stop_code
    fileid_stop_code="." #code is sent to plotsuject;  use this at the end of taskname if you want just that file; for BUGs like rest_ec_1 and rest_ec_12
    
    #tasks to extract features
    protocol=protocol
    tasks_extract_l=['_'+protocol+'_'] #chose tasks to extract, always put the baseline, 
    file_sufix=protocol+"_all" #title and file sufix of plots
    
    #threshold reward_level
    reward_level=0
    
    #bad subjects list
    bad_subjects_l=[]
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
    
    
    
    #Plot Subjects 
    plot_subjects_v2(groupdir, true_fileid_seq, tasks_extract_l, band=band, file_sufix=file_sufix, reward_level=reward_level,  bad_subjects_l=bad_subjects_l, fileid_stop_code=fileid_stop_code)


if __name__=="__main__":
     #---DATA DIR
    datadir='/Users/nm.costa/Google_Drive/projects/phd/research/2_THESIS_PUBLICATIONS/thesis/C3_e2_results/results/eeg/e2_study_2_150uV_pz_avgref'
    #my.get_test_folder(foldername="e2_data")#
    #PLAY ONLY ONE SUBJECT
    #play_subject(datadir, group="EG", subject="S016")
    #PLAY ALL SUBJECTS - One band
    #play_subjects(datadir, band="alpha", protocol="ec")
    #PLAY ALL SUBJECTS - Multiple bands
    play_subjects_v2(datadir, band=['lower_alpha','upper_alpha','alpha'], protocol='ec')