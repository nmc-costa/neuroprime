#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Mon Jul 30 13:58:31 2018


BCI to play experiment

@author: nm.costa
"""

from __future__ import (absolute_import, division, print_function)
from builtins import * #all the standard builtins python 3 style

import time
#import os
import random
import numpy as np
#import sys
import copy
import ast
#import json
## My functions
import neuroprime.src.utils.myfunctions as my
#from functions.nftalgorithm import nftalgorithm
# My classes
from neuroprime.src.initbciclass import initbciclass, get_amp_subprocess
from neuroprime.src.brain_interfaces.e2_bci.restclass import restclass
from neuroprime.src.brain_interfaces.e2_bci.nftclass import nftclass
from neuroprime.src.brain_interfaces.e2_bci.primeclass import primeclass
from neuroprime.src.brain_interfaces.e2_bci.reportclass import reportclass
#LOGGING -
import logging
#Config this script lo show sobmodules loggers
#logging.basicConfig(level=logging.INFO)
#Module logger
logger = my.setlogfile(modulename=__name__, setlevel=logging.INFO, disabled=True)

#debugging
#import pdb


#GLOBAL VARS
SAVE_FOLDER='e2_data' #DESKTOP
SAVE_BY_TASK=True #EEG True:save task by task; False:save full session
#add amps
ADD_AMPS_ON=True # GSR AND HR
ADD_AMPS_SAVE_BY_TASK= False #Saving at the end - taking too mutch time saving by task
#stimulus time
MASTER_STIMULUS_TIME=90 #s
#update threshold at NFT end
MASTER_UPDATE_THRESHOLD_AFTERTASK = True #(see nftclass.threshold_update_aftertask =>needs to be true to update)
NFT_PROCESS_CHS=['Fp1','Fp2', 'Fz','Pz'] #chs used throught the processing #NOTE: Include Fp1 and Fp2 for rejection of blinks and saccades
AMP_MANUAL_REF=['Cz']
RE_REFERENCE =[]##online is not a good idea to have average reference(unseen noise)
THRESHOLD_REWARD_LEVEL=-0.38 #std (-0.38*std => 65% above) #INITIAL THRESHOLD
TOTAL_BLOCK_NR=6
FILELOGGER = True

def bci():
    st =time.time()
    bci = initbciclass(filelogger=FILELOGGER, logfolder='e2_data/')
    rest = restclass(filelogger=FILELOGGER, logfolder='e2_data/')
    nft = nftclass(filelogger=FILELOGGER, logfolder='e2_data/')
    prime = primeclass(filelogger=FILELOGGER, logfolder='e2_data/')
    report = reportclass()
    et =time.time() - st
    logger.info("!!ELAPSED TIME INIT CLASS BCICLASS!! : {}".format(et))


    #RANDOM VARS
    random.seed() #None or no argument seeds from current time or from an operating system specific randomness source if available

    try:#catch errors and close

        #2RE-INIT Vars
        #Manual REF
        bci.amp_ref_channels=rest.amp_ref_channels=nft.amp_ref_channels=prime.amp_ref_channels=AMP_MANUAL_REF

        #SAVE BY TASK
        bci.SAVE_TASK=rest.SAVE_TASK=nft.SAVE_TASK=prime.SAVE_TASK=report.SAVE_TASK=SAVE_BY_TASK #True, save file by task or False, by session (WARNING: ALL TASKS SHOULD RESPECK THE SAME METHOD)
        folder_path=my.get_test_folder(foldername=SAVE_FOLDER) #folderpath
        #Start dialogue (alphabetic order)
        info={'EXP_VERSION': 'e2_bci', 'SAVE_FOLDER': folder_path,'SAVE': ['yes', 'no'], 'NFT_PROCESS_CHS': str(NFT_PROCESS_CHS),
              'subject':1, 'session':1,
              'pg': ['EG', 'CG'], #['EG', 'CG', 'random'],
              'feat': ['a','s','d','t','b','g'],
              'eyes': ['ec','eo'],
              'prime': ['BM', 'IM', 'WHM'],
              "technician": "Nuno Costa"}
        title='experiment 2'
        fixed=['EXP_VERSION']
        newinfo=my.gui_dialogue(info=info,title=title,fixed=fixed)
        #random group choice - randomize EG and CG-not good because never know how it can end - using pseudo randomization in excel
#        if newinfo['pg'] =="random":
#           newinfo['pg'] = random.choice(['EG','CG'])
        #SAVE VARS
        bci.FOLDER_DATA=rest.FOLDER_DATA=nft.FOLDER_DATA=prime.FOLDER_DATA= newinfo['SAVE_FOLDER']
        bci.GROUP=rest.GROUP =nft.GROUP =prime.GROUP = newinfo['pg']  #EG or CG
        bci.SUBJECT_NR =rest.SUBJECT_NR =nft.SUBJECT_NR = prime.SUBJECT_NR = newinfo['subject']
        bci.SESSION_NR=rest.SESSION_NR  =nft.SESSION_NR =prime.SESSION_NR = newinfo['session']
        bci.NFT_PROCESS_CHS=ast.literal_eval(newinfo['NFT_PROCESS_CHS'])

        if newinfo['SAVE']=='yes': bci.SAVE=rest.SAVE=nft.SAVE=prime.SAVE= True
        if newinfo['SAVE']=='no': bci.SAVE=rest.SAVE=nft.SAVE=prime.SAVE= False
        report.SAVE=False#Nao grave

        #TOTAL BLOCK NUMBER
        bci.TOTAL_BLOCK_NR=rest.TOTAL_BLOCK_NR=nft.TOTAL_BLOCK_NR=prime.TOTAL_BLOCK_NR= TOTAL_BLOCK_NR



        ###INIT BCI
        st=time.time()

        #INIT SAVING
        rest.init_io()
        prime.init_io()
        nft.init_io()
        report.init_io()

        #INIT PRESENTATION AND ACQUISITION, PATCH NFT AND prime CLASS WITH only one AMP and PYFF object
        bci.on_init()



        #add subprocess amps - limitation - using only the first filname - #TODO: add updates
        if ADD_AMPS_ON:
            #clean up any old process
            import multiprocessing
            for p in multiprocessing.active_children():
                print("TERMINATING PROCESS: ", p.name, p.pid)
                p.terminate()#force termination
                p.join()#wait to terminate
            if bci.SAVE:#add james folder to path
                bci.TASK="JAMES"
                bci.update_file_path()
            gsr=get_amp_subprocess(filepath=bci.FILENAME_EEG_PATH, save_task=ADD_AMPS_SAVE_BY_TASK , process_name='GSR')
            gsr.configure(stream_type='GSR', stream_server='lsl', lsl_amp_name='GSR', lsl_marker_name="PyffMarkerStream")
            hr=get_amp_subprocess(filepath=bci.FILENAME_EEG_PATH, save_task=ADD_AMPS_SAVE_BY_TASK , process_name='HR')
            hr.configure(stream_type='HR', stream_server='lsl', lsl_amp_name='HR', lsl_marker_name="PyffMarkerStream")
            time.sleep(10)
            if bci.SAVE:#go to james folder to path
                bci.TASK=""
                bci.update_file_path()




        #1.PRESENTATION PATCHING
        rest.pyff = bci.pyff
        prime.pyff = bci.pyff
        nft.pyff = bci.pyff
        report.pyff=bci.pyff
        #2.ACQUISITON PATCHING
        rest.amp = bci.amp
        prime.amp = bci.amp
        nft.amp = bci.amp
        report.amp=bci.amp



        ##DEFINE VARS
        #bci vars
        bci.thresholdbuffer_eo=[]
        bci.thresholdbuffer_ec=[]
        #TASK protocol eyes
        if newinfo['eyes'] =="eo":
            bci.protocol_eyes_l=["eyes_closed_v2", "eyes_open_v2", "eyes_open",
                                 "eyes_open", "eyes_open",
                                 "eyes_closed", "eyes_closed",
                                 "eyes_closed", "eyes_closed",
                                 "eyes_open", "eyes_open",
                                 "eyes_closed_v2", "eyes_open_v2", "eyes_open"]
        if newinfo['eyes'] =="ec":
             bci.protocol_eyes_l=["eyes_closed_v2", "eyes_open_v2", "eyes_open",
                                 "eyes_closed", "eyes_closed",
                                 "eyes_open", "eyes_open",
                                 "eyes_open", "eyes_open",
                                 "eyes_closed", "eyes_closed",
                                 "eyes_closed_v2", "eyes_open_v2", "eyes_open"]

        #rest vars
        rest.PROTOCOL_TYPE =  "REST" #
        rest.PROTOCOL_DESIGN = "normal"

        #prime VARS
        if newinfo['prime'] =="BM": prime.audiostimulus_l = ["breathingv6.ogg", "imageryv6.ogg", "breathingv6.ogg", "imageryv6.ogg"]
        if newinfo['prime'] =="IM": prime.audiostimulus_l = ["imageryv6.ogg", "breathingv6.ogg", "imageryv6.ogg", "breathingv6.ogg"]
        if newinfo['prime'] =="WHM": prime.audiostimulus_l = ["imageryv6.ogg","whmv1.ogg", "whmv1.ogg", "whmv1.ogg"]
        prime.PROTOCOL_TYPE =  "PRIME" #
        prime.PROTOCOL_DESIGN = "normal" #normal, test

        #REPORT VARS
        #None

        #NFT VARS
        if newinfo['feat'] =="a": nft.PROTOCOL_FEATURE = "alpha"
        if newinfo['feat'] =="s": nft.PROTOCOL_FEATURE = "SMR"
        nft.PROTOCOL_TYPE =  "NFT" #
        nft.PROTOCOL_DESIGN = "normal" # Normal
        #online vars (advanced: change in nftclass)
        nft.adaptative_threshold_aftertask=MASTER_UPDATE_THRESHOLD_AFTERTASK
        nft.select_chs =bci.NFT_PROCESS_CHS #chs used throught the processing #NOTE: Include Fp1 and Fp2 for rejection of blinks and saccades
        nft.ref_channels = RE_REFERENCE
        nft.threshold_reward_level= THRESHOLD_REWARD_LEVEL
        #INIT NFT ALGORITHM
        nft.init_processing_algorithm(feature=nft.PROTOCOL_FEATURE)


        et =time.time() - st
        logger.info("!!ELAPSED TIME INIT METHODS BCICLASS!! : {}".format(et))

        ###EXPERIMENT SESSION
        bci.start_time=time.time()

        #class initial stae
        nft.serialize(objectname="nftclass_init_state") #BUG: #Solved puttingin init state
        prime.serialize(objectname="primeclass_init_state")
        rest.serialize(objectname="restclass_init_state")
        bci.serialize(objectname="bci_init_state")

        #master stim time for tasks
        master_stim_1= MASTER_STIMULUS_TIME #s #rest eo & ec
        master_stim_2= 2*master_stim_1 #s #rest, prime and nft full task

        #raise RuntimeError("END EXPERIMENT")

        #1. BLOCK IN
        bci.BLOCK_NR = 1
        rest.BLOCK_NR=prime.BLOCK_NR=nft.BLOCK_NR=bci.BLOCK_NR

        #task 1: rest olhos fechados
        bci.TASK_NR=1
        rest.TASK_NR=prime.TASK_NR=nft.TASK_NR=bci.TASK_NR
        rest.STIM_TIME= master_stim_1 #s
        rest.protocol_eyes=bci.protocol_eyes_l[bci.TASK_NR-1]
        rest.START_WAIT_FOR_KEY=True
        if ADD_AMPS_ON:
            gsr.start()
            hr.start()
        rest.on_play_check(markernumerate=bci.TASK_NR) #rest.on_play(markernumerate=bci.TASK_NR) #or nft.off_rest_bci
        if ADD_AMPS_ON:
            gsr.stop()
            hr.stop()
        baseline_data=np.array(rest.amp.amp.samples_buffer)#mushu format: numpy array samples X channels
        baseline_markers=rest.amp.amp.markers_buffer_mushu#mushu format: list #timecorrected
        #initial bands thresholds eyes closed(ec)
        initial_reward_bands_ec, initial_inhibit_bands_ec = nft.baseline_thresholds(data=baseline_data, markers=baseline_markers, markernumerate=bci.TASK_NR)
        update_reward_bands_ec, update_inhibit_bands_ec=initial_reward_bands_ec, initial_inhibit_bands_ec
        bci.thresholdbuffer_ec.append(update_reward_bands_ec[nft.PROTOCOL_FEATURE]['threshold'])


        #task 2: rest olhos abertos
        bci.TASK_NR =2
        rest.TASK_NR=prime.TASK_NR=nft.TASK_NR=bci.TASK_NR
        rest.STIM_TIME= master_stim_1 #s
        rest.protocol_eyes=bci.protocol_eyes_l[bci.TASK_NR-1]
        rest.START_WAIT_FOR_KEY=True
        if ADD_AMPS_ON:
            gsr.start()
            hr.start()
        rest.on_play_check(markernumerate=bci.TASK_NR) #rest.on_play(markernumerate=bci.TASK_NR) #or nft.off_rest_bci
        if ADD_AMPS_ON:
            gsr.stop()
            hr.stop()
        baseline_data=np.array(rest.amp.amp.samples_buffer)#mushu format: numpy array samples X channels
        baseline_markers=rest.amp.amp.markers_buffer_mushu#mushu format: list #timecorrected
        #initial bands thresholds eyes open(eo)
        initial_reward_bands_eo, initial_inhibit_bands_eo = nft.baseline_thresholds(data=baseline_data, markers=baseline_markers, markernumerate=bci.TASK_NR)
        update_reward_bands_eo, update_inhibit_bands_eo=initial_reward_bands_eo, initial_inhibit_bands_eo
        bci.thresholdbuffer_eo.append(update_reward_bands_eo[nft.PROTOCOL_FEATURE]['threshold'])

        #task 3: nft eyes open
        bci.TASK_NR =3
        rest.TASK_NR=prime.TASK_NR=nft.TASK_NR=bci.TASK_NR
        nft.STIM_TIME= master_stim_2 #s
        nft.protocol_eyes=bci.protocol_eyes_l[bci.TASK_NR-1]
        nft.START_WAIT_FOR_KEY=False
        nft.initial_reward_bands, nft.initial_inhibit_bands = update_reward_bands_eo, update_inhibit_bands_eo
        if ADD_AMPS_ON:
            gsr.start()
            hr.start()
        nft.on_play_check(markernumerate=bci.TASK_NR)#nft.on_play(markernumerate=bci.TASK_NR)
        if ADD_AMPS_ON:
            gsr.stop()
            hr.stop()
        #update thresholds
        if MASTER_UPDATE_THRESHOLD_AFTERTASK:
            update_reward_bands_eo[nft.PROTOCOL_FEATURE]['threshold']=nft.new_threshold
        bci.thresholdbuffer_eo.append(update_reward_bands_eo[nft.PROTOCOL_FEATURE]['threshold'])



        #task report:  (dont update task_nr because files not saved)
        report.START_WAIT_FOR_KEY=True
        report.on_play_check()
        #raise RuntimeError("Terminate Experiment") #for tests




        #2.Block of stimulus ( FACTORIAL DESIGN)
        for i,audio in enumerate(prime.audiostimulus_l):
            #UPATE BLOCK
            bci.BLOCK_NR+=1
            rest.BLOCK_NR=prime.BLOCK_NR=nft.BLOCK_NR=bci.BLOCK_NR
            #eyes protocol copy of previous update
            irb_eo, iib_eo = copy.copy(update_reward_bands_eo), copy.copy(update_inhibit_bands_eo)
            irb_ec, iib_ec = copy.copy(update_reward_bands_ec), copy.copy(update_inhibit_bands_ec)

            #PLAY NEW BLOCK
            if bci.GROUP=="EG":
                #task 1:prime
                bci.TASK_NR+=1
                rest.TASK_NR=prime.TASK_NR=nft.TASK_NR=bci.TASK_NR
                prime.STIM_TIME= master_stim_2 #s
                prime.protocol_eyes=bci.protocol_eyes_l[bci.TASK_NR-1]
                prime.START_WAIT_FOR_KEY=True
                if ADD_AMPS_ON:
                    gsr.start()
                    hr.start()
                prime.on_play_check( audiostimulus=audio, markernumerate=bci.TASK_NR)
                if ADD_AMPS_ON:
                    gsr.stop()
                    hr.stop()
                #task 2: NFT
                bci.TASK_NR+=1
                rest.TASK_NR=prime.TASK_NR=nft.TASK_NR=bci.TASK_NR
                nft.STIM_TIME= master_stim_2 #s
                nft.protocol_eyes=bci.protocol_eyes_l[bci.TASK_NR-1]
                nft.START_WAIT_FOR_KEY=False
                nft.initial_reward_bands, nft.initial_inhibit_bands = irb_eo, iib_eo
                if nft.protocol_eyes=="eyes_closed": nft.initial_reward_bands, nft.initial_inhibit_bands = irb_ec, iib_ec
                if ADD_AMPS_ON:
                    gsr.start()
                    hr.start()
                nft.on_play_check(markernumerate=bci.TASK_NR)#nft.on_play(markernumerate=bci.TASK_NR)
                if ADD_AMPS_ON:
                    gsr.stop()
                    hr.stop()
                #update nft thresholds
                if nft.protocol_eyes=="eyes_open":
                    if MASTER_UPDATE_THRESHOLD_AFTERTASK:
                        update_reward_bands_eo[nft.PROTOCOL_FEATURE]['threshold']=nft.new_threshold
                    bci.thresholdbuffer_eo.append(update_reward_bands_eo[nft.PROTOCOL_FEATURE]['threshold'])
                if nft.protocol_eyes=="eyes_closed":
                    if MASTER_UPDATE_THRESHOLD_AFTERTASK:
                        update_reward_bands_ec[nft.PROTOCOL_FEATURE]['threshold']=nft.new_threshold
                    bci.thresholdbuffer_ec.append(update_reward_bands_ec[nft.PROTOCOL_FEATURE]['threshold'])


            elif bci.GROUP=="CG":
                #task 1: rest
                bci.TASK_NR+=1
                rest.TASK_NR=prime.TASK_NR=nft.TASK_NR=bci.TASK_NR
                rest.STIM_TIME= master_stim_1 #s
                rest.protocol_eyes=bci.protocol_eyes_l[bci.TASK_NR-1]
                rest.START_WAIT_FOR_KEY=True
                if ADD_AMPS_ON:
                    gsr.start()
                    hr.start()
                rest.on_play_check(markernumerate=bci.TASK_NR)
                if ADD_AMPS_ON:
                    gsr.stop()
                    hr.stop()
                #task 2: nft
                bci.TASK_NR+=1
                rest.TASK_NR=prime.TASK_NR=nft.TASK_NR=bci.TASK_NR
                nft.STIM_TIME= master_stim_2 #s
                nft.protocol_eyes=bci.protocol_eyes_l[bci.TASK_NR-1]
                nft.START_WAIT_FOR_KEY=False
                nft.initial_reward_bands, nft.initial_inhibit_bands = irb_eo, iib_eo
                if nft.protocol_eyes=="eyes_closed": nft.initial_reward_bands, nft.initial_inhibit_bands = irb_ec, iib_ec
                if ADD_AMPS_ON:
                    gsr.start()
                    hr.start()
                nft.on_play_check( markernumerate=bci.TASK_NR)#nft.on_play(markernumerate=bci.TASK_NR)
                if ADD_AMPS_ON:
                    gsr.stop()
                    hr.stop()
                #update nft thresholds
                if nft.protocol_eyes=="eyes_open":
                    if MASTER_UPDATE_THRESHOLD_AFTERTASK:
                        update_reward_bands_eo[nft.PROTOCOL_FEATURE]['threshold']=nft.new_threshold
                    bci.thresholdbuffer_eo.append(update_reward_bands_eo[nft.PROTOCOL_FEATURE]['threshold'])
                if nft.protocol_eyes=="eyes_closed":
                    if MASTER_UPDATE_THRESHOLD_AFTERTASK:
                        update_reward_bands_ec[nft.PROTOCOL_FEATURE]['threshold']=nft.new_threshold
                    bci.thresholdbuffer_ec.append(update_reward_bands_ec[nft.PROTOCOL_FEATURE]['threshold'])


        #3. BLOCK OUT
        bci.BLOCK_NR+=1
        rest.BLOCK_NR=prime.BLOCK_NR=nft.BLOCK_NR=bci.BLOCK_NR

        #task 1: rest olhos fechados
        bci.TASK_NR +=1
        rest.TASK_NR=prime.TASK_NR=nft.TASK_NR=bci.TASK_NR
        rest.STIM_TIME= master_stim_1 #s
        rest.protocol_eyes=bci.protocol_eyes_l[bci.TASK_NR-1]
        rest.START_WAIT_FOR_KEY=True
        if ADD_AMPS_ON:
            gsr.start()
            hr.start()
        rest.on_play_check(markernumerate=bci.TASK_NR)
        if ADD_AMPS_ON:
            gsr.stop()
            hr.stop()

        #task 2: rest olhos abertos
        bci.TASK_NR +=1
        rest.TASK_NR=prime.TASK_NR=nft.TASK_NR=bci.TASK_NR
        rest.STIM_TIME= master_stim_1 #s
        rest.protocol_eyes=bci.protocol_eyes_l[bci.TASK_NR-1]
        rest.START_WAIT_FOR_KEY=True
        if ADD_AMPS_ON:
            gsr.start()
            hr.start()
        rest.on_play_check(markernumerate=bci.TASK_NR)
        if ADD_AMPS_ON:
            gsr.stop()
            hr.stop()

        #task 3: nft
        bci.TASK_NR+=1
        rest.TASK_NR=prime.TASK_NR=nft.TASK_NR=bci.TASK_NR
        nft.STIM_TIME= master_stim_2 #s
        nft.protocol_eyes=bci.protocol_eyes_l[bci.TASK_NR-1]
        nft.START_WAIT_FOR_KEY=False
        nft.initial_reward_bands, nft.initial_inhibit_bands = update_reward_bands_eo, update_inhibit_bands_eo #or self.reward_bands, self.inhibit_bands - last calculated reward and inhibit bands
        if ADD_AMPS_ON:
            gsr.start()
            hr.start()
        nft.on_play_check(markernumerate=bci.TASK_NR)#nft.on_play(markernumerate=bci.TASK_NR)
        if ADD_AMPS_ON:
            gsr.stop()
            hr.stop()

        #task report
        report.START_WAIT_FOR_KEY=True
        report.on_play_check()





        bci.elapsed_time =time.time() - bci.start_time
        logger.info("!!ELAPSED TIME INIT METHODS BCICLASS!! : {}".format(bci.elapsed_time))



        bci.on_quit()
        if ADD_AMPS_ON:
            gsr.on_quit()
            hr.on_quit()


    except Exception as e:
        logger.error("!!!!SOMETHING WENT WRONG DURING BCI : {}".format(e))
        bci.on_quit()
        if ADD_AMPS_ON:
            gsr.on_quit()
            hr.on_quit()

















if __name__ == "__main__":
    bci()

