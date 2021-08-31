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


class nftclass(initbciclass):


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


        #protocol features of NFT
        self.PROTOCOL_FEATURES_L = ["SMR", "upper_alpha"]  #List
        self.PROTOCOL_FEATURE =  "SMR" #SMR or upper_alpha
        self.random_seed = None  #None or no argument seeds from current time or from an operating system specific randomness source if available

        #OFFLINE PROCESSING -
        self.get_baseline_thresholds=False #play
        self.acquire_baseline_data=False #True, get data or False, simulate
        #reward and inhibit bands - dict objects to buffer band features
        self.initial_reward_bands, self.initial_inhibit_bands = {},{} #initial bands
        self.reward_bands, self.inhibit_bands = {}, {} #state bands - updated during online neurofeedback



        #ONLINE PROCESSING

        #INIT PARAMETERS of nftalgorithm
        #for advanced edition go to nftalgorithm.py
        self.window_time =1024 #ms window in ms to segment the data and process - NOTE:2^8 is better for n_fft (window to segment and epoching)
        self.sampleRate=1000 #Hz sample rate of the EEG amplifier
        self.blocktime=50 #ms multiple of block to add in window ring buffer (multiples of this value will be added) #NOTE: Because of online routine is ~250ms it will put >200ms online, and it's not constant
        self.calculate_iaf=False #True/False - activate Individual Alpha Frequency calculation
        self.show_inhibit_bands=False #True/False - show or not inhibit bands in feedback(goes to presentation)

        #PREPROCESSING (https://en.wikipedia.org/wiki/Electroencephalography)
        self.l_freq = 40 #hz - for limit see bands used for feature - Till 40 we let pass some muscle artifacts
        self.h_freq = 1 #Hz - NOTE:Removes DC offset= constant freqs
        self.subsample=None #None | hz  - it interferes with fft
        self.select_chs =['Fp1','Fp2', 'Fz','Pz'] #chs used throught the processing #NOTE: Include Fp1 and Fp2 for rejection of blinks and saccades
        self.ref_channels = [] #rereferencing ; ref_channels= "average"  |  [] No-rereferencing | ['CH'] for rereference - WARNING:online is better to be Cz or Pz, not average
        self.rej_max_peaktopeak = 100e-6 #V
        self.rej_min_peaktopeak = 0.5e-6 #V

        #PROCESSING
        self.n_fft=1024 #samples, window_time * sampleRAte
        self.n_per_seg=self.n_fft*1 #fft window size percentage
        self.n_overlap=int(math.ceil(self.n_per_seg *0.25))
        self.pink_max_r2=None #None  #0.95 , None - doesnt check for noise in signal (#WARNING: if used it stops program)
        self.threshold_reward_level=-0.38 #std (-0.38*std => 65% above)
        self.threshold_inhibit_level=1
        self.feedback_reward_level=0
        self.feedback_inhibit_level=0

        #additional processing
        self.adaptative_threshold_intask = None#s None| int seconds #update during task
        self.adaptative_threshold_aftertask=True #update threshold at the end of the nfttask






        #Changes to speed up(TODO):
            #Rereference and select channels in wyrm instead of mne
            #Subsample to 500Hz or 250Hz - no because you lose definition of fft
            #Use Samples as they come?? - yes but a multiple of does samples - time will depend on online routine has the number of samples
            #filter to less frequences - yes 40 hz






    def init_processing_algorithm(self, feature="SMR"):
        """
        Why give the class a processing algorithm?
        Advantages:Save online iteration results
        Disadvanages: Reset to initial state when needed.

        WARNING: #TODO With a global difined processing algorithm after using the algorithm locally, the object is never changed globally - less code
        """
        self.logger.info("\n>> ***init_processing_algorithm***")
        start_time = time.time()
        ###INIT nftalgorithm

        try:
            #ASSERT
            amp_fs=self.amp.get_sampling_frequency()
            amp_chs=self.amp.get_channels()
            #CONVENTION: ch_names=amp_chs   # to simplify nftalgorythm (SAME AS initbciclass - necessary if you don't use nftclass.on_int())
            if set(amp_chs).issubset(self.ch_names):
                self.ch_names=amp_chs#update to new names that are inside the initial self.ch_names
            else:
                raise AssertionError("\n>> Server AMP CHs different from initbciclass ch_names: \n>> self.ch_names: {}; \n>> self.amp.amp.channels {}; \n>> Change ch_names to match what is comming from the stream".format(self.ch_names, amp_chs))

            assert amp_fs==self.sampleRate

            self.blocksize=int((self.blocktime*1000)/amp_fs) #samples - samples to add to ringbuffer


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





    """
    Training - OFFLINE

    NFT Individul Target Thresholds from baseline

    """

    def off_rest_bci(self, presType="pyff", markernumerate=0):
        """
        Acquire Baseline data (Same as restclass)
        method: Rest state
        """
        self.logger.info("\n>> ***off_rest_bci***")

        if presType == "pyff":
            #INIT VARS
            self.PROTOCOL_TYPE =  "REST"
            self.STIM_TIME = self.STIM_TIME
            #instructions
            pcol_eyes=""
            if self.protocol_eyes=='eyes_closed_v2':
                self.INIT_TEXT = "TAREFA: ESTADO DE REPOUSO OLHOS FECHADOS.    BLOCO: {} / {} \n\n\nAproveite agora para respirar, beber água ou chamar o investigador caso necessite de ajuda para ficar mais confortável. \n\n\nDurante as tarefa, mantenha os OLHOS FECHADOS. \n\nTente não mexer a cabeça ou piscar os olhos!\n\nColoque-se confortavelmente e TENTE RELAXAR.".format(self.BLOCK_NR, self.TOTAL_BLOCK_NR)
                self.STIMULUS_TEXT ="Mantenha os OLHOS FECHADOS e TENTE RELAXAR!"
                pcol_eyes="ec"
            if self.protocol_eyes=='eyes_open_v2':
                self.INIT_TEXT = "TAREFA: ESTADO DE REPOUSO OLHOS ABERTOS seguido por NEUROFEEDBACK.    BLOCO: {} / {} \n\n\n\n\nDurante as tarefas, mantenha os olhos abertos focados no ecrã. \nTente não mexer a cabeça ou piscar os olhos!\n\nColoque-se confortavelmente e TENTE RELAXAR.".format(self.BLOCK_NR, self.TOTAL_BLOCK_NR)
                self.STIMULUS_TEXT ="Mantenha os OLHOS ABERTOS focados na cruz e TENTE RELAXAR!\n\n\n\n\n\n\n\n\n\n+"
                pcol_eyes="eo"
            if self.protocol_eyes=='eyes_open':
                self.INIT_TEXT = "TAREFA: ESTADO DE REPOUSO OLHOS ABERTOS seguido por NEUROFEEDBACK.    BLOCO: {} / {} \n\n\nAproveite agora para respirar, beber água ou chamar o investigador caso necessite de ajuda para ficar mais confortável. \n\n\nDurante as tarefas, mantenha os OLHOS ABERTOS focados no ecrã. \n\nTente não mexer a cabeça ou piscar os olhos!\n\nColoque-se confortavelmente e TENTE RELAXAR.".format(self.BLOCK_NR, self.TOTAL_BLOCK_NR)
                self.STIMULUS_TEXT ="Mantenha os OLHOS ABERTOS focados na cruz e TENTE RELAXAR!\n\n\n\n\n\n\n\n\n\n+"
                pcol_eyes="eo"
            if self.protocol_eyes=='eyes_closed':
                self.INIT_TEXT = "TAREFA: ESTADO DE REPOUSO OLHOS FECHADOS seguido por NEUROFEEDBACK.    BLOCO: {} / {} \n\n\nAproveite agora para respirar, beber água ou chamar o investigador caso necessite de ajuda para ficar mais confortável. \n\n\nDurante as tarefas, mantenha os olhos fechados. \n\nTente não mexer a cabeça ou piscar os olhos!\n\nColoque-se confortavelmente e TENTE RELAXAR.".format(self.BLOCK_NR, self.TOTAL_BLOCK_NR)
                self.STIMULUS_TEXT ="Mantenha os OLHOS FECHADOS e TENTE RELAXAR!"
                pcol_eyes="ec"

            self.subtask="rest"+"_"+str(markernumerate)
            if pcol_eyes: self.subtask="rest"+"_"+pcol_eyes+"_"+str(markernumerate) #type: subtask_pcol_eyes_tasknumber
            self.START_MARKER = "START_"+self.subtask
            self.END_MARKER = "END_"+self.subtask
            ###START
            self.on_loop()

        if presType == "psychopy":
            pass #TODO: IMPLEMENT



    def baseline_thresholds(self, data=None, markers=None, filepath=None, filetype=None, markernumerate=0,  taskname="rest"):
        """
        taskname: string (optional: does nothing)
        """
        self.logger.info("\n>> ***baseline_thresholds*** \n>> Feature: {}".format(self.PROTOCOL_FEATURE))

        reward_bands, inhibit_bands=self.offline_processing(data=data, markers=markers, filepath=filepath, filetype=filetype, taskname=taskname)

        return reward_bands, inhibit_bands


    def offline_processing(self, data=None, markers=None, filepath=None, filetype=None, taskname="rest"):
        """
        # Processing baseline data
        # Feature Extraction: Thresholds, mean & std for reward bands and inhibit bands
        # each protocol feature has unique reward and inhibit bands

        data: mushudata | None
        """
        #RUN Routine
        processing_finished, _ =self.processingclass.play_routine(data=data, markers=markers, filepath=filepath, filetype=filetype, taskname=taskname, routine="offline")
        if not processing_finished:
            self.logger.error("PROCESSING DID NOT END - check processingclass nftalgorithm")
            raise

        #Return Reward and inhibit bands with thresholds
        reward_bands=self.processingclass.reward_bands
        inhibit_bands=self.processingclass.inhibit_bands

        #PROCESSING CLASS INITIAL STATE
        self.processingclass = self.processingclass.reset_class_state()

        return reward_bands, inhibit_bands


    """
    Online

    Real time processing

    """



    def on_nft_bci(self,
                   presType="pyff",
                   markernumerate=0,
                   save_online_result=True):
        self.logger.info("\n>> ***on_nft_bci***")

        #Reset|Init class vars
        self.presType=presType
        self.save_online_result=save_online_result

        #adding result to buffers
        self.resultbuffer=[]
        #adding result to a file
        subtask=self.PROTOCOL_FEATURE+"_"+str(markernumerate)
        self.savefile=None
        if save_online_result and self.SAVE:
            filename=None
            filetype=None
            if self.FILENAME_EEG_PATH:
                filename = self.FILENAME_EEG_PATH
            if self.replayamp:
                filename, filetype = os.path.splitext(self.filetoreplay)
            if filename:
                filepath = filename +'_'+subtask+'_online_result.pcl'
                self.savefile=open(filepath, 'wb')

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
                self.on_loop(method="closed_loop")
                self.new_threshold=self.threshold_update_aftertask(method="extreme_case")#new_threshold?
                if self.savefile:
                    pickle.dump(self.resultbuffer, self.savefile, 2) #with open probably opens again
                    #json.dump(str(result), self.savefile)
                    self.savefile.close()
            except Exception as e:
                self.logger.error("\n>> ON_NFT_BCI: {}".format(e))
                #PROCESSING CLASS INITIAL STATE - ADDITIONAL RESET
                self.processingclass.reset_class_state()
                if self.savefile:
                    pickle.dump(self.resultbuffer, self.savefile, 2)
                    #json.dump(str(result), self.savefile)
                    self.savefile.close()
                self.on_quit()
                raise

        if presType == "psychopy":
            pass #TODO: IMPLEMENT

        try:#just for peace of mind
            if self.savefile: self.savefile.close()
        except:
            pass


    def threshold_update_aftertask(self, method="extreme_case"):
        threshold=self.initial_reward_bands[self.PROTOCOL_FEATURE]['threshold']
        try:
            if self.adaptative_threshold_aftertask:
                feedbackbuffer=[]
                for result in self.resultbuffer:
                    if result['sent']['sent']:
                        feedbackbuffer.append(result['reward_bands'][self.PROTOCOL_FEATURE]['feedback'])
                feed_above_thre=[feed for feed in feedbackbuffer if feed >= threshold]
                self.feedratio_above=len(feed_above_thre)/len(feedbackbuffer)
                #ONLY IN EXTREME CASES
                if method=="extreme_case":
                    if self.feedratio_above*100>90: threshold=threshold+0.1*threshold
                    if self.feedratio_above*100<10: threshold=threshold-0.1*threshold
        except:
            pass

        self.new_threshold=threshold

    def closed_loop(self):
        start_time = time.time()
        self.logger.info("on_nft start_time: {}".format(start_time))

        #INITIAL REWARD and Inhibit Bands
        self.reward_bands=self.initial_reward_bands
        self.inhibit_bands=self.initial_inhibit_bands

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
                self.reward_bands, self.inhibit_bands, sent, log, timestamp = self.online_processing(samples, markers, self.reward_bands, self.inhibit_bands)
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



        #FINAL REWARD and Inhibit Bands
