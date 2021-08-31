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
#import copy
#import json
#
## My functions
import neuroprime.src.utils.myfunctions as my
#from functions.nftalgorithm import nftalgorithm

# My classes
from neuroprime.src.initbciclass import initbciclass
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


def bci():
    st =time.time()
    bci = initbciclass()
    rest = restclass()
    nft = nftclass()
    prime = primeclass()
    report = reportclass()


    et =time.time() - st

    logger.info("!!ELAPSED TIME INIT CLASS BCICLASS!! : {}".format(et))

    #RANDOM VARS
    random.seed() #None or no argument seeds from current time or from an operating system specific randomness source if available

    try:#catch and close

        #2RE-INIT Vars

        #SAVE
        bci.SAVE=rest.SAVE=nft.SAVE=prime.SAVE= False
        bci.SAVE_TASK=rest.SAVE_TASK=nft.SAVE_TASK=prime.SAVE_TASK=False #True, save file by task or False, by session
        folder_path=my.get_test_folder(foldername='e2_bci_v1') #folderpath
        #Start dialogue
        info={'savefolder': folder_path, 'subject':1, 'session':1, 'exp_version': 'e2_v1',
              'pg': ['EG', 'CG', 'random'],
              'prime': ['BM', 'IM'],
              'feat': ['a','s','d','t','b','g'],
              "technician": "Nuno Costa"} #'pg': ['EG', 'CG', 'PILOT', 'TEST','random']
        title='experiment 2'
        fixed=['exp_version']
        newinfo=my.gui_dialogue(info=info,title=title,fixed=fixed)
        #random group choice - randomize EG and CG-not good because never know how it can end - using pseudo randomization in excel
        if newinfo['pg'] =="random":
           newinfo['pg'] = random.choice(['EG','CG'])
        #SAVE VARS
        bci.FOLDER_DATA=rest.FOLDER_DATA=nft.FOLDER_DATA=prime.FOLDER_DATA= newinfo['savefolder']
        bci.GROUP=rest.GROUP =nft.GROUP =prime.GROUP = newinfo['pg']  #EG or CG
        bci.SUBJECT_NR =rest.SUBJECT_NR =nft.SUBJECT_NR = prime.SUBJECT_NR = newinfo['subject']
        bci.SESSION_NR=rest.SESSION_NR  =nft.SESSION_NR =prime.SESSION_NR = newinfo['session']



        ###INIT BCI
        st=time.time()

        #INIT SAVING
        rest.init_io()
        prime.init_io()
        nft.init_io()
        report.init_io()

        #INIT PRESENTATION AND ACQUISITION, PATCH NFT AND prime CLASS WITH only one AMP and PYFF object
        bci.on_init()


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

        #rest vars
        nft.PROTOCOL_TYPE =  "REST" #
        rest.PROTOCOL_DESIGN = "normal"

        #prime VARS
        if newinfo['prime'] =="BM": prime.audiostimulus_l = ["breathingv6.ogg", "imageryv6.ogg"]
        if newinfo['prime'] =="IM": prime.audiostimulus_l = ["imageryv6.ogg", "breathingv6.ogg"]
        prime.PROTOCOL_TYPE =  "PRIME" #
        prime.PROTOCOL_DESIGN = "normal" #normal, test

        #NFT VARS
        if newinfo['feat'] =="a": nft.PROTOCOL_FEATURE = "alpha"
        if newinfo['feat'] =="s": nft.PROTOCOL_FEATURE = "SMR"
        nft.PROTOCOL_TYPE =  "NFT" #
        nft.PROTOCOL_DESIGN = "normal" # Normal
        #online vars (change in nftclass)
        #INIT NFT ALGORITHM
        nft.init_processing_algorithm(feature=nft.PROTOCOL_FEATURE)


        et =time.time() - st
        logger.info("!!ELAPSED TIME INIT METHODS BCICLASS!! : {}".format(et))

        ###EXPERIMENT SESSION
        bci.start_time=time.time()

        #master stim time for tasks
        master_stim_1= 10 #s #rest eo & ec
        master_stim_2= 2*master_stim_1 #s #rest, prime and nft full task

        #1. BLOCK IN
        bci.BLOCK_NR = 1
        prime.BLOCK_NR=nft.BLOCK_NR=bci.BLOCK_NR

        #task 1: rest olhos fechados
        bci.TASK_NR=1
        rest.TASK_NR=prime.TASK_NR=nft.TASK_NR=bci.TASK_NR
        rest.STIM_TIME= master_stim_1 #s
        rest.protocol_eyes="eyes_closed_v2"
        rest.START_WAIT_FOR_KEY=True
        rest.on_play_check(markernumerate=bci.TASK_NR) #rest.on_play(markernumerate=bci.TASK_NR) #or nft.off_rest_bci
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
        rest.protocol_eyes="eyes_open_v2"
        rest.START_WAIT_FOR_KEY=True
        rest.on_play_check(markernumerate=bci.TASK_NR) #rest.on_play(markernumerate=bci.TASK_NR) #or nft.off_rest_bci
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
        nft.protocol_eyes="eyes_open"
        nft.START_WAIT_FOR_KEY=False
        nft.initial_reward_bands, nft.initial_inhibit_bands = update_reward_bands_eo, update_inhibit_bands_eo
        nft.on_play_check(markernumerate=bci.TASK_NR)#nft.on_play(markernumerate=bci.TASK_NR)
        #update thresholds
        update_reward_bands_eo[nft.PROTOCOL_FEATURE]['threshold']=nft.new_threshold
        bci.thresholdbuffer_eo.append(update_reward_bands_eo[nft.PROTOCOL_FEATURE]['threshold'])



        #task report:  (dont update task_nr because files not saved)
        report.START_WAIT_FOR_KEY=True
        report.on_play_check()

        #raise RuntimeError("Terminate Experiment")


        #2.Block of stimulus ( FACTORIAL DESIGN)
        for i,audio in enumerate(prime.audiostimulus_l):
            #UPATE BLOCK
            bci.BLOCK_NR+=1
            prime.BLOCK_NR=nft.BLOCK_NR=bci.BLOCK_NR
            #eyes protocol
            protocol_eyes="eyes_open"
            irb, iib = update_reward_bands_eo, update_inhibit_bands_eo
            if bci.BLOCK_NR==2 or bci.BLOCK_NR==4:
                protocol_eyes="eyes_closed"
                irb, iib = update_reward_bands_ec, update_inhibit_bands_ec

            #PLAY NEW BLOCK
            if bci.GROUP=="EG":
                #task 1:prime
                bci.TASK_NR+=1
                rest.TASK_NR=prime.TASK_NR=nft.TASK_NR=bci.TASK_NR
                prime.STIM_TIME= master_stim_2 #s
                prime.protocol_eyes=protocol_eyes
                prime.START_WAIT_FOR_KEY=True
                prime.on_play_check( audiostimulus=audio, markernumerate=bci.TASK_NR)#prime.on_play(audiostimulus=audio, markernumerate=bci.TASK_NR)

                #task 2: NFT
                bci.TASK_NR+=1
                rest.TASK_NR=prime.TASK_NR=nft.TASK_NR=bci.TASK_NR
                nft.STIM_TIME= master_stim_2 #s
                nft.protocol_eyes=protocol_eyes
                nft.START_WAIT_FOR_KEY=False
                nft.initial_reward_bands, nft.initial_inhibit_bands = irb, iib #or self.reward_bands, self.inhibit_bands - last calculated reward and inhibit bands
                nft.on_play_check(markernumerate=bci.TASK_NR)#nft.on_play(markernumerate=bci.TASK_NR)


            elif bci.GROUP=="CG":
                #task 1: rest
                bci.TASK_NR+=1
                rest.TASK_NR=prime.TASK_NR=nft.TASK_NR=bci.TASK_NR
                rest.STIM_TIME= master_stim_1 #s
                rest.protocol_eyes=protocol_eyes
                rest.START_WAIT_FOR_KEY=True
                rest.on_play_check(markernumerate=bci.TASK_NR)
                #task 2: nft
                bci.TASK_NR+=1
                rest.TASK_NR=prime.TASK_NR=nft.TASK_NR=bci.TASK_NR
                nft.STIM_TIME= master_stim_2 #s
                nft.protocol_eyes=protocol_eyes
                nft.START_WAIT_FOR_KEY=False
                nft.initial_reward_bands, nft.initial_inhibit_bands = irb, iib #or self.reward_bands, self.inhibit_bands - last calculated reward and inhibit bands
                nft.on_play_check( markernumerate=bci.TASK_NR)#nft.on_play(markernumerate=bci.TASK_NR)

            #update nft thresholds
            if protocol_eyes=="eyes_open":
                update_reward_bands_eo[nft.PROTOCOL_FEATURE]['threshold']=nft.new_threshold
                bci.thresholdbuffer_eo.append(update_reward_bands_eo[nft.PROTOCOL_FEATURE]['threshold'])
            if protocol_eyes=="eyes_closed":
                update_reward_bands_ec[nft.PROTOCOL_FEATURE]['threshold']=nft.new_threshold
                bci.thresholdbuffer_ec.append(update_reward_bands_ec[nft.PROTOCOL_FEATURE]['threshold'])

        """
        #3. BLOCK OUT
        bci.BLOCK_NR+1
        prime.BLOCK_NR=nft.BLOCK_NR=bci.BLOCK_NR

        #task 1: rest olhos fechados
        bci.TASK_NR +=1
        rest.TASK_NR=prime.TASK_NR=nft.TASK_NR=bci.TASK_NR
        rest.STIM_TIME= master_stim_1 #s
        rest.protocol_eyes="eyes_closed_v2"
        rest.START_WAIT_FOR_KEY=True
        rest.on_play_check(markernumerate=bci.TASK_NR)

        #task 2: rest olhos abertos
        bci.TASK_NR +=1
        rest.TASK_NR=prime.TASK_NR=nft.TASK_NR=bci.TASK_NR
        rest.STIM_TIME= master_stim_1 #s
        rest.protocol_eyes="eyes_open_v2"
        rest.START_WAIT_FOR_KEY=True
        rest.on_play_check(markernumerate=bci.TASK_NR)

        #task 3: nft
        bci.TASK_NR+=1
        rest.TASK_NR=prime.TASK_NR=nft.TASK_NR=bci.TASK_NR
        nft.STIM_TIME= master_stim_2 #s
        nft.protocol_eyes="eyes_open"
        nft.START_WAIT_FOR_KEY=False
        nft.initial_reward_bands, nft.initial_inhibit_bands = update_reward_bands_eo, update_inhibit_bands_eo #or self.reward_bands, self.inhibit_bands - last calculated reward and inhibit bands
        nft.on_play_check( markernumerate=bci.TASK_NR)#nft.on_play(markernumerate=bci.TASK_NR)

        #task report
        report.START_WAIT_FOR_KEY=True
        report.on_play_check()
        """




        bci.elapsed_time =time.time() - bci.start_time
        logger.info("!!ELAPSED TIME INIT METHODS BCICLASS!! : {}".format(bci.elapsed_time))

        nft.serialize(objectname="nftclass_finalstate")
        prime.serialize(objectname="primeclass_finalstate")
        bci.serialize(objectname="bci_finalstate")

        bci.on_quit()


    except Exception as e:
        logger.error("!!!!SOMETHING WENT WRONG DURING BCI : {}".format(e))
        bci.on_quit()

















if __name__ == "__main__":
    bci()

