#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Fri May  3 13:26:20 2019

@author: nm.costa
"""

from neuroprime.src.initbciclass import initbciclass
import time

class testclass(initbciclass):
    def init(self):
        """
        INIT Global Constants
        """
        #1.INIT Parent Class
        initbciclass.init(self)
        #2.Alter or add other functions

    def on_play(self, markernumerate=0):
        """
        PLAY
        """
        ##UPDATE/RESET
        self.update_file_path() #update filename with BLOCK_NR

        #Instructions
        self.INIT_TEXT="\n\n\n\n\nTASK 1: Estado de Repouso, 2 min!"

        #Stimulus
        self.STIMULUS_TEXT ="\n\n\n\n\n\n\n\n\n\n+"
        self.PROTOCOL_TYPE =  "REST"
        self.PROTOCOL_DESIGN = "normal" #normal, ABA
        self.STIM_TIME = 60*1 #s
        self.subtask='rest'+"_"+str(markernumerate)
        self.START_MARKER = "START_"+self.subtask
        self.END_MARKER = "END_"+self.subtask

        #START loop of data
        self.start_time = time.time() #start time
        self.on_loop() #online loop
        self.end_time = time.time()  #end time
        self.elapsed_time =self.end_time - self.start_time

if __name__ == "__main__":
    #1.Start Class
    test = testclass()
    #2.SAVE information
    test.SAVE = False
    test.FOLDER_DATA = "/Users/testdata" #folder to save the data
    test.GROUP = 'TEST'
    test.SUBJECT_NR = 1
    test.SESSION_NR = 1

    #INIT Methods - Saving, Acquisition and Presentation
    test.on_init()

    #start experiment
    test.BLOCK_NR = 1 #1st trial
    test.on_play(markernumerate=test.BLOCK_NR)
    test.BLOCK_NR = test.BLOCK_NR+1 #2nd trial
    test.on_play(markernumerate=test.BLOCK_NR)

    #quit
    test.on_quit()