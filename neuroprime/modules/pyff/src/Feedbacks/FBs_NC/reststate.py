#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Fri Mar 16 10:30:57 2018

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


class reststate(myfeedclass):

    # 1st method - init called automatically when feedback is initialized - overwrite
    def init(self):
        #init method of the parent PygameFeedback class
        myfeedclass.init(self)
        #caption
        self.caption = "Rest state Presentation"
        # Markers -TRIGGER VALUES FOR THE PARALLELPORT (Numbers 1-250) or LSL (Strings)
        self.START_MARKER= "START_EXP_REST"
        
        #REST STATE Protocol GLOBALS
        self.STOP_TIME = 130 # s -+10s for time issues
        self.PROTOCOL = "eyes_closed"
        self.TEXT = "Feche os olhos e tente relaxar. \nQuando ouvir o som pode abrir novamente."

        self.logger.info("Feedback successfully loaded: " + self.caption)



if __name__ == "__main__":
#Testing the Feedback
    fb = reststate()
    try:
        fb.on_init()
        fb.on_play()
        fb.on_stop()
    except:
        fb.logger.error("ERROR FEEDBACK: {}".format(fb.caption))
        fb.on_stop()
   