#        self.final_reward_bands = reward_bands
#        self.final_inhibit_bands = inhibit_bands

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



    def online_processing(self, samples, markers, reward_bands, inhibit_bands, taskname="feed"):
        """
        GET ONLINE FEATURES AND SEND TO PRESENTATION

        taskname: string (optional: does nothing)
        """
        log='\n>> ONLINE PROCESSING OF  {}  samples, and  MARKERS: {}'.format(samples.shape, markers)
        sent = False #result sent to presentation
        timestamp=time.time()
        IAF=[]
        IAF_ch=[]
        input_data=samples.shape #default
        psd_linregress ={}
        current_result = {"reward_bands":reward_bands, "inhibit_bands":inhibit_bands} #current result from processing class
        #current resultbuffer:
        current_res={"reward_bands": current_result['reward_bands'], "inhibit_bands": current_result['inhibit_bands'],'sent':sent, 'timestamp':timestamp, 'log':log, "IAF":IAF , "IAF_ch":IAF_ch, "psd_linregress":psd_linregress, 'in_data':input_data} 


        #ONLINE PROCESSING
        st=time.time()
        processing_finished, self.processingclass = self.processingclass.play_routine(data=samples, markers=markers, reward_bands=reward_bands, inhibit_bands=inhibit_bands, taskname=taskname, routine="online")
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
        #UPDATE INFO
        try:
            reward_bands=copy.copy(current_result["reward_bands"])
            inhibit_bands=copy.copy(current_result["inhibit_bands"])
            IAF=copy.copy(current_result["IAF"])
            IAF_ch=copy.copy(current_result["IAF_ch"])
            psd_linregress =copy.copy(current_result["psd_linregress"])
            indata= copy.copy(current_result["indata"]) #data that was used in the algorithm
            if indata:
                shape_indata=None
                try:#if the type of data is not wyrm format it can give errors
                    shape_indata= indata.data.shape
                    log=log+"\n>> SHAPE INPUT DATA: {}".format(shape_indata)
                except:
                    pass
                if shape_indata: input_data=shape_indata
                #Uncomment to save all indata
                #input_data=indata
        except:
            pass
        self.logger.info("\n>> Processing finished!")

        #remove nan valuse because they give erros - only needed if using log10 - also check for why
        self.logger.debug("#BUG #TODO NaN values appear converting psd values to log10")
