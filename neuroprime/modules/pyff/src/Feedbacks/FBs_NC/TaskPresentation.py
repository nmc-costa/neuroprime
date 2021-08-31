#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Mon Jan 22 11:00:53 2018

Script:
    Session App - Training Tasks Presentation app - PreT + NFT


TODO:
    Markers: Baginning of tasks
    Create a base class named Task - Make all Tasks based on the inherited

@author: nm.costa
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


class TaskPresentation(PygameFeedback):
    """Training Tasks Presentation app - PreT + NFT"""
    # Markers -TRIGGER VALUES FOR THE PARALLELPORT (Numbers 1-250) or LSL (Strings)
    START_EXP, END_EXP = "START_EXP", "END_EXP"
    COUNTDOWN_START = "COUNTDOWN_START"
    START_TRIAL = "START_TRIAL"
    SHORTPAUSE_START, SHORTPAUSE_END = "SHORTPAUSE_START", "SHORTPAUSE_END"
    TEST_TICK = "TEST_TICK"
    # 1st method - init called automatically when feedback is initialized - overwrite

    """ PygameFeedback Functions"""

    def init(self):
        """
        Initializes variables etc., but not pygame itself.
        """
        PygameFeedback.init(self)  #init metho of the parent PygameFeedback class
        self.caption = "Pre Training Signal Presentation"
        # self.send_parallel(self.START_EXP)
        self.send_lsl(self.START_EXP)
        #self.send_udp(self.START_EXP)
        #------------------
        # SET VARIABLES
        #--------------------
        #Random
        self.random_seed = 1234
        #Session Configuration
        self.sessionCounter = 0  # Sessions for each subject
        self.runCounter = 0  # Pre-T(randomized Stimulus) + NFT SMR;
        self.runs = 2  #number of runs - The max will depend on the number of stimulus - runs are differen from each other; they compose a session
        #Tasks configuration
        self.taskCounter = 0  #5 Tasks/Run; 4 tasks PreT + 1 Task NFT / per run
        self.taskName = ""  # Each of The five tasks as a name
        self.taskCfg = {
                "Task_1" :
                    {"type":"traits", "type_of_traits": "mix", "fullname" : "Personality Traits Active baseline", "shortname": "AB1", "duration" : 0, "number_of_traits" : 10, "seconds_per_trait" : 5, "pause_after": 3, "instructions": "Escolha os adjectivos que a caracterizam. Sim = Tecla S. Nao = Tecla N"},
                "Task_2" :
                    {"type" : "stimulus", "fullname":"Pre-Training Stimulus", "shortname": "S", "duration": 180, "seconds_per_trait" : 5, "pause_after": 3, "instructions": "1.Respire pausadamente; \n 2.Tente acompanhar a respiração com os estimulos Audio e visuais "},
                "Task_3":
                    {"type" : "traits",  "type_of_traits": "mix", "fullname" : "Personality Traits Active baseline", "shortname": "AB2", "duration" : 0, "number_of_traits" : 10, "seconds_per_trait" : 5, "pause_after": 3, "instructions": "Escolha os adjectivos que a caracterizam. Sim = Tecla S. Nao = Tecla N"},
                "Task_4":
                    {"type" : "self_report","fullname" : "Self-Report Evaluation", "shortname": "SRE", "duration" : 0, "pause_after": 3,"instructions": "Escolha de 0 a 9 usando a numeração do teclado."},
                "Task_5":
                    {"type" : "NFT", "fullname" : "Neurofeedback Training", "shortname": "NFT", "duration" : 300, "number_of_traits" : 10, "seconds_per_trait" : 5, "instructions": "Tente regular a sua atividade cerebral atraves de estrategias mentais"}
                }
        self.taskSave = {"Task_1" :{}, "Task_2":{} ,"Task_3" :{},"Task_4" :{},"Task_5" :{}}
        #Tasks to present:
        self.tasks_to_present = ["Task_1", "Task_3"]
        # Trials configuration
        self.trials = 0 #Trials are replicate of same experimental conditions
        # Color of the symbols
        self.color = [0, 0, 0]
        self.backgroundColor = [127, 127, 127]
        # text Fontheight in pixels
        self.fontheight = 50
        # Keys
        self.key_target = "s"
        self.key_nontarget = "n"
        # change default PygameFeedback.init values
        #self.FPS = 60
        self.fullscreen = False
        #Logger info
        self.logger.debug("on_init")
        self.logger.debug("Feedback successfully loaded: " + self.caption)

    def pre_mainloop(self):
        PygameFeedback.pre_mainloop(self)
        #plant the random seed in the beginning
        random.seed(self.random_seed)
        #TODO - ALL TASKS INIT - Create Class of Tasks
        #--------------------------------------------------------
        # TASKS INIT
        #--------------------------------------------------------
        for task in self.tasks_to_present:
            task_type = self.taskCfg[task]['type']
            # PERSONALITY TRAITS
            if task_type == "traits":
                #GENERATE TRAITS
                sample = self.generate_traits(self.taskCfg[task]['type_of_traits'], self.taskCfg[task]['number_of_traits'])
                self.taskSave[task]["sample_traits"] = sample
                self.taskSave[task]["trait_counter"] = 0
                #GENERATE SYMBOLS
                symbols = self.generate_pygame_symbols(task)
                self.taskSave[task]["symbols"] = symbols
                # The chosen traits: yesT: yes traits
                # The unchosen traits: noT: no traits
                self.taskSave[task]["yes_traits"] = []
                self.taskSave[task]["no_traits"] = []
            #Stimulus
            if task_type == "stimulus":
                pass
            #Self_report Evaluation
            if task_type == "self_report":
                pass
            #NFT
            if task_type == "NFT":
                pass


        # Initialize the logic - represents the current position in the list of stimuli
        #self.current_index = 0
        # And here we go...
        #a QUIT event is scheduled. This event will appear in Pygame's event queue after the given time and marks the regular end of the Feedback
