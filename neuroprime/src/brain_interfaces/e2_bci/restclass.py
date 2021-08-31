#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Thu Jun 3 18:11:57 2019

@author: nm.costa
"""
from __future__ import (absolute_import, division, print_function)
from builtins import * #all the standard builtins python 3 style


import time

#import copy
import sys
import os

# My functions
import neuroprime.src.utils.myfunctions as my

#import functions.eegfunctions as eeg

# My classes
from neuroprime.src.initbciclass import initbciclass

#LOGGING - logger from initbciclass
import logging
#other modules configuration
logging.basicConfig(stream=sys.stdout, level=logging.INFO)
#SET Module logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.info('Logger started')
#debugging
#import pdb


class restclass(initbciclass):


    def init(self):
        """
        Global Constants
        """
        #1.INIT Parent Class
        initbciclass.init(self)
        #2.Alter or add other functions

        #INIT SAVING
        self.TASK = "REST"
        self.subtask = ""

        #INIT PRESENTATION VARS
        #Presentation PROTOCOL VARS- TODO: randomize protocol_feature
        self.PROTOCOL_TYPE = "REST" #NFT or REST the functions will change it accordingly
        self.PROTOCOL_DESIGN = "normal" #ABA or Normal -
        self.STIM_TIME = 60*3#60*2


        ##EXPERIMENT VARS


    def off_rest_bci(self, presType="pyff", markernumerate=0):
        # ------
        # Acquire Baseline data
        # method: Rest state with eyes closed
        #-------
        self.logger.info("\n>> ***off_rest_bci***")

        if presType == "pyff":
            #INIT VARS
            self.PROTOCOL_TYPE = self.PROTOCOL_TYPE
            self.STIM_TIME = self.STIM_TIME
            #instructions
            pcol_eyes=""
            if self.protocol_eyes=='eyes_closed_v2':
                self.INIT_TEXT = "TAREFA: ESTADO DE REPOUSO OLHOS FECHADOS.    BLOCO: {} / {} \n\n\nAproveite agora para respirar, beber água ou chamar o investigador caso necessite de ajuda para ficar mais confortável. \n\n\nDurante as tarefas, mantenha os OLHOS FECHADOS. \n\nTente não mexer a cabeça ou piscar os olhos!\n\nColoque-se confortavelmente e TENTE RELAXAR.".format(self.BLOCK_NR, self.TOTAL_BLOCK_NR)
                self.STIMULUS_TEXT ="Mantenha os OLHOS FECHADOS e TENTE RELAXAR!"
                pcol_eyes="ec"
            if self.protocol_eyes=='eyes_open_v2':
                self.INIT_TEXT = "TAREFA: ESTADO DE REPOUSO OLHOS ABERTOS seguido por NEUROFEEDBACK.    BLOCO: {} / {} \n\n\n\n\nDurante as tarefas, mantenha os OLHOS ABERTOS focados no ecrã. \nTente não mexer a cabeça ou piscar os olhos!\n\nColoque-se confortavelmente e TENTE RELAXAR.".format(self.BLOCK_NR, self.TOTAL_BLOCK_NR)
                self.STIMULUS_TEXT ="Mantenha os OLHOS ABERTOS focados na cruz e TENTE RELAXAR!\n\n\n\n\n\n\n\n\n\n+"
                pcol_eyes="eo"
            if self.protocol_eyes=='eyes_open':
                self.INIT_TEXT = "TAREFA: ESTADO DE REPOUSO OLHOS ABERTOS seguido por NEUROFEEDBACK.    BLOCO: {} / {} \n\n\nAproveite agora para respirar, beber água ou chamar o investigador caso necessite de ajuda para ficar mais confortável. \n\n\nDurante as tarefas, mantenha os OLHOS ABERTOS focados no ecrã. \n\nTente não mexer a cabeça ou piscar os olhos!\n\nColoque-se confortavelmente e TENTE RELAXAR.".format(self.BLOCK_NR, self.TOTAL_BLOCK_NR)
                self.STIMULUS_TEXT ="Mantenha os OLHOS ABERTOS focados na cruz e TENTE RELAXAR!\n\n\n\n\n\n\n\n\n\n+"
                pcol_eyes="eo"
            if self.protocol_eyes=='eyes_closed':
                self.INIT_TEXT = "TAREFA: ESTADO DE REPOUSO OLHOS FECHADOS seguido por NEUROFEEDBACK.    BLOCO: {} / {} \n\n\nAproveite agora para respirar, beber água ou chamar o investigador caso necessite de ajuda para ficar mais confortável. \n\n\nDurante as tarefas, mantenha os OLHOS FECHADOS. \n\nTente não mexer a cabeça ou piscar os olhos!\n\nColoque-se confortavelmente e TENTE RELAXAR.".format(self.BLOCK_NR, self.TOTAL_BLOCK_NR)
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





    def on_play(self, markernumerate=0):
        """
        ON PLAY

        Play the one trial
        """
        ##UPDATE/RESET
        self.update_file_path()#WARNING: NECESSARY
        self.start_time = time.time()


        ###OFFLINE PIPELINE
        self.off_rest_bci(  markernumerate=markernumerate)

        ###LOG TIME
        self.end_time = time.time()
        self.elapsed_time =self.end_time - self.start_time
        self.logger.info("!!ON_PLAY ELAPSED TIME!! : {}".format(self.elapsed_time))

if __name__ == "__main__":
    #1.Start Class
    rest = restclass(inlet_block_time=None)
    #save folder dir
    test_folder_path=os.path.join(my.get_test_folder(), 'restclass') #folderpath

    try:
        #2.RE-INIT Vars
        #SAVING - Reinitialize parameters
        rest.SAVE = True
        #Start dialogue
        info={'SAVE': ['no', 'yes'], 'savefolder': test_folder_path, 'subject':999, 'session':999, 'exp_version': 2,
              'group': ['EG', 'CG', 'PILOT'], "technician": "Nuno Costa"}
        title='test experiment'
        fixed=['exp_version']
        newinfo=my.gui_dialogue(info=info,title=title,fixed=fixed)


        #SAVE VARS
        rest.FOLDER_DATA = newinfo['savefolder']
        rest.GROUP = newinfo['group']  #EG or CG
        rest.SUBJECT_NR = newinfo['subject']
        rest.SESSION_NR = newinfo['session']

        if newinfo['SAVE']=='yes': rest.SAVE= True
        if newinfo['SAVE']=='no': rest.SAVE= False

        #RUN EXPERIMENT
        rest.PROTOCOL_DESIGN = "normal" #ABA or Normal
        rest.on_init()  #INIT Methods - Saving, Acquisition and Presentation
        #PLAY
        st=time.time()
        rest.on_play_check(markernumerate=rest.TASK_NR)
        et =time.time() - st
        rest.logger.info("!!ELAPSED TIME INIT METHODS BCICLASS!! : {}".format(et))
        rest.on_quit()
    except Exception as e:
        rest.logger.error("SOMETHING WENT WRONG: {}".format(e))
        rest.on_quit()