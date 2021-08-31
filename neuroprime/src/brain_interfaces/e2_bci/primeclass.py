#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Tue May  1 11:09:39 2018

@author: nm.costa
"""

from __future__ import division

import time

import os

import random

# My functions
import neuroprime.src.utils.myfunctions as my

# My classes
from neuroprime.src.initbciclass import initbciclass
#LOGGING - logger from initbciclass



class primeclass(initbciclass):

    """
    INIT all class Variables and constants
    """

    def init(self):
        """
        Global Constants
        """
        # 1.INIT Parent Class
        initbciclass.init(self)
        # 2.Alter or add other vars

        #INIT SAVING
        self.TASK = 'PRIME'  #
        self.subtask = "ALLTASKS"  #ALL TASKs in same FILE

        #INIT PRESENTATION VARS

        #Presentation PROTOCOL VARS
        self.PROTOCOL_TYPE =  "prime" #
        self.PROTOCOL_DESIGN = "normal" #normal, test
        #presentation init screen
        self.INIT_TEXT = "Vamos iniciar a tarefa de Pre-treino:"

        self.STIM_TIME = 60*3 #s

        ##EXPERIMENT VARS

        #INIT prime Stimulus
        #random seed
        self.random_seed = None  #None or no argument seeds from current time or from an operating system specific randomness source if available
        #STIMULUS LIST
        self.audiostimulus_l = ["breathingv6.ogg", "imageryv6.ogg"] #stimulus file name from maincode.stimulus folder
        self.videostimulus_l = None
        self.imagestimulus_l = None





    """
    OFFLINE

    Randomized presentation of fixed number of stimulus
    """



    def offline_priming(self, audiostimulus=None, videostimulus=None, imagestimulus=None, textstimulus=None, presType="pyff", markernumerate=0):
        """
        OFFLINE Priming

        Randomized presentation of fixed number of stimulus
        """
        self.logger.info("***offline_priming***")


        if presType == "pyff":
            #INIT VARS
            self.PROTOCOL_TYPE =  "stimulus"
            self.audiostimulus = audiostimulus
            self.videostimulus = videostimulus
            self.imagestimulus = imagestimulus
            self.textstimulus = textstimulus
            self.STIM_TIME = self.STIM_TIME
            #Instructions
            pcol_eyes=""
            if self.protocol_eyes=="eyes_open":
                self.INIT_TEXT = "primeclass a comecar OLHOS ABERTOS"
                self.STIMULUS_TEXT = "Mantenha os OLHOS ABERTOS focados na cruz, atento ás instruções auditivas!\n\n\n\n\n\n\n\n\n\n+"
                pcol_eyes="eo"
            if self.protocol_eyes=="eyes_closed":
                self.INIT_TEXT = "primeclass a comecar OLHOS FECHADOS"
                self.STIMULUS_TEXT = "Mantenha os OLHOS FECHADOS, atento ás instruções auditivas!"
                pcol_eyes="ec"
            #change instructions depending on stimulus
            stimulus=""
            if self.audiostimulus:
                typestimulus='PRATICA GUIADA "{}" '.format(self.audiostimulus)
                if not self.audiostimulus.find("whm")==-1:
                    typestimulus="PRATICA DE RESPIRAÇÃO GUIADA, METODO WIM HOF,".upper()
                if not self.audiostimulus.find("breath")==-1:
                    typestimulus="PRATICA DE RESPIRAÇÃO GUIADA".upper()
                if not self.audiostimulus.find("imag")==-1:
                    typestimulus="PRATICA DE IMAGINAÇÃO GUIADA".upper()
                self.INIT_TEXT = "TAREFA: {} seguida por NEUROFEEDBACK.    BLOCO: {} / {} \n\n\nDurante a PRATICA GUIADA se perceber que começou a pensar noutra coisa, saiba que é normal, divagar faz parte da natureza da mente, apenas observe a distração, e gentilmente volte a sua atenção para a tarefa. \n\nTente não mexer a cabeça ou piscar os olhos!\n\nColoque-se confortavelmente. ".format(typestimulus, self.BLOCK_NR, self.TOTAL_BLOCK_NR)
                if self.protocol_eyes=="eyes_open": self.INIT_TEXT=self.INIT_TEXT+"\n\n\nDurante as tarefas, mantenha os OLHOS ABERTOS focados no ecrã, atento ao audio."
                if self.protocol_eyes=="eyes_closed": self.INIT_TEXT=self.INIT_TEXT+"\n\n\nDurante as tarefas, mantenha os OLHOS FECHADOS, atento ao audio."
                stimulus, _ = os.path.splitext(self.audiostimulus)
                self.PROTOCOL_TYPE =  "audiostimulus"

            if self.videostimulus: #NOT IMPLEMENTED
                self.INIT_TEXT = None
                stimulus, _ = os.path.splitext(self.videostimulus)
                self.PROTOCOL_TYPE =  "videostimulus"
            if self.imagestimulus:#NOT IMPLEMENTED
                self.INIT_TEXT = None
                stimulus, _ = os.path.splitext(self.videostimulus)
                self.PROTOCOL_TYPE =  "imagestimulus"
            if self.textstimulus:
                stimulus="textstim"
                self.INIT_TEXT = self.textstimulus #INIT INSTRUCTIONS
                self.STIMULUS_TEXT = ""#self.STIMULUS_TEXT #SAME as INSTRUCTIONS
                self.PROTOCOL_TYPE =  "textstimulus"




            self.subtask=stimulus+"_"+str(markernumerate)
            if pcol_eyes: self.subtask=stimulus+"_"+pcol_eyes+"_"+str(markernumerate) #type: subtask_pcol_eyes_tasknumber
            self.START_MARKER = "START_"+self.subtask
            self.END_MARKER = "END_"+self.subtask
            #Loop
            self.on_loop()


        if presType == "psychopy":
            pass #TODO: IMPLEMENT






    """
    Online

    Real time Selection of stimulus based on the target

    Machine learning framework

    Should be similar to the Neurofeedback closed loop aplication

    """


    def online_priming(self):
        pass






    def on_play(self, audiostimulus=None, videostimulus=None, imagestimulus=None ,textstimulus=None, markernumerate=1):
        """
        ON Play

        Play one session of the class
        """
        ##UPDATE/RESET
        self.update_file_path()#WARNING: NECESSARY
        self.start_time = time.time()


        ###OFFLINE PiPELINE
        if self.PROTOCOL_DESIGN=="normal":
            self.logger.debug("AUDIO: {}".format(self.audiostimulus))
            self.offline_priming(audiostimulus=audiostimulus, videostimulus=videostimulus, imagestimulus=imagestimulus, textstimulus=textstimulus, markernumerate=markernumerate)



        self.end_time = time.time()
        self.elapsed_time =self.end_time - self.start_time
        self.logger.info("!!ON_PLAY ELAPSED TIME!! : {}".format(self.elapsed_time))



if __name__ == "__main__":
    #WARNING TO SIMULATE:  USE Generated data or Replay data ( - Generated(outlet_actichamp.py,sine waves), Replay(PREFERABLY file_stream_player.py or class replayamp - does not simulate all)
    replayamp=False

    #replay sample data
    filetoreplay=my.get_filetoreplay() #filepath

    #save folder dir
    test_folder_path=my.get_test_folder() #folderpath


    #1.Start Class
    prime = primeclass(replayamp=replayamp, filetoreplay=filetoreplay)
    try:
        #2.RE-INIT Vars
        #SAVING - Reinitialize parameters
        #Start dialogue
        info={'SAVE': ['no', 'yes'],'savefolder': test_folder_path, 'subject':1, 'session':1, 'exp_version': 2,
              'group': ['EG', 'CG', 'PILOT'], "technician": "Nuno Costa"}
        title='test experiment'
        fixed=['exp_version']
        newinfo=my.gui_dialogue(info=info,title=title,fixed=fixed)

        #Save vars
        prime.FOLDER_DATA = newinfo['savefolder']
        prime.GROUP = newinfo['group']  #EG or CG
        prime.SUBJECT_NR = newinfo['subject']
        prime.SESSION_NR = newinfo['session']

        if newinfo['SAVE']=='yes': prime.SAVE= True
        if newinfo['SAVE']=='no': prime.SAVE= False

        #Experiment Vars
        prime.PROTOCOL_TYPE =  "prime" #
        prime.PROTOCOL_DESIGN = "normal" #test & normal

        #Randomize Stimulus
        random.seed()#None or no argument seeds from current time or from an operating system specific randomness source if available
        prime.audiostimulus_l = ["imageryv6.ogg" ]
        #random.shuffle(prime.audiostimulus_l)

        #INIT Methods - Saving, Acquisition and Presentation
        prime.on_init()

        st=time.time()
        #PLAY
        for i,stim in enumerate(prime.audiostimulus_l):
            print ("RUN STIMULUS:", stim)
            prime.BLOCK_NR = i+1 #BLOCK
            prime.on_play(audiostimulus=stim, videostimulus=None, imagestimulus=None, textstimulus=None, markernumerate=prime.BLOCK_NR)

        et =time.time() - st
        prime.logger.info("!!ELAPSED TIME prime TEST!! : {}".format(et))
        prime.serialize(objectname="primeclass_finalstate")
        prime.on_quit()
    except:
        prime.logger.error("SOMETHING WENT WRONG")
        prime.on_quit()