#QUIT after presenting
        pygame.time.set_timer(pygame.QUIT, 10 * 1000)
        # Take time
        self.clock.tick()
        # Start first task
        self.present_tasks()


    def post_mainloop(self):
        #send marker
        self.send_lsl(self.END_EXP)
        # time since the last call
        elapsed_seconds = self.clock.tick() / 1000.
        # parent-quiting pygame correctly
        PygameFeedback.post_mainloop(self)
        # Total number of items processed - Limited
        #logger information
        self.logger.info("Experiment elapsed time: {:f} s".format(elapsed_seconds))
        self.logger.info("Traits that were chosen as yes Task 1: \n {:s}".format(', '.join([str(trait) for trait in self.taskSave["Task_1"]["yes_traits"]])))
        self.logger.info("Traits that were chosen as no Task 1: \n {:s}".format(', '.join([str(trait1) for trait1 in self.taskSave["Task_1"]["no_traits"]])))
        self.logger.info("Experiment elapsed time: {:f} s".format(elapsed_seconds))
        self.logger.info("Traits that were chosen as yes Task 3: \n {:s}".format(', '.join([str(trait) for trait in self.taskSave["Task_3"]["yes_traits"]])))
        self.logger.info("Traits that were chosen as no Task 3: \n {:s}".format(', '.join([str(trait1) for trait1 in self.taskSave["Task_3"]["no_traits"]])))
        self.logger.debug("Quitting pygame.")

    def tick(self):
        task = self.tasks_to_present[self.taskCounter]
        task_type = self.taskCfg[task]['type']
        #TODO: Timer of each task
        if task_type == "traits":
            #wait for pygame event
            self.wait_for_pygame_event()
            if self.keypressed: #When event keypress occurs
                tc = self.taskSave[task]["trait_counter"]
                st = self.taskSave[task]["sample_traits"]
                sym = self.taskSave[task]["symbols"]
                key = self.lastkey_unicode
                self.keypressed = False
                if key not in (self.key_target, self.key_nontarget):
                    print "Wrong key pressed."
                    return
                else:
                    print key,
                    if key == self.key_nontarget:
                        no_traits = self.taskSave[task]["no_traits"]
                        no_traits.append(st[tc])
                    elif key == self.key_target:
                        yes_traits = self.taskSave[task]["yes_traits"]
                        yes_traits.append(st[tc])
                #Switch to new trait
                self.taskSave[task]["trait_counter"] += 1
                # Finished Showing first task? - pass to another task
                if self.taskSave[task]["trait_counter"] > len(sym) - 1:
                    self.taskCounter +=1 # Switching task
                     # Finished showing All task
                    if self.taskCounter > len(self.tasks_to_present)-1:
                        self.on_stop() # finish experiment
                    else: #present new task
                        self.present_tasks()
                else: #present new traits
                    self.present_tasks()


        if task_type=="stimulus":
            pass
        if task_type=="self_report":
            pass
        if task_type=="NFT":
            pass




    def pause_tick(self):
        pass

    # method: play_tick method - called several time per second - from feedback start till it stops - depends on the FPS variable - default value of 30 - PygameFeedback Class
    def play_tick(self):
        pass


    # method - only load graphics needed - inherited from PygameFeedback class - automatically called when feedback is started
    def init_graphics(self):
        # load graphics
        path = os.path.dirname(globals()["__file__"])  # __file__ is attribute of a model - the pathname of the file from wich the module was loaded - Pygame
        # load and create bar and ball objects