#                        current_dict = current_result
#                        if past_dict:
#                            current_result = my.replace_nan_w_previous_value(current_dict, past_dict)
#                        past_dict = current_result

        #IF FEEDBACK in current_result DICT
        if my.dictfinditem(current_result, "feedback"):
            #current_result valid?
            if not my.dictfinditem(reward_bands, "feedback"):
                msg="\n>> Feedback for reward Band missing. Possible bug!"
                self.logger.error(msg)
                log=log+msg
                sent = False
                #add current_result to buffers
                timestamp=time.time()
                current_res={"reward_bands": current_result['reward_bands'], "inhibit_bands": current_result['inhibit_bands'],'sent':sent, 'timestamp':timestamp, 'log':log, "IAF":IAF , "IAF_ch":IAF_ch, "psd_linregress":psd_linregress, 'in_data':input_data} 
                self.resultbuffer.append(current_res)#self.resultbuffer.extend([current_res])
                return reward_bands, inhibit_bands, sent, log, timestamp #TODO add timeout after some continues
            if inhibit_bands and not my.dictfinditem(current_result['inhibit_bands'], "feedback"):
                msg="\n>> Feedback for inhibit Bands missing. Possible bug!"
                self.logger.warning(msg)
                log=log+msg

                #don't do nothing? or self.show_inhibit_bands=False

            #INITIAL THRESHOLD AND BANDS- if missing; add to local bands; continue to next loop
            self.processing_counter+=1
            if self.processing_counter==1:
                log=log+'\n>> Processing Initial Threshold!'
                #EMPTY BANDS ?
                if not reward_bands: reward_bands=current_result["reward_bands"]
                if not inhibit_bands: inhibit_bands=current_result["inhibit_bands"]
                #EMPTY THRESHOLDS ?
                try:
                    ##WARNING: #TODO: need to update to copy_bands_datatype(bands, input_dt='feedback', output_dt='threshold') - without it thresholds keys are not updated
                    bands=reward_bands
                    for band_key in bands:
                        if not my.dictfinditem(reward_bands[band_key], "threshold") or not reward_bands[band_key]["threshold"]:
                            band_value=bands.get(band_key, None )
                            reward_bands[band_key]["threshold"]=eeg.threshold(band_value, bandtype="reward", datatype="feedback")#go see the definition
                    bands=inhibit_bands
                    for band_key in bands:
                        if not my.dictfinditem(inhibit_bands[band_key], "threshold") or not inhibit_bands[band_key]["threshold"]:
                            band_value=bands.get(band_key, None )
                            inhibit_bands[band_key]["threshold"]=eeg.threshold(band_value, bandtype="inhibit", datatype="feedback")
                except Exception as e:
                    msg='\n>> Problems in setting first threshold, something missing? {}'.format(e)
                    self.logger.error(msg)
                    log=log+msg

                sent = False
                #add current_result to buffers
                timestamp=time.time()
                current_res={"reward_bands": current_result['reward_bands'], "inhibit_bands": current_result['inhibit_bands'],'sent':sent, 'timestamp':timestamp, 'log':log, "IAF":IAF , "IAF_ch":IAF_ch, "psd_linregress":psd_linregress, 'in_data':input_data} 
                self.resultbuffer.append(current_res)#self.resultbuffer.extend([current_res])
                return reward_bands, inhibit_bands, sent, log, timestamp

            #ADAPTATIVE THRESHOLD - after Xtime update threshold ; it will be used in next iteration

            if self.adaptative_threshold_intask:
                duration=self.amp.received_samples / self.amp.get_sampling_frequency() #s
                #rounding to us, it shouldn't repeat
                duration_us = int(1e6*duration)
                adaptative_threshold_us = int(1e6*self.adaptative_threshold_intask)
                mdc=duration_us % adaptative_threshold_us
                if mdc==0:
                    try:
                        ##WARNING: #TODO: need to update to copy_bands_datatype(bands, input_dt='feedback', output_dt='threshold') - without it thresholds keys are not updated
                        bands=reward_bands
                        for band_key in bands:
                            band_value=bands.get(band_key, None )
                            reward_bands[band_key]["threshold"]=eeg.threshold(band_value, bandtype="reward", datatype="feedback")
                        bands=inhibit_bands
                        for band_key in bands:
                            band_value=bands.get(band_key, None )
                            inhibit_bands[band_key]["threshold"]=eeg.threshold(band_value, bandtype="inhibit", datatype="feedback")
                    except Exception as e:
                        msg="COULDN'T UPDATE THRESHOLD, error:{}".format(e)
                        self.logger.error(msg)
                        log=log+msg
                    msg="\n>>THRESHOLDS UPDATED: {}s :".format(duration)
                    self.logger.info(msg)
                    log=log+msg



