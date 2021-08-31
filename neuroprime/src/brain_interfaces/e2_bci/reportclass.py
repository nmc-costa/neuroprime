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


class reportclass(initbciclass):


    def init(self):
        """
        Global Constants
        """
        #1.INIT Parent Class
        initbciclass.init(self)
        #2.Alter or add other functions

        #INIT SAVING
        self.TASK = 'REPORT'
        self.subtask = ""
        self.SAVE=False #always

        #INIT PRESENTATION VARS
        #Presentation PROTOCOL VARS- TODO: randomize protocol_feature
        self.PROTOCOL_TYPE = "REPORT" # report
        self.PROTOCOL_DESIGN = "normal" #ABA or Normal -
        #presentation init screen
        self.INIT_TEXT = "TAREFA: RESPONDER AOS QUESTIONÁRIOS \n\n\nPor favor, pegue nos questionários indicados e preencha. \n\n\nAssim que preencher, continue com as tarefas neste computador após clicar no enter."
        #stimulus screen(No Stim)
        self.STIMULUS_TEXT ="\n\n\n\n\n\n\n\n\nCarregando tarefa....."
        self.STIM_TIME = 0.5 #s

        ##EXPERIMENT VARS


    def off_report_bci(self, presType="pyff", markernumerate=0):
        """
        Simple Instructions screen
        """
        self.logger.info("\n>> ***off_report_bci***")

        if presType == "pyff":
            #INIT VARS
            self.PROTOCOL_TYPE = self.PROTOCOL_TYPE
            self.INIT_TEXT = self.INIT_TEXT
            self.STIMULUS_TEXT = self.STIMULUS_TEXT
            self.STIM_TIME = self.STIM_TIME #s
            self.subtask="report"+"_"+str(markernumerate)
            self.START_MARKER = "START_"+self.subtask #Obrigatory to send start and stop
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
        self.off_report_bci(markernumerate=markernumerate)

        ###LOG TIME
        self.end_time = time.time()
        self.elapsed_time =self.end_time - self.start_time
        self.logger.info("!!ON_PLAY ELAPSED TIME!! : {}".format(self.elapsed_time))

if __name__ == "__main__":
    #1.Start Class
    report = reportclass()
    try:
        report.on_init()  #INIT Methods - Saving, Acquisition and Presentation
        #PLAY
        st=time.time()
        report.on_play(markernumerate=report.BLOCK_NR)
        et =time.time() - st
        report.logger.info("!!ELAPSED TIME INIT METHODS BCICLASS!! : {}".format(et))
        report.on_quit()
    except Exception as e:
        report.logger.error("SOMETHING WENT WRONG: {}".format(e))
        report.on_quit()