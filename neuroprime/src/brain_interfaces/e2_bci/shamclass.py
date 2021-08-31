#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Thu Jun 21 18:11:57 2018

e1 version working

@author: nm.costa
"""


from __future__ import division


#from __future__ import (absolute_import, division, print_function)
#from builtins import * #all the standard builtins python 3 style


__version__="3.1+dev"


import time
import datetime
import os
import random
import math
import copy
import json
import sys
import cPickle as pickle
# My functions
import neuroprime.src.utils.myfunctions as my
from neuroprime.src.signal_processing.nftalgorithm import nftalgorithm
import neuroprime.src.signal_processing.eegfunctions as eeg

# My classes
from neuroprime.src.initbciclass import initbciclass

#LOGGING - logger from initbciclass
import logging
setlevel=logging.WARNING
logging.basicConfig(stream=sys.stdout, level=setlevel)
#Module logger
logger = my.setlogfile(modulename=__name__, setlevel=setlevel, disabled=True)
logger.info('Logger started')
#debugging
#import pdb


class shamclass(initbciclass):


    def init(self):
        """
        Global Constants
        """
        #1.INIT Parent Class
        initbciclass.init(self)
        #2.Alter or add other functions

        #INIT SAVING
        self.TASK = 'NFT' # NFT
        self.subtask = ""  #ALL TASKs in same FILE

        #INIT PRESENTATION VARS
        #Presentation PROTOCOL VARS- TODO: randomize protocol_feature
        self.PROTOCOL_TYPE = "" #NFT or REST the functions will change it accordingly
        self.PROTOCOL_DESIGN = "normal" #ABA or Normal -
        #presentation init screen
        self.INIT_TEXT = ""

        self.STIM_TIME=30#s



        ##EXPERIMENT VARS
        self.datatdir=my.get_test_folder(foldername="e2_data")
        self.subjectdir="EG/S001" #
        self.fileid="online_result" #id that identifies the file


        #protocol features of NFT
        self.PROTOCOL_FEATURES_L = ["SMR", "upper_alpha"]  #List
        self.PROTOCOL_FEATURE =  "SMR" #SMR or upper_alpha
        self.random_seed = None  #None or no argument seeds from current time or from an operating system specific randomness source if available

        #OFFLINE PROCESSING -
        #reward and inhibit bands - dict objects to buffer band features
        self.initial_reward_bands, self.initial_inhibit_bands = {},{} #initial bands
        self.reward_bands, self.inhibit_bands = {}, {} #state bands - updated during online neurofeedback

        #ONLINE PROCESSING







    """
    Online

    SHAM from resultbuffer data from subject

    """



    def on_sham_bci(self,
                   presType="pyff",
                   markernumerate=0):
        self.logger.info("\n>> ***on_nft_bci***")

        #Reset|Init class vars
        self.presType=presType
        subtask=self.PROTOCOL_FEATURE+"_"+str(markernumerate)

        if presType == "pyff":
            #INIT VARS  - presentation
            self.PROTOCOL_TYPE = "NFT"
            self.STIM_TIME = self.STIM_TIME #s
            #add pyff vars
            if self.protocol_eyes=='eyes_open':
                self.feedback_bars=True
                self.feedback_sounds=True
            if self.protocol_eyes=='eyes_closed':
                self.feedback_bars=False
                self.feedback_sounds=True
            #instructions
            pcol_eyes=""
            if self.protocol_eyes=='eyes_open':
                self.INIT_TEXT = "TAREFA: TREINO DE NEUROFEEDBACK.    BLOCO: {} / {} \n\nOBJECTIVOS: \n1. A barra reflete a sua atividade cerebral, tente controlar; \n2. Obtenha o máximo número de pontos, mantendo a barra acima do threshold. \n\n\nExplore estratégias mentais que aumentem a barra. Exemplos: -Pensamentos positivos, neutros ou negativos; -Não pensar; -Focar em algo; -Entre outros.\n\n\nMantenha os olhos abertos e permaneça atento ás barras".format(self.BLOCK_NR, self.TOTAL_BLOCK_NR)
                self.STIMULUS_TEXT ="!Mantenha os OLHOS ABERTOS!"#"\n\n\n\nObjectivo: manter barra verde, acima do threshold!\n\nMantenha os OLHOS ABERTOS!\nTente não mexer a cabeça ou piscar os olhos!\n\nCarregando tarefa....."
                pcol_eyes="eo"
            if self.protocol_eyes=='eyes_closed':
                self.INIT_TEXT = "TAREFA: TREINO DE NEUROFEEDBACK.    BLOCO: {} / {} \n\nOBJECTIVOS: \n1. O som reflete a sua atividade cerebral, tente controlar; \n2. Tente manter o som mais grave. \n\n\nExplore estratégias mentais. Exemplos: -Pensamentos positivos, neutros ou negativos; -Não pensar; -Focar em algo; -Entre outros.\n\n\nMantenha os olhos fechados e permaneça atento ao audio.".format(self.BLOCK_NR, self.TOTAL_BLOCK_NR)
                self.STIMULUS_TEXT ="\n\n\n\nObjectivo: manter o som mais grave \n\nMantenha os OLHOS FECHADOS!\n\nTente não mexer a cabeça!"
                pcol_eyes="ec"

            self.subtask=subtask
            if pcol_eyes: self.subtask=self.PROTOCOL_FEATURE+"_"+pcol_eyes+"_"+str(markernumerate) #type: subtask_pcol_eyes_tasknumber
            self.START_MARKER = "START_"+self.subtask
            self.END_MARKER = "END_"+self.subtask
            ###START LOOP
            try:
                self.on_loop(method="sham_loop")
            except Exception as e:
                self.logger.error("\n>> ON_NFT_BCI: {}".format(e))
                self.on_quit()
                raise

        if presType == "psychopy":
            pass #TODO: IMPLEMENT



    def sham_loop(self):
        start_time = time.time()
        self.logger.info("on_nft start_time: {}".format(start_time))
        
        #get subject resultbuffer based on the block we are in
        resultbuffer=[]
        filedir=os.path.join(self.datadir, self.subjectdir, "NFT")
        #choose filename from the filelist using BLOCK_NR
        BLOCK = 'b'+ '{num:02d}'.format(num=self.BLOCK_NR)

        ld=os.listdir(filedir)
        dn=self.fileid #file id
        filename=None
        for fn in ld:
            if not fn.find(dn)==-1:
                if not fn.find(BLOCK)==-1:
                    filename=fn #
                    break 
        if not filename: raise AssertionError("Problems finding file: fileid:{} ; Block: {}".format(dn, BLOCK))
        
        filepath=os.path.join(filedir, filename)
        with open(filepath, "rb") as f:
            resultbuffer=pickle.load(f)
        self.resultbuffer=resultbuffer

        #INITIAL REWARD and Inhibit Bands
        init_result=self.resultbuffer[0]
        self.reward_bands=init_result["reward_bands"]
        self.inhibit_bands=init_result["inhibit_bands"]

        #INIT TIMES
        init_buffer_timestamp=init_result["timestamp"]
        init_loop_timestamp=time.time()
        
        #STREAM NAMES
        amp_name="AMP PID"
        marker_name="MARKER"
        try:
            if self.amp.amp.lsl_amp_name:
                amp_name=self.amp.amp.lsl_amp_name
            if self.amp.amp.lsl_marker_name:
                marker_name=self.amp.amp.lsl_marker_name
        except:
            pass



        ##GET/SAVE DATA
        STOP = False
        timer = my.Timer(autoreset=True)
        fs = self.amp.get_sampling_frequency()
        server_buffer_time=self.chunksize/ fs #server mininimum buffer time
        next_sec = 1
        first_sent=False
        self.processing_counter=0
        self.previous_ts=time.time()
        current_len_samples=0
        while not STOP:
            loop_start_time=time.time()

            #GET DATA
            samples, markers = self.amp.get_data()  #PROBLEMS running it two times in a row
            if markers: #LOG RIGHT AWAY MARKERS
                for m in markers:
                    t0_data=self.amp.amp.duration #ms
                    self.logger.info("\n>> {} : {}s, {}".format(marker_name,(t0_data + m[0])/1000, m[1]))#absolute timestamp s

            #ONLINE ROUTINE 
            if len(samples)>0:
                st=time.time()
                self.reward_bands, self.inhibit_bands, sent, log, timestamp = self.online_sham() #TODO
                et=time.time()-st
                self.logger.info("\n\n>> ONLINE ROUTINE DURATION: {} s \n>> SENT: {}\n>> TIME BETWEEN ROUTINES: {} s\n LOG: {}\n".format(et, sent,timestamp-self.previous_ts, log))
                self.previous_ts=timestamp
                if sent and not first_sent:
                    first_sent=True
                    #play presentation - show task
                    self.pyff.play()


            #STOP IF END_MARKER
            if self.END_MARKER in [m for _, m in markers]:
                STOP = True
                break
            #STOP with replayamp
            if self.replayamp:
                for _, m in markers:
                    if m.find("END")>-1:
                        break
                elapsed_time = time.time() - start_time
                if elapsed_time>self.STIM_TIME:
                    STOP = True
                    break
            #STOP if only has 'END' in the name - for Multiprocessing and if presentation ENDs abruptly
            if self.END_MARKER=='END':
                end='END'
                if any([m.upper().find(end)>-1 for _, m in markers]):
                    STOP = True
                    break

            #SLEEP
            timer.sleep_atleast(server_buffer_time)

            #LOG INFO
            try:
                if self.amp.received_samples > 0:
                    sample_duration = self.amp.received_samples / fs
                    loop_elapsed = time.time() - loop_start_time
                    loop_duration = time.time() - start_time
                    if len(samples)>0:
                        current_len_samples=len(samples)
                    if sample_duration > next_sec:
                        datetime_duration = datetime.timedelta(seconds=int(sample_duration))
                        self.logger.info("\n>> {} {} DATETIME: {} \n>> Received Samples Duration: {} s\n>> Loop Duration: {} s \n>> Loop Elapsed time: {} s \n>> Samples_received : {} \n>> get_data chunk average : {}".format(amp_name, self.amp.amp.pid, datetime_duration, sample_duration, loop_duration, loop_elapsed, self.amp.received_samples, current_len_samples))
                        next_sec += 1
            except:
                pass


        #LOG last time after loop breaks
        try:
            if self.amp.received_samples > 0:
                datetime_duration = datetime.timedelta(seconds=int(sample_duration))
                self.logger.info("\n>> {} {} DATETIME: {} \n>> Received Samples Duration: {} s\n>> Loop Duration: {} s \n>> Loop Elapsed time: {} s \n>> Samples_received : {} \n>> get_data chunk average : {}".format(amp_name, self.amp.amp.pid, datetime_duration, sample_duration, loop_duration, loop_elapsed, self.amp.received_samples, current_len_samples))
            #LOG elapsed time
            elapsed_time = time.time() - start_time
            self.logger.info("ELAPSED TIME :{}".format(elapsed_time))
        except:
            pass

        #PROCESSING CLASS INITIAL STATE - ADDITIONAL RESET
        self.processingclass = self.processingclass.reset_class_state()



    def online_sham(self, resultbuffer, resultbuffer_index ):
        """
        GET SHAM SUBJECT FEATURES AND SEND TO PRESENTATION

        TODO
        """
        log='\n>> ONLINE PROCESSING OF  {}  samples, and  MARKERS: {}'.format(samples.shape, markers)
        sent = False #result sent to presentation
        timestamp=time.time()
        e_timestamp=timestamp-self.start_on_sham_time
        
 #current result from processing class
        #current resultbuffer:
        current_res={"reward_bands": current_result['reward_bands'], "inhibit_bands": current_result['inhibit_bands'],'sent':sent, 'timestamp':timestamp, 'log':log, "IAF":IAF , "IAF_ch":IAF_ch, "psd_linregress":psd_linregress, 'in_data':input_data} 


        #ONLINE PROCESSING
        st=time.time()
        et=time.time()-st
        msg="\n>> NFTALGORITHM ELAPSED TIME: {}".format(et)
        log=log+msg
        self.logger.warning(msg)


        #CONTINUE TO NEXT ITERATION IF NOT FINISHED
        if not processing_finished:
            msg="\n>> Processing not finished!"
            self.logger.warning(msg)
            log=log+msg
            sent = False
            #add current_result to buffers
            timestamp=time.time()
            self.resultbuffer.append(current_res)#self.resultbuffer.extend([current_res])
            #continue to next while iteration
            return reward_bands, inhibit_bands, sent, log, timestamp #TODO add timeout after some continues

        #RESULT & SEND (IF FINISHED)
        current_result = copy.copy(self.processingclass.result) #UPDATE RESULT


        #SENDING FEATURES TO PRESENTATION
        if self.presType=="pyff":
            self.pyff.send_control_signal(parse_result)
            msg="\n>> SENT FEATURES TO PYFF: {}".format(parse_result)
            #self.logger.info(msg)
            log=log+msg




        sent = True
        #add current_result to buffers
        timestamp=time.time()
        current_res={"reward_bands": current_result['reward_bands'], "inhibit_bands": current_result['inhibit_bands'],'sent':sent, 'timestamp':timestamp, 'log':log, "IAF":IAF , "IAF_ch":IAF_ch, "psd_linregress":psd_linregress, 'in_data':input_data} 
        current_res["inhibit_bands"]["show"]=self.show_inhibit_bands #add 'show' value
        self.resultbuffer.append(current_res)#self.resultbuffer.extend([current_res])

        return reward_bands, inhibit_bands, sent, log, timestamp



    def on_init(self):
        """
        ON INIT
        """
        initbciclass.on_init(self)
        self.logger.debug('#NOTE init_processing can only be done afer init acquisition and presentation - because the class is always reset, you just need to init one time')
        self.init_processing_algorithm(feature=self.PROTOCOL_FEATURE)


  

    def on_play(self, markernumerate=0):
        """
        """
        ##UPDATE/RESET
        self.update_file_path()#WARNING: NECESSARY
        self.start_time = time.time()


        ###ONLINE NEUROFEEDBACK PIPELINE
        self.on_sham_bci(markernumerate=markernumerate)

        ###LOG TIME
        self.end_time = time.time()
        self.elapsed_time =self.end_time - self.start_time
        self.logger.info("!!ON_PLAY ELAPSED TIME!! : {}".format(self.elapsed_time))

if __name__ == "__main__":
    #WARNING TO SIMULATE:  USE ONLY Replay data -  Replay(PREFERABLY file_stream_player.py instead of using replayamp of nftclass)

    #replayamp
    replayamp=False
    #replay sample data (using same for online and offline if you don't acquire data)
    folderdir='e2_data/e2_pilot'
    filename="EG_S001_REST_ss01_b01_08102019_14h16m_rest_2"
    amp_ref=['Cz']#[] - no_ref (give manual information about the ref)
    filetoreplay=my.get_filetoreplay(folderdir=folderdir,filename=filename, filetype=".meta") #filepath

    #save folder dir
    test_folder_path=os.path.join(my.get_test_folder(), 'nftclass') #folderpath



    #1.Start Class
    nft = shamclass()
    nft.logger.debug("#WARNING replayamp only useful for online routines")
    try:
        #2.RE-INIT Vars
        #SAVING
        #Start dialogue
        info={'SAVE': ['no', 'yes'], 'savefolder': test_folder_path, 'subject':1, 'session':1, 'exp_version': 2, 'group': ['EG', 'CG', 'PILOT'], "technician": "Nuno Costa"}
        title='test experiment'
        fixed=['exp_version']
        newinfo=my.gui_dialogue(info=info,title=title,fixed=fixed)
        #Save vars
        nft.FOLDER_DATA = newinfo['savefolder']
        nft.GROUP = newinfo['group']  #EG or CG
        nft.SUBJECT_NR = newinfo['subject']
        nft.SESSION_NR = newinfo['session']

        if newinfo['SAVE']=='yes': nft.SAVE= True
        if newinfo['SAVE']=='no': nft.SAVE= False

        #Experiment Vars
        nft.protocol_eyes="eyes_open"
        nft.get_baseline_thresholds=True
        nft.acquire_baseline_data=False
        nft.PROTOCOL_DESIGN = "normal" #ABA, normal
        nft.amp_ref_channels=amp_ref
        #Assigne randomly a feature for each subject
#        nft.PROTOCOL_FEATURES_L = ["SMR", "upper_alpha", "alpha"]
#        random.seed(nft.random_seed)
#        random.shuffle(nft.PROTOCOL_FEATURES_L)
        nft.PROTOCOL_FEATURE = "alpha" # nft.PROTOCOL_FEATURES_L[0] - randomized

        nft.on_init()  #INIT Methods - Saving, Acquisition and Presentation

        st=time.time()

        #PLAY
        nft.TASK_NR = 1
        nft.on_play(markernumerate=nft.BLOCK_NR)


        et =time.time() - st
        nft.logger.info("!!ELAPSED TIME INIT METHODS BCICLASS!! : {}".format(et))
        nft.on_quit()
    except Exception as e:
        nft.logger.error("\n>> SOMETHING WENT WRONG: {}".format(e))
        nft.on_quit()