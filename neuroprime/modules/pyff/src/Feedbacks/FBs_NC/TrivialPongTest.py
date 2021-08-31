#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Tue Nov 21 15:23:03 2017

SCRIPT:
    Implementing simple Pong Game Feedback subclass in a BCI System- Bastian Venthur Thesis
    Properties:
        Ball bounces everywhere - Bar and walls
        No penalties
        Ball controlled by BCI system using motor imagery techniques
        DATA: BCI System classification output value [-1...1] via control-signal
        MARKERS: Sending trough _lsl_outlet stream created from the

    Packages:
        Pygame graphical toolkit

    Supported by pyff via PygameFeedback base class - Adevantage: easier to implement, Takes care of:
        implementing pygame
        Initializing graphics
        setting screen size, position etc
        play_tick method - Game main loop that iterates several times per second (ticks) -> derived from MainloopFeedback class and Pygame main loop - can be overwritten

    pylsl marker

@author: Nuno costa
"""
import sys
# Get src path
sys.path.append("../../")  # appending src folder to the path
import random
import time
import os
import pygame
from FeedbackBase.PygameFeedback import PygameFeedback
import logging
from pylsl import StreamInfo, StreamOutlet, local_clock
# Config Logging to see or emit errors
logging.basicConfig(level=logging.DEBUG)

# Create trivial pong and pass to it the PygameFeedback class
class TrivialPongTest(PygameFeedback):

    # TRIGGER VALUES FOR THE PARALLELPORT (MARKERS)
    START_EXP, END_EXP = 100, 101
    COUNTDOWN_START = 30
    START_TRIAL = 35
    HIT, MISS = 11, 21
    SHORTPAUSE_START, SHORTPAUSE_END = 249, 250
    TEST_TICK = 1

    # 1st method - init called automatically when feedback is initialized - overwrite
    def init(self):
        PygameFeedback.init(self)  #init metho of the parent PygameFeedback class
        self.caption = "Trivial Pong Test NC"
        # self.send_parallel(self.START_EXP)
        self.send_lsl("START")
        # set the initial value for the classifier output
        self.val = 0.0
        # set the initial speeds for ball and bar
        self.barspeed = [3, 0]
        self.speed = [2, 2]
        print ("Feedback successfully loaded: " + self.caption)


    # 2nd method - only load graphics needed - inherited from PygameFeedback class - automatically called when feedback is started
    def init_graphics(self):
        # load graphics
        path = os.path.dirname(globals()["__file__"])  # __file__ is attribute of a model - the pathname of the file from wich the module was loaded - Pygame
        # load and create bar and ball objects
        self.ball = pygame.image.load(os.path.join(path, "ball.png"))
        self.ballrect = self.ball.get_rect()
        self.bar = pygame.image.load(os.path.join(path, "bar.png"))
        self.barrect = self.bar.get_rect()

    # 3rd method: control signals - inherited from FeedbackBase class - called whenever Feedback controller receives new data - overwrite to update value to classification output
    def on_control_event(self, data):
        self.val = data["clout"] # clout - classification output

    # 4th method: play_tick method - called several time per second - from feedback start till it stops - depends on the FPS variable - default value of 30 - PygameFeedback Class
    def play_tick(self):
        # screen
        width, height = self.screenSize
        w_half = width / 2.
        # move bar and ball
        pos = w_half + w_half * self.val
        self.barrect.center = pos, height - 20
        self.ballrect = self.ballrect.move(self.speed)
        # collision detection walls
        if self.ballrect.left < 0 or self.ballrect.right > width:
            self.speed[0] = -self.speed[0]
        if self.ballrect.top < 0 or self.ballrect.bottom > height:
            self.speed[1] = -self.speed[1]
        if self.barrect.left < 0 or self.barrect.right > width:
            self.barspeed[0] = -self.barspeed[0]
        if self.barrect.top < 0 or self.barrect.bottom > height:
            self.barspeed[1] = -self.barspeed[1]
        # collision detection for bar vs ball
        if self.barrect.colliderect(self.ballrect):
            self.speed[0] = -self.speed[0]
            self.speed[1] = -self.speed[1]
        # update the screen
        self.screen.fill(self.backgroundColor)
        self.screen.blit(self.ball, self.ballrect)
        self.screen.blit(self.bar, self.barrect)
        pygame.display.flip()
        # Send marker in each tick


        markernames = ['Pyff-M1', 'Pyff-M2', 'Pyff-M3', 'Pyff-M4', 'Pyff-M5', 'Pyff-M6']
        # pick a sample to send an wait for a bit - working
        MK = random.choice(markernames)
        # LSL
        # outlet = self._lsl_outlet
        # outlet.push_sample([MK])
        self.send_lsl(MK)
        # self.send_parallel(self.TEST_TICK)
        # self.send_udp(MK)

    def post_mainloop(self):
        self.logger.debug("Quitting pygame.")
        #self.send_parallel(self.END_EXP)
        self.send_lsl("END")
        PygameFeedback.post_mainloop(self)

    def on_quit(self):
        print "Feedback quit!"


#
if __name__ == "__main__":
#Testing the Feedback
   fb = TrivialPongTest()
   fb.on_init()
   fb.on_play()