#           if my.check_dict_nan(current_result): #Not Sending if NaN results


            if my.dictfinditem(current_result, "threshold"):#make sure threshold is also
                parse_result={"reward_bands":current_result['reward_bands'], "inhibit_bands":current_result['inhibit_bands']} #only send reward and inhibit bands from current processing result

                #WARNING: NOT NEEDED - IMPLEMENTED IN feedbackclass
#                if not self.show_inhibit_bands and my.dictfinditem(buffer_result, "inhibit_bands"): #TODO not the best solution - implement in nftalgorithm for less processing
#                    buffer_result["inhibit_bands"] = None

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


    def on_play_baseline(self, markernumerate=0, method='rest'):
        """
        ON Play baseline

        Play one session of the class
        """
        ###OFFLINE PIPELINE
        if self.acquire_baseline_data:
            #Rest method
            if method=='rest':
                self.off_rest_bci( markernumerate=markernumerate)
        #Rest DATA to load
        if self.acquire_baseline_data and self.SAVE:
            filetype=".meta"
            #ADD subtask
            DATA_FILENAME = self.FILENAME_EEG_DATA + '_'+ self.subtask + filetype
            DATA_PATH= self.EEG_PATH
        else:
            #replay sample data
            filedir, filename, ext =my.parse_path_list(self.filetoreplay) #parse
            filetype = '.'+ext
            #add to path
            DATA_FILENAME = filename + filetype
            DATA_PATH = filedir


        #filepath of data to load
        self.logger.debug("#BUG - to io.load_mushu_data the path need to be complete with also filetype - be careful")
        self.filepath=os.path.normpath(os.path.join(DATA_PATH, DATA_FILENAME))

        #4. INITIAL FEATURES: Calculate Rest IAF,bands and Thresholds
        #random upper_alpha or SMR protocol_feature
        self.initial_reward_bands, self.initial_inhibit_bands = self.baseline_thresholds( filepath=self.filepath, filetype=filetype, markernumerate=markernumerate, taskname='rest')
        msg = str({"inhibit_bands": self.initial_inhibit_bands, "reward_bands": self.initial_reward_bands })
        self.logger.info(msg)

    def on_play_nft(self, markernumerate=0):
        """
        On play NFT
        adaptative_threshold: None | float (s) update time of threshold
        """
        ###ONLINE NEUROFEEDBACK PIPELINE

        #validate threshold
        if not self.adaptative_threshold_intask:
            if not self.initial_reward_bands or not my.dictfinditem(self.initial_reward_bands, "threshold"):
                self.logger.warning('>> Note: Missing reward bands initial threshold. Calculating using firs block of data')


        #5 Online Neurofeedback Training
        self.on_nft_bci(markernumerate=markernumerate,
                        save_online_result=True)

    def on_play(self, markernumerate=0):
        """
        """
        ##UPDATE/RESET
        self.update_file_path()#WARNING: NECESSARY
        self.start_time = time.time()


        ###OFFLINE BASELINE THRESHOLDS
        if self.get_baseline_thresholds: self.on_play_baseline(markernumerate=markernumerate)

        #WARNING: Initial thresholds are important for nft signal presentation

        ###ONLINE NEUROFEEDBACK PIPELINE
        self.on_play_nft(markernumerate=markernumerate)

        ###LOG TIME
        self.end_time = time.time()
        self.elapsed_time =self.end_time - self.start_time
        self.logger.info("!!ON_PLAY ELAPSED TIME!! : {}".format(self.elapsed_time))

if __name__ == "__main__":
    #WARNING TO SIMULATE:  USE ONLY Replay data -  Replay(PREFERABLY file_stream_player.py instead of using replayamp of nftclass)

    #replayamp
    replayamp=False
    #replay sample data (using same for online and offline if you don't acquire data)
    folderdir='e2_sample'
    filename="EG_S001_REST_ss01_b01_08102019_14h13m_rest_1"
    amp_ref=['Cz']#[] - no_ref (give manual information about the ref)
    filetoreplay=my.get_filetoreplay(folderdir=folderdir,filename=filename, filetype=".meta") #filepath

    #save folder dir
    test_folder_path=os.path.join(my.get_test_folder(), 'nftclass') #folderpath



    #1.Start Class
    nft = nftclass(replayamp=replayamp, filetoreplay=filetoreplay)
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