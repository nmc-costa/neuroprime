#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Tue Oct 23 11:33:10 2019

@author: nm.costa
"""

import os
import copy
import pandas as pd
#import numpy as np
#import matplotlib.pyplot as plt
import time


# My functions
import neuroprime.src.utils.myfunctions as my
from neuroprime.src.signal_processing.nftalgorithm import nftalgorithm
from neuroprime.src.brain_interfaces.e2_bci.nftclass import nftclass

import logging
logger = logging.getLogger(__name__)
logger.info('Logger started')



"""PIPELINES"""
#UPDATE nftclass.py pipeline to work only offline
#NOTE: you could have only created new class to work with nftalgorithm, but in that way you have to do a new init(), this way you just have to adapt
class nftclass_offline(nftclass):
    def init_processing_algorithm(self, feature="SMR"):
        """
        UPDATE TO OFFLINE
        """
        self.logger.info("\n>> ***init_processing_algorithm***")
        start_time = time.time()
        ###INIT nftalgorithm

        try:
            #ASSERT DATA VARS (GET FROM .meta file)
            amp_fs=1000 #Hz
            amp_chs=["Fp1", "Fz", "F3", "F7", "FT9", "FC5", "FC1", "C3", "T7", "TP9", "CP5", "CP1", "Pz", "P3", "P7", "O1", "Oz", "O2", "P4", "P8", "TP10", "CP6", "CP2", "C4", "T8", "FT10", "FC6", "FC2", "F4", "F8", "Fp2"] #"Channels":
            self.amp_ref_channels=['Cz'] #"MANUAL_AMP_REF_CH":
            self.ch_names=amp_chs
            self.blocksize=int((self.blocktime*1000)/amp_fs) #samples - samples to add to ringbuffer
            self.threshold_reward_level=0 #WARNING: ZERO OBLIGATORY FOR GETTING THE MEAN only for each epoch; zero = *sd :mean+ (0)*sd;
            self.threshold_inhibit_level=self.feedback_reward_level=self.feedback_inhibit_level=0


            ##INIT nftalgorithm class
            self.processingclass=nftalgorithm(amp_fs=amp_fs, amp_chunksize=self.chunksize, amp_chs=amp_chs, blocksize=self.blocksize, window_time=self.window_time, calculate_iaf=self.calculate_iaf, feature=feature, ch_names=self.ch_names)

            #Change some INIT vars
            self.processingclass.subsample=self.subsample
            self.processingclass.l_freq=self.l_freq
            self.processingclass.h_freq=self.h_freq
            self.processingclass.n_fft=self.n_fft
            self.processingclass.n_per_seg=self.n_per_seg
            self.processingclass.n_overlap=self.n_overlap
            self.processingclass.rej_max_peaktopeak=self.rej_max_peaktopeak
            self.processingclass.rej_min_peaktopeak=self.rej_min_peaktopeak
            self.processingclass.pink_max_r2=self.pink_max_r2
            self.processingclass.select_chs=self.select_chs
            self.processingclass.amp_ref_channels=self.amp_ref_channels#initbciclass #important
            self.processingclass.ref_channels=self.ref_channels
            self.processingclass.threshold_reward_level=self.threshold_reward_level
            self.processingclass.threshold_inhibit_level=self.threshold_inhibit_level
            self.processingclass.feedback_reward_level=self.feedback_reward_level
            self.processingclass.feedback_inhibit_level=self.feedback_inhibit_level

            #INIT METHODS before main routine
            self.processingclass.init_methods()
            #initial state of all the init_methods
    #        self.processingclass_initial_state=copy.deepcopy(self.processingclass)
        except Exception as e:
            raise RuntimeError("\n>> init_processing_algorithm had some problem {}".format(e))

        end_time = time.time()
        elapsed_time = end_time-start_time
        self.logger.info("\n>> ***init_processing_algorithm***ELAPSED TIME: {}".format(elapsed_time))



"""FUNCTIONS"""


def df_to_excel(DataFrame, filedir,filename):
    logger.warning("TRYING TO SAVE...")
    writer = pd.ExcelWriter(os.path.join(filedir,filename)+'_features.xlsx')
    DataFrame.to_excel(writer, 'Sheet1')
    writer.save()

def df_bands(reward_bands, inhibit_bands, filedir,filename):
    df_reward_bands=pd.DataFrame(reward_bands)
    df_reward_bands_T=df_reward_bands.transpose()
    df_inhibit_bands=pd.DataFrame(inhibit_bands)
    df_inhibit_bands_T = df_inhibit_bands.transpose()
    df_result_T=pd.concat([df_reward_bands_T,df_inhibit_bands_T])
    print df_result_T
#    df_to_excel(df_result_T, filedir,filename)
    return df_result_T

def df_subject(bands_d, true_fileid_seq):
    data_a=[]
    for i, fid in enumerate(true_fileid_seq):
        if fid in bands_d.keys():
            if bands_d[fid]:
                for band in bands_d[fid]:
                    if bands_d[fid][band]["epoch_a"]:
                        data_a.append( {"order":i, 'fileid':fid, "band":band, "mean":bands_d[fid][band]["threshold_mean"], "std": bands_d[fid][band]["threshold_std"], "epoch_a": bands_d[fid][band]["epoch_a"]} )
                    else:
                        data_a.append( {"order":i, 'fileid':fid, "band":band, "mean":bands_d[fid][band]["threshold_mean"], "std": bands_d[fid][band]["threshold_std"] } )
            else:
                data_a.append({"order":None, 'fileid':fid, "error":"processing"}) #missing file from folder
        else:
            data_a.append({"order":None, 'fileid':fid, "error":"missing"}) #missing file from folder
    data_df= pd.DataFrame(data_a)
    return data_df

def get_filenamesequence(files_l, fileid_seq):
    ld=files_l #os.listdir(filesdir)
    fnseq={}
    for fid in fileid_seq:
        found=False
        for fn in ld:
            if not fn.find(fid)==-1:
                found=True
                fnseq[fid]=fn #Discriptor = NAme
                break
        if not found:
            fnseq[fid]= None
            logger.error("#ERROR: MISSING FILE WITH THE FOLLOWING DISCRIPTOR: "+fid)
    return fnseq

def get_bands_processing(PROCESSING_PIPELINE, filepath, filetype, taskname="DA",routine="offline"):
    """nftclass+nftalgorithm type of pipelines"""
    
    logger.info("!PLAY Processing!..."+filepath)
    
    #PROCESSING CLASS INITIAL STATE 
    local_processing_pipeline=copy.deepcopy(PROCESSING_PIPELINE) #don't alter PROCESSING_PIPELINE object
    reward_bands, inhibit_bands=None, None
    
    #PLAY ROUTINE
    processing_finished, _ = local_processing_pipeline.play_routine(filepath=filepath, filetype=filetype, taskname=taskname, routine=routine)
    if not processing_finished:
       logger.error("PROCESSING DID NOT END - Feature CHs must be  with to mutch noise - check Chs")
       return reward_bands, inhibit_bands, local_processing_pipeline, processing_finished
    #OUTPUT RESULTS (NEEDS TO BE A DEEPCOPY to SEVER CONNECTION WITH PIPELINE)
    reward_bands=copy.deepcopy(local_processing_pipeline.reward_bands)
    inhibit_bands=copy.deepcopy(local_processing_pipeline.inhibit_bands)
    
    return reward_bands, inhibit_bands, local_processing_pipeline, processing_finished


def play_feature_extraction(datadir, outdir, pipe="pz_avgref", rej_max_peaktopeak = 150e-6, rej_min_peaktopeak = 0.5e-6):
    #---DATA DIR
    datadir=datadir#'/Volumes/Seagate/e2_priming/e2_data'#my.get_test_folder(foldername="e2_data")#
    pipe=pipe #"pz_comref""pz_avgref"
#    study='study_2_150uV'
    outdir=outdir#'/Volumes/Seagate/e2_priming/e2_'+study+"_"+pipe#my.get_test_folder(foldername="e2_data_da")#
    #---PROCESSING PIPELINE 
    ###use NFT processing pipeline offline
    nft=nftclass_offline()
    if pipe=="pz_avgref":
        #REINIT VARS (same as in e2_bci.py, or change accordingly)
        nft.PROTOCOL_FEATURE = "allbands_Pz_pipeline" #"alpha" #"allbands_Pz_pipeline"
        nft.select_chs =['Fp1','Fp2','Fz','Cz','Pz'] #chs used throught the processing #NOTE: Include Fp1 and Fp2 for rejection of blinks and saccades
        nft.ref_channels = "average"
        nft.pink_max_r2 = None #0.95 #None : Don't remove noisysignal epoch
        nft.rej_max_peaktopeak = rej_max_peaktopeak #V
        nft.rej_min_peaktopeak = rej_min_peaktopeak #V
    if pipe=="pz_comref":#used on online nft
        #REINIT VARS (same as in e2_bci.py, or change accordingly)
        nft.PROTOCOL_FEATURE = "allbands_Pz_pipeline" #"alpha" #"allbands_Pz_pipeline"
        nft.select_chs =['Fp1','Fp2','Fz','Pz'] #chs used throught the processing #NOTE: Include Fp1 and Fp2 for rejection of blinks and saccades
        nft.ref_channels = []
        nft.pink_max_r2 = None #0.95 #None : Don't remove noisysignal epoch
        #artifact rejection
        nft.rej_max_peaktopeak = rej_max_peaktopeak #V
        nft.rej_min_peaktopeak = rej_min_peaktopeak #V
    #INIT NFT ALGORITHM
    nft.init_processing_algorithm(feature=nft.PROTOCOL_FEATURE)#
    PROCESSING_PIPELINE=nft.processingclass #WARNING use copy.deepcopy() when passing
    
    ###Use other pipeline with same nftclass and nftalgorithm structure (EXAMPLE)
    #from neuroprime.src.signal_processing.nftalgorithm import nftalgorithm as eegpipeline#use specific pipeline
    ##init
    #PROCESSING_PIPELINE=eegpipeline()
    ##change init vars
    #PROCESSING_PIPELINE.serialize=False
    ##init methods from init vars
    #PROCESSING_PIPELINE.init_methods()
    
    #---FACTORIAL DA DESIGN
    #Init vars
    filetype=".meta"
    fileid_seq=["rest_ec_1.meta","rest_eo_2.meta","alpha_eo_3.meta", #b1
                "rest_ec_4.meta", "rest_eo_4.meta","breathingv6_ec_4.meta", "breathingv6_eo_4.meta","imageryv6_ec_4.meta", "imageryv6_eo_4.meta","whmv1_ec_4.meta","whmv1_eo_4.meta","alpha_ec_5.meta","alpha_eo_5.meta",#b2
                "rest_ec_6.meta", "rest_eo_6.meta","breathingv6_ec_6.meta", "breathingv6_eo_6.meta","imageryv6_ec_6.meta", "imageryv6_eo_6.meta","whmv1_ec_6.meta","whmv1_eo_6.meta","alpha_ec_7.meta","alpha_eo_7.meta",#b3
                "rest_ec_8.meta", "rest_eo_8.meta","breathingv6_ec_8.meta", "breathingv6_eo_8.meta","imageryv6_ec_8.meta", "imageryv6_eo_8.meta","whmv1_ec_8.meta","whmv1_eo_8.meta","alpha_ec_9.meta","alpha_eo_9.meta",#b4
                "rest_ec_10.meta", "rest_eo_10.meta","breathingv6_ec_10.meta", "breathingv6_eo_10.meta","imageryv6_ec_10.meta", "imageryv6_eo_10.meta","whmv1_ec_10.meta","whmv1_eo_10.meta","alpha_ec_11.meta","alpha_eo_11.meta",#b5
                "rest_ec_12.meta","rest_eo_13.meta","alpha_eo_14.meta"#b6
                ]
    #Try only with [ec_1,...]
    #Factorial design folder analysis
    groupdir=datadir
    out_groupdir=outdir
    my.assure_path_exists(out_groupdir)
    group_l=os.listdir(groupdir)
    groups_bands_d={}
    groups_psd_d={}
    for g in group_l:
        subjectdir=os.path.join(groupdir, g)
        if not os.path.isdir(subjectdir): continue #test if is a folder
        out_subjectdir=os.path.join(out_groupdir, g)
        my.assure_path_exists(out_subjectdir)
        subject_l=os.listdir(subjectdir)
        subjects_bands_d={}
        subjects_psd_d={}
        for s in subject_l:
            taskdir=os.path.join(subjectdir, s)
            if not os.path.isdir(taskdir): continue #test if is a folder
            out_taskdir=os.path.join(out_subjectdir, s)
            my.assure_path_exists(out_taskdir)
            task_l=os.listdir(taskdir)
            tasks_bands_d={}
            tasks_psd_d={}
            for t in task_l:
                filedir=os.path.join(taskdir, t)
                if not os.path.isdir(filedir): continue #test if is a folder
                out_filedir=os.path.join(out_taskdir, t)
                my.assure_path_exists(out_filedir)
                file_l=[ name for name in os.listdir(filedir) if os.path.isfile(os.path.join(filedir, name)) ] #get only files
                
                
                #PROCESSING
                fnseq=get_filenamesequence(file_l, fileid_seq) #dict as no sequence
                true_fileid_seq=[]
                for fid in fileid_seq:
                    if fid in fnseq:
                        true_fileid_seq.append(fid.split(".")[0])
                bands_d={}
                subtask_psd_d={}
                reward_bands_d, inhibit_bands_d={},{}
                for k in fnseq:
                    f=fnseq[k] #f.meta
                    if f: #if file exists
                        fn=f.split(".")[0]
                        filepath = os.path.join(filedir, f)
                        fid=k.split(".")[0]
                        taskname = fid
                        #play pipeline - 
                        reward_bands, inhibit_bands, processing_pipeline, processing_finished=get_bands_processing(PROCESSING_PIPELINE, filepath, filetype, taskname=taskname)
                        #(WARNING:deepcopy)
                        reward_bands, inhibit_bands=copy.deepcopy(reward_bands), copy.deepcopy(inhibit_bands)
                        #save #serialize pipeline
                        try:
                            my.serialize_object(processing_pipeline, out_filedir,fn+"_mean_epoch_pipeline_vars", method="pickle")
                            my.serialize_object(processing_pipeline, out_filedir,fn+"_mean_epoch_pipeline_vars", method="json")
                        except:
                            pass
                        #get epoch_psd_average bands
                        reward_bands_d[fid]=reward_bands 
                        inhibit_bands_d[fid]=inhibit_bands
                        if reward_bands and inhibit_bands:
                            bands_d[fid]=reward_bands
                            bands_d[fid].update(inhibit_bands)
                        elif reward_bands:
                            bands_d[fid]=reward_bands
                        elif inhibit_bands:
                            bands_d[fid]=inhibit_bands
                        else:
                            bands_d[fid]=None
                        
                        #get psd mean
                        subtask_psd_d[fid]={'psd':None, 'freqs':None}
                        
                        #EXTRACT ALL EPOCHS FEATURES 
                        #-Reuse pipeline class epoch psds=(n_epochs, n_channels, n_freqs)
                        if processing_finished:
                            #save also psd mean before using it
                            try:
                                subtask_psd_d[fid]['psd']=copy.deepcopy(processing_pipeline.psd.tolist()) #average of epochs from numpy to list
                                subtask_psd_d[fid]['freqs']=copy.deepcopy(processing_pipeline.psd.tolist())
                            except:
                                pass
                            epoch_bands_d ={}
                            for band in bands_d[fid]:
                                bands_d[fid][band]["epoch_a"] = []
                            for i,psd in enumerate(processing_pipeline.psds): #ASSUMING PSDS in order
                                #extract epoch psd feature
                                processing_pipeline.psd=psd #epoch_psd
                                processing_pipeline.epoch_psd_feature_extraction( processing_pipeline.psd_select_chs_ordered, processing_pipeline.psd_picks, processing_pipeline.psd_ch_feature_picks, processing_pipeline.psd_ch_iaf_picks )
                                #ADD EPOCH FEATURES TO BANDS dict
                                if processing_pipeline.noisysignal:
                                    processing_pipeline.noisysignal=False
                                    for band in bands_d[fid]:
                                        bands_d[fid][band]["epoch_a"].append(None)
                                    continue
                                #epoch bands (WARNING:deepcopy)
                                reward_bands_e, inhibit_bands_e = copy.deepcopy(processing_pipeline.reward_bands), copy.deepcopy(processing_pipeline.inhibit_bands)
                                epoch_bands_d[i]=reward_bands_e
                                epoch_bands_d[i].update(inhibit_bands_e)
                                for band in bands_d[fid]:
                                    bands_d[fid][band]["epoch_a"].append([epoch_bands_d[i][band]["threshold_mean"], epoch_bands_d[i][band]["threshold_std"]]) #offline pipe adds threshold name tag, online adds feedback



                #---SAVE : SERIALIZE FILEDIR VARS
                save_files=False
                if save_files:
                    try:
                        my.serialize_object(reward_bands_d, out_filedir, "mean_epoch_reward_bands_d", method="json")
                        my.serialize_object(inhibit_bands_d, out_filedir, "mean_epoch_inhibit_bands_d", method="json")
                        my.serialize_object(bands_d, out_filedir, "bands_d", method="json")
                        my.serialize_object(subtask_psd_d, out_filedir, "task_psd_d", method="json")
                    except:
                        pass
                    #all bands
                    data_subject_df=df_subject(bands_d, true_fileid_seq)
                    try:
                        data_subject_df.to_pickle(os.path.join(out_filedir,'all_analysis_df.pcl'))
                        df_to_excel(data_subject_df, out_filedir,'all_analysis_df')
                    except:
                        pass
                tasks_bands_d[t]=bands_d
                tasks_psd_d[t]=subtask_psd_d
            #---SERIALIZE TASKDIR VARS
            save_tasks=True
            if save_tasks:
                try:
                    my.serialize_object(tasks_bands_d, out_taskdir,g+"_"+s+"_"+ "tasks_bands_d", method="json")
                    my.serialize_object(tasks_psd_d, out_taskdir,g+"_"+s+"_"+ "tasks_psd_d", method="json")
                except:
                    pass
            subjects_bands_d[s]=tasks_bands_d
            subjects_psd_d[s]=tasks_psd_d
        #---SERIALIZE SUBJECTDIR VARS
        save_subjects=False
        if save_subjects:
            try:
                my.serialize_object(subjects_bands_d, out_subjectdir, "subjects_bands_d", method="json")
                my.serialize_object(subjects_psd_d, out_subjectdir, "subjects_psd_d", method="json")
            except:
                pass
        groups_bands_d[g]=subjects_bands_d
        groups_psd_d[g]=subjects_psd_d
    #---SERIALIZE GROUPDIR VARS-TODO
    save_groups=True
    if save_groups:
        try:
            my.serialize_object(groups_bands_d, out_groupdir, "groups_bands_d", method="json")
            my.serialize_object(groups_psd_d, out_groupdir, "groups_psd_d", method="json")
        except:
            pass


if __name__=="__main__":
    #---DATA DIR
    datadir='/Volumes/Seagate/e2_priming/e2_data_clean'#'/Volumes/Seagate/e2_priming/e2_data'#my.get_test_folder(foldername="e2_data")#
    pipe="pz_avgref" #"pz_comref""pz_avgref"
    rej_max_peaktopeak = 150e-6
    rej_min_peaktopeak = 0.5e-6
    study='study_2_150uV'
    outdir='/Volumes/Seagate/e2_priming/e2_'+study+"_"+pipe#'/Volumes/Seagate/e2_priming/e2_'+study+"_"+pipe#my.get_test_folder(foldername="e2_data_da")#
    play_feature_extraction(datadir, outdir, pipe=pipe, rej_max_peaktopeak = rej_max_peaktopeak, rej_min_peaktopeak = rej_min_peaktopeak)
