#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Fri Apr 27 14:13:08 2018

@author: nm.costa
"""

from __future__ import division

import sys
# Get src path
sys.path.append("../../")  # appending src folder to the path
import random
import time
import os
import pygame
#my feedback class
from myfeedclass import myfeedclass

from pylsl import StreamInfo, StreamOutlet, local_clock

import logging
#set for this file
logging.basicConfig(level=logging.DEBUG)


class init(myfeedclass):
    # 1st method - init called automatically when feedback is initialized - you cans set this variables from wyrm
    def init(self):
        #init method of the parent PygameFeedback class
        myfeedclass.init(self)
        #caption
        self.caption = "INIT Presentation"
        
        # Markers -TRIGGER VALUES FOR THE PARALLELPORT (Numbers 1-250) or LSL (Strings)
        self.START_MARKER= "START_EXP_INIT"

        #REST STATE Protocol GLOBALS
        self.STOP_TIME = 200 # s -+10s for time issues
        self.PROTOCOL = "eyes_closed"
        self.TEXT = "Vamos iniciar a tarefa:\n\n1) 2 minutos de Estado de repouso;\n2)Sessao de NFT."

        self.logger.info("Feedback successfully loaded: " + self.caption)



if __name__ == "__main__":
#Testing the Feedback
    fb = init()
    try:
        fb.on_init()
        fb.on_play()
        fb.on_stop()
    except:
        fb.logger.error("ERROR FEEDBACK: {}".format(fb.caption))
        fb.on_stop()
