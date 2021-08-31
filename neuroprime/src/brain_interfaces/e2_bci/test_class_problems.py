# -*- coding: utf-8 -*-
"""
Created on Thu Oct 10 11:15:58 2019

@author: nm.costa
"""
from __future__ import (absolute_import, division, print_function) #unicode_literals - more info needed to addapt; absolute_import does not let you to import from current folder, need to specify from the main package neuroprime...
from builtins import * #all the standard builtins python 3 style

import os
import time
## My functions
import neuroprime.src.utils.myfunctions as my
from neuroprime.src.initbciclass import initbciclass
from neuroprime.src.brain_interfaces.e2_bci.primeclass import primeclass
from neuroprime.src.brain_interfaces.e2_bci.reportclass import reportclass

def test_1():
    """BUG: Report class is breaking  next task
    SOLVED:
    """
    bci = initbciclass()
    prime = primeclass()
    report = reportclass()



    #save folder dir
    test_folder_path=os.path.join(my.get_test_folder(), 'test_class_problems') #folderpath

    #1.Start Class
    report = reportclass()
    prime = primeclass()
    try:
        #2.RE-INIT Vars
        #SAVING - Reinitialize parameters
        bci.SAVE=prime.SAVE= False
        report.SAVE=False#Nao grave
        bci.SAVE_TASK=prime.SAVE_TASK=report.SAVE_TASK=True#report.SAVE_TASK

        #Start dialogue
        info={'savefolder': test_folder_path, 'subject':1, 'session':1, 'exp_version': 2,
              'group': ['EG', 'CG', 'PILOT'], "technician": "Nuno Costa"}
        title='test experiment'
        fixed=['exp_version']
        newinfo=my.gui_dialogue(info=info,title=title,fixed=fixed)

        #Save vars
        bci.FOLDER_DATA=prime.FOLDER_DATA = newinfo['savefolder']
        bci.GROUP=bci.FOLDER_DATA=prime.GROUP = newinfo['group']  #EG or CG
        bci.SUBJECT_NR =prime.SUBJECT_NR = newinfo['subject']
        bci.SESSION_NR=prime.SESSION_NR = newinfo['session']


        #INIT Methods - Saving, Acquisition and Presentation
        bci.on_init()
        #1.PRESENTATION PATCHING
        prime.pyff = bci.pyff
        report.pyff= bci.pyff
        #2.ACQUISITON PATCHING
        prime.amp = bci.amp
        report.amp=bci.amp

        #Experiment Vars
        prime.audiostimulus_l = ["imagery_v6.ogg" ]
        #random.shuffle(prime.audiostimulus_l)

        #Task 1 report
        report.START_WAIT_FOR_KEY=True
        report.on_play_check()


        #Task 2 stim
        prime.STIM_TIME= 30 #s
        prime.protocol_eyes="eyes_open"
        prime.START_WAIT_FOR_KEY=True

        #PLAY
        for i,stim in enumerate(prime.audiostimulus_l):
            print ("RUN STIMULUS:", stim)
            prime.BLOCK_NR = i+1 #BLOCK
            prime.on_play(audiostimulus=stim, videostimulus=None, imagestimulus=None, textstimulus=None, markernumerate=prime.BLOCK_NR)


        bci.on_quit()
    except:
        bci.on_quit()

if __name__ == "__main__":
    test_1()