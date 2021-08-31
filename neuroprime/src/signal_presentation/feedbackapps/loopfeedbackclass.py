#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Mon Jul 30 12:58:19 2018

Loopfeedbackclass loops through feedbackclass
Aim to reduce initiation and transition between tasks

@author: nm.costa
"""


from __future__ import division  #It creates int problems in older divisions

__version__="2.0"


#import sys
#import os
#import random
import time
#import copy
import pygame

# My functions
#import maincode.src.functions.myfunctions as my
from feedbackclass import feedbackclass






class loopfeedbackclass(feedbackclass):

    def init(self):
        self.logger.info("INIT")
        #init method of the parent PygameFeedback class
        feedbackclass.init(self)
        self.quitfeedback = False




    def pre_mainloop(self):
        """This pre_mainloop is independent from feedbackclass.
        This is because you just want to init_graphics and not pygame in each iteration"""
        self.logger.info("PRE_MAINLOOP LOOPFEEDBACKCLASS")
        #LOG INPUT VARS for debug
        self.logger.debug("*************!!!SELF DICT START!!!*************")
        self.logger.debug(self.__dict__)
        self.logger.debug("*************!!!SELF DICT END!!!*************")



        #INIT GRAPHICS - HEAVY STUFF
        self.init_graphics()
        self.logger.debug("PROTOCOL_TYPE: {} ; PROTOCOL_DESIGN: {}".format(self.PROTOCOL_TYPE, self.PROTOCOL_DESIGN))

        #------
        #Start Mainloop
        #------
        ## TIME
        #STOP CONDITION
        self.STOP_TIME=None
        if self.stop_condition:
            self.STOP_TIME = self.STIM_TIME*360#scalar number - IF SOMETHING GOES Wrong it explodes the app program -
            #a QUIT event is scheduled. This event will appear in Pygame's event queue after the given time and marks the regular end of the Feedback
            pygame.time.set_timer(pygame.QUIT, self.STOP_TIME * 1000)
        #CLOCKS
        self.current_exp_clock = pygame.time.Clock()
        self.tick_clock = pygame.time.Clock()
        self.tick_time = 0
        start_tick = self.current_exp_clock.tick() / 1000.
        #send marker
        self.send_lsl(self.START_MARKER)
        self.logger.info("{} : {}".format(self.START_MARKER, start_tick))
        #INTRO Screen - The first GUI to appear - TODO: wait for keypress before starting
        self.present_symbols(self.initSymbol)

    def post_mainloop(self):
        self.logger.info("POST_MAINLOOP")
        self.logger.debug("#TODO be careful where to use quitfeedback - because if you didn't send it early it will not end")
        # time since the last call
        stop_tick = self.current_exp_clock.tick() / 1000.
        elapsed_pre_post = stop_tick
        #send end marker
        self.send_lsl(self.END_MARKER)
        self.logger.info("{} : {}".format(self.END_MARKER, elapsed_pre_post))
        self.logger.debug("Elapsed time from pygame.init(), in ms: {}".format(pygame.time.get_ticks()))
        #end cue
        if self.on_sound_cue_bell:
            ch = self.sound_cue_bell.play()  #channel playing
            while ch.get_busy():
                pygame.time.delay(100)
        self.loading_screen()

        ##loop
        #1.Stop all sound chs active
        pygame.mixer.stop()
        #2.reinit
        self.on_reinit()




    def on_reinit(self):
        self.logger.info("ON_REINIT")
        #1.reinit parent vars
        feedbackclass.on_init(self)  #reinit parent on_init without needing to send interaction sendinit
        #2.update screen with BACKGROUND CANVAS
        self.update_screen()




    def on_quit(self):
        self.logger.info("ON_QUIT")
#        self.END_MARKER ="END"
        #end everything using parent class
        feedbackclass.post_mainloop(self)
        feedbackclass.on_quit(self)

    def on_init(self):
        """
        On init

        Necessary to start only one time the things that take more time
        """
        self.logger.info("ON_INIT")
        feedbackclass.on_init(self)  #called in send_init
        feedbackclass.init_pygame(self) #init pygame only one time
        self.logger.debug("#NOTE #WARNING pygame engine is inited only one time, therefore, parameters that are used in pygame.init(), can't be updated aftwards with set_pyff_variables, e.g. fullscreen, FPS, ...")
        #clock for all experiment - starting on send_init and if you call self.quitfeedback that goes to parent post_mainloop
        self.exp_clock = pygame.time.Clock()
        start_tick = self.exp_clock.tick() / 1000.
        self.logger.info("{} : {}".format("BEGIN OF EXPERIMENT", start_tick))


"""UTILS"""
def dictfinditem(obj, key):
    if key in obj: return obj[key]
    for k, v in obj.items():
        if isinstance(v,dict):
            item = dictfinditem(v, key)
            if item is not None:
                return item
    return False

if __name__ == "__main__":
#Testing the Feedback
    fb = loopfeedbackclass()
    try:
        fb.on_init()
        fb.on_play()
        print("END ON_PLAY")
        fb.on_play()
        print("END ON_PLAY")
        fb.on_play()
        print("END ON_PLAY")
        fb.on_stop()
        fb.on_quit()
        print("END ON_STOP ON_QUIT")
        fb.quitfeedback = True
        fb.on_play()
        print("END ON_PLAY")
    except:
        fb.logger.error("ERROR FEEDBACK: {}".format(fb.caption))
        fb.on_stop()
        fb.on_stop()
        time.sleep(10)
        fb.on_quit()