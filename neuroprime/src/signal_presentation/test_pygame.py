#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Tue Aug 27 10:57:00 2019

@author: nm.costa
"""
from __future__ import (absolute_import, division, print_function)
from builtins import * #all the standard builtins python 3 style


import os
import time

def pygame_test_mixer():
    import pygame
    import neuroprime.src.utils.myfunctions as my
    import neuroprime.stimulus
    stimdir=os.path.abspath(neuroprime.stimulus.__file__)
    stimdir, filen, ext =my.parse_path_list(stimdir) #parse
    #filepath
    filepath_r= os.path.join(stimdir,'c1_A_bass_organ.ogg')
    filepath_i= os.path.join(stimdir,'c1_G_bass_organ.ogg')
    #INIT AUDIO
    pygame.mixer.init()  # init sound engine
    #INIT Sounds
    sound_ch_n=pygame.mixer.get_num_channels() #generally 8 chs
    sound_feedback_ch = pygame.mixer.Channel(sound_ch_n-1)
    sound_feedback_reward= pygame.mixer.Sound(filepath_r)
    sound_feedback_inhibit= pygame.mixer.Sound(filepath_i)
    #play
    sound_feedback_ch.play(sound_feedback_reward) 
    time.sleep(5)
    sound_feedback_ch.play(sound_feedback_inhibit)
    time.sleep(5)
    sound_feedback_ch.play(sound_feedback_reward) 
    time.sleep(5)
    #Quit mixer
    pygame.mixer.quit()

if __name__ == "__main__":
    pygame_test_mixer()