#        self.ball = pygame.image.load(os.path.join(path, "ball.png"))
#        self.ballrect = self.ball.get_rect()
#        self.bar = pygame.image.load(os.path.join(path, "bar.png"))
#        self.barrect = self.bar.get_rect()

    # method: control signals - inherited from FeedbackBase class - called whenever Feedback controller receives new data - overwrite to update value to classification output - NFT
    def on_control_event(self, data):
        self.val = data["clout"] # clout - classification output


    def on_quit(self):
        self.logger.info("Feedback quit!")


    """ SPECIfIC Functions"""

    def generate_traits(self, type_of_traits, number):
        """Generate random Traits
        TODO: don't repeat traits in task 1 and 2 and between runs!!'
            Do other types
        """
        self.logger.info("GENERATING Personality Traits")
        # type_of_traits:
        # Deffault -> Random: "positive"; "neutral"; "negative"; "mix"; "random"
        # TODO -> Non-random: "positive"; "neutral"; "negative"; "mix"; "random"
        #Load traits
        with open("PositiveTraits.txt", 'r') as fin:
            self.positive_traits_list = [line.rstrip('\r\n') for line in fin]
        with open("NeutralTraits.txt", 'r') as fin:
            self.neutral_traits_list = [line.rstrip('\r\n') for line in fin]
        with open("NegativeTraits.txt", 'r') as fin:
            self.negative_traits_list = [line.rstrip('\r\n') for line in fin]
        # Randomize data - TODO
        if type_of_traits == 'mix':
             #Normalize to 1/3 by the minimum length list
            alen = [len(self.positive_traits_list), len(self.neutral_traits_list), len(self.negative_traits_list)]
            minlen = min(alen)
            mixM = []
            mixM.extend(self.positive_traits_list[1:minlen])
            mixM.extend(self.neutral_traits_list[1:minlen])
            mixM.extend(self.negative_traits_list[1:minlen])
            random.shuffle(mixM)
            #TODO: SAve traits
            trait_sample = random.sample(mixM, number)
        #TODO:
        if type_of_traits == 'positive':
            pass
        if type_of_traits == 'neutral':
            pass
        if type_of_traits == 'negative':
            pass
        if type_of_traits == 'random':
            #Positive or Neurtral or negative
            pass


        self.logger.info("Sample of traits: \n {:s}".format(', '.join([str(trait) for trait in trait_sample])))
        return trait_sample

    def generate_pygame_symbols(self, task):
        """Generate symbols/Graphs for pygame during mainloop depeending on tasks
        TODO:
            Test presenting a trait
        """
        self.logger.info("GENERATING PYGAME SYMBOLS")
        task_type = self.taskCfg[task]['type']
        if task_type=="traits":
            sample_traits = self.taskSave[task]["sample_traits"]
            # Create symbols for each trait - use font
            font = pygame.font.Font(None, self.fontheight)  #fonts text
            font_traits = [font.render(trait, True, self.color) for trait in sample_traits]
            # width and height of letters bounding box
            #Max font width and height of list of fonts
            width, height = max([fonts.get_size() for fonts in font_traits])
            # Combine 2 surfaces in 1 and store them
#            symbols = []
#            for symbol_trait in font_traits:
#                #surface to hold font -draw surface font on top other surface
#                surface = pygame.Surface((width, height), pygame.SRCALPHA)
#                surface.blit(symbol_trait, (0, height))
#                symbols.append(surface)

            #return symbols
            return font_traits

        if task_type=="stimulus":
            pass
        if task_type=="self_report":
            pass
        if task_type=="NFT":
            pass


    def present_tasks(self):
        """Present tasks."""
        task = self.tasks_to_present[self.taskCounter]
        task_type = self.taskCfg[task]['type']
        self.logger.info("Current Task : {:s} \n Task Type: {:s}".format(task, task_type))

        if task_type=="traits":
            self.screen.fill(self.backgroundColor)
            symbols = self.taskSave[task]["symbols"]
            font_to_blit = symbols[self.taskSave[task]["trait_counter"]]
            self.screen.blit(font_to_blit,
                             font_to_blit.get_rect(center=self.screen.get_rect().center))
            pygame.display.flip()
        if task_type=="stimulus":
            pass
        if task_type=="self_report":
            pass
        if task_type=="NFT":
            pass


if __name__ == "__main__":
#Testing the Feedback
   fb = TaskPresentation()
   fb.on_init()
   fb.on_play()

   #TESTING
#   fb.pre_mainloop()
#   fb.generate_pygame_symbols()
