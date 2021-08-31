#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Tue May  1 16:03:47 2018

FAQs:
    **feedbackapps folder**
    #WARNING Folder is added temporarely when you use the batch start_pyff
    #allways use the batch to not have problems

    **Vertical screen refresh**

    It can make a big difference whether or not you use fullscreen mode.  If
    you don't use fullscreen mode, hardware backends may not enable hardware
    surface and double buffering (for more information, see
    http://kevinlocke.name/inquiry/sdlblitspeed/sdlblitspeed.php).  If stimulus
    presentation is not time-locked with the vertical screen refresh rate,
    flickering artefacts may result. Time-locking should be automatically
    enabled in fullscreen mode. If it is not, check

        * if you got the latest graphics driver installed
        * if you got the latest DirectX version (on windows machines)

    You might also need to set your graphics driver to sync vertical refresh
    The standard driver is DirectX. If you work on a non-Windows machine, you
    need to change the video_driver variable
    (ftp://ptah.lnf.kth.se/pub/misc/sdl-env-vars gives a list of drivers).
    Double buffering is enabled by default to prevent tearing. Note that with
    doublebuf, hwsurface (hardware surface) is used instead of swsurface
    (software surface).  If you write your own drawing routines, be sure to use
    pygame.diplay.flip() command instead of pygame.display.update(), to have
    your stimuli rendered properly in double buffer mode.


@author: nm.costa
"""

from __future__ import division  #It creates int problems in older divisions

__version__="2.0"

#import sys
import os
import random
import time
#import os
import pygame


if __name__ == "__main__":
    from neuroprime.modules.pyff.src.FeedbackBase.PygameFeedback import PygameFeedback
    #NOTE: THIS IS USING neuroprime package module - when this is main - there is no forsiable problem usind with the neuroprime Environment, probably you can use it in python 2.7
else: #when is called from feedbackcontroller GUI
    from FeedbackBase.PygameFeedback import PygameFeedback
"""
feedbackcontroller GUI needs to be start from pyff environment (batch file) to work properly, while the neuroprime needs to start from the neuroprime encironment. It adds the necessary subfolders, also adds 'feedbackapps' folder as a repository for feedbacks (this is done in the batch start_pyff -use it!). However, it does not know it is located in the neuroprime folder.

"""



#from pylsl import StreamInfo, StreamOutlet, local_clock




import logging
logging_level=logging.DEBUG



class feedbackclass(PygameFeedback):
    """
    """
    #PATHS INIT
    currentDIR = os.path.dirname(os.path.abspath(__file__))  #os.path.dirname(sys.modules[__name__].__file__) # Get current dir - os.getcwd()-not good; dirname = os.path.dirname(os.path.abspath(__file__))
    maincodeDIR = os.path.dirname(os.path.dirname(os.path.dirname(currentDIR))) #get to neuroprime
    stimulusDIR = os.path.join(maincodeDIR, "stimulus")

    # 1st method - init called automatically when feedback is initialized - overwrite
    def init(self):
        #init method of the parent PygameFeedback class
        PygameFeedback.init(self)
        self.logger.setLevel(logging_level) #PARENT LOGGER RESET LEVEL

        #logger debug
        self.logger.debug("has_lsl : {}".format(self._has_lsl))
        self.logger.debug("lsl_outlet : {}".format(self._lsl_outlet))

        ###PARAMETERS PRESENTATION VARS###
        #CAPTION - Parent var
        self.logger.debug("#NOTE #WARNING: PARAMETERS PRESENTATION VARS - CAN'T BE CHANGED IN CHILD CLASS by pyff.set_variables, YOU NEED TO CHANGE THEM here ")

        #Window Caption
        self.caption = "Presentation"

        #COLOR SETTINGS
        self.BLACK = (  0,   0,   0)
        self.WHITE = (255, 255, 255)
        self.BLUE =  (  0,   0, 255)
        self.GREEN = (  0, 255,   0)
        self.RED =   (255,   0,   0)
        self.GREY =  ( 20,  20,  20)


        #DISPLAY SETTINGS
        self.fullscreen = True #Parent var
        if self.fullscreen:
            self.screenSize = [0, 0]  #use to let it figure out the maximum resolution
        else:
            self.screenSize = [1024, 768] #800×600, 960×720, 1024×768, 1280×960,
            self.screenPos = [200, 100]
            self.logger.warning("#BUG #SOLVED #screen: Surface Blited gets uncentered")

        self.marginratio = 1/20.
        #color of text and background
        self.color = self.WHITE
        self.backgroundColor = self.BLACK
        self.updatescreen = False  #update screen and background parameters for each graphical symbol

        #RANDOMIZE
        self.randomize = True  #enable all randomization
        self.random_seed = 1234  #Random Seed Initialize the random number generator


        self.stop_condition=False #use it if you want to set a timer to blow the program (see below)




        ###PROTOCOL PRESENTATION VARS###
        self.logger.debug("#NOTE #WARNING: PROTOCOL PRESENTATION VARS - CAN BE CHANGED IN CHILD CLASS by pyff.set_variables")

        #EXPERIMENT
        #show init instructions screen
        self.START_WAIT_FOR_KEY = True #
        #Markers -TRIGGER VALUES FOR THE PARALLELPORT (Numbers 1-250) or LSL (Strings)
        self.START_MARKER, self.END_MARKER = "START_EXP", "END_EXP"
        self.SHORTPAUSE_START, self.SHORTPAUSE_END = "SHORTPAUSE_START", "SHORTPAUSE_END"
        self.START_FLIP = "1sFLIP"
        self.FIRST_FLIP = False
        self.TEST_TICK = "TEST_TICK"
        #design
        self.PROTOCOL_TYPE = "TEST"
        self.PROTOCOL_DESIGN = "TEST" #
        #stimulus
        self.STIM_TIME = 10 #s
        self.logger.debug("#TODO text stimulus is implemented, but should be uniform like audio,video,image - use self.textstimulus only, if possible")
        mindfulness_text_instructions = "Durante a meditação, preste atenção à sensação física da respiração.\n\nSiga o movimento natural e espontâneo da respiração, não tente alterá-lo. \n\nApenas preste atenção a esse movimento. \n\nSe perceber que a sua atenção se desviou para outra coisa, traga-a de volta à sensação física da respiração. \n\nPor favor, mantenha seus olhos abertos."
        self.INIT_TEXT = mindfulness_text_instructions#"Presenting My Feedback Class. \nGreetings Muggles!." #INIT INSTRUCTIONS
        self.STIMULUS_TEXT = mindfulness_text_instructions #"\n\nPermaneça atento."
        self.END_TEXT = "YOU HAVE BEEN STIMULATED! \nI'LL BE BACK!"  #NOT NEEDED  -  TODO:Posso implementar
        self.audiostimulus = None  #file to use as audio stimulus - randomize and play - time the stimulus
        self.videostimulus = None
        self.imagestimulus = None
        self.audiostimulus_loop = 0 #-1 infinite loop; 0 no loop
        #likert scale keys
        self.key_target=["0","1","2", "3", "4", "5"]
        #Auditory Presentation feedback cues
        self.on_sound_cue_bell = True     # Auditory cues provided when bigning,ending, pause the feedback
        self.on_sound_cue_point = False #on/off sound cue_point

        #Neurofeedback bars
        self.feedback_bars=True
        self.show_inhibit_bands = False #activate/deactivate inhibit bands
        self.bar_position = "1" #"1","2","3" positions for rb+ib
        self.show_points = True
        self.point_symbol = None #this enables saving the symbol

        #Neurofeedback sounds
        self.feedback_sounds = True #activate feeback sounds



        ###STATE VARS - NEED RESET IN POST MAINLOOP###
        self.logger.debug("#NOTE #WARNING: STATE PRESENTATION VARS - THEY CANT be used outside this class")
        #pre_mainloop
        self.initSymbol = None
        self.endSymbol = None
        self.sound_cue_bell = None
        self.sound_cue_point = None

        self.sound_feedback_ch = 0 #ch for specific control
        self.sound_feedback_reward= None
        self.sound_feedback_inhibit= None
        self.on_play_reward=False
        self.on_play_inhibit=False
        self.audioStim_ob = None
        self.barsSurface = False  #initially you don't have surface
        #on_control_event
        self.eegTuple= {}
        #COUNTERS
        self.STIM_COUNTER = 0
        self.TICK_COUNTER = 0
        self.POINTS_COUNTER = 0
        #flags
        self.A_condition_flag = 0
        self.B_condition_flag = 0



        self.data_mockup = {'reward_bands': {'alpha': {'feedback_ch': 'Pz', 'feedback': 1.4156414080256676e-12, 'threshold_mean': 2.547767102262791e-12, 'feedback_units': 'V', 'threshold_ch': 'Pz', 'feedback_std': 2.527619872288862e-13, 'band': (8, 12), 'threshold': 1.4543761897095011e-12, 'threshold_std': 6.116296657479971e-14, 'feedback_mean': 1.4156414080256676e-12, 'threshold_units': 'V'}}, 'inhibit_bands': {'theta': {'feedback_ch': 'Pz', 'feedback': 5.150103398999269e-12, 'threshold_mean': 2.8166815588628684e-12, 'feedback_units': 'V', 'threshold_ch': 'Pz', 'feedback_std': 4.741406906378323e-12, 'band': (4, 8), 'threshold': 4.140409981618913e-12, 'threshold_std': 5.83478635248156e-13, 'feedback_mean': 5.150103398999269e-12, 'threshold_units': 'V'}, 'beta': {'feedback_ch': 'Pz', 'feedback': 5.421192460884977e-13, 'threshold_mean': 5.356556416499489e-13, 'feedback_units': 'V', 'threshold_ch': 'Pz', 'feedback_std': 3.0262489570356274e-13, 'band': (15, 35), 'threshold': 1.2252325338031387e-12, 'threshold_std': 2.99952047616384e-13, 'feedback_mean': 5.421192460884977e-13, 'threshold_units': 'V'}}}


        #self.send_lsl("PRESENTATION_INIT") #Mark the communication from wyrm
        self.logger.info("Feedback successfully loaded: " + self.caption)





    #--------
    #MAINLOOP
    #-------
    def pre_mainloop(self):
        self.logger.info("PRE_MAINLOOP")
        #LOG INPUT VARS for debug
        self.logger.debug("*************!!!SELF DICT START!!!*************")
        self.logger.debug(self.__dict__)
        self.logger.debug("*************!!!SELF DICT END!!!*************")

        #INIT PARENT
        PygameFeedback.pre_mainloop(self)  #init_pygame, init_graphics

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
        #CLOCKS (the cloks are in ms but the vars are in s)
        self.exp_clock = pygame.time.Clock() #ms
        self.tick_clock = pygame.time.Clock() #ms
        self.tick_time = 0
        start_tick = self.exp_clock.tick() / 1000. #s
        #send marker
        self.send_lsl(self.START_MARKER)
        #self.send_udp(self.START_MARKER)
        self.logger.debug("{} : {}".format(self.START_MARKER, start_tick))
        #INTRO Screen - The first GUI to appear - TODO: wait for keypress before starting
        self.present_symbols(self.initSymbol)


    def post_mainloop(self):
        self.logger.debug("POST MAINLOOP")
        # time since the last call
        stop_tick = self.exp_clock.tick() / 1000. #s
        elapsed_pre_post = stop_tick #s
        #send marker
        #self.send_udp(self.END_MARKER)
        self.send_lsl(self.END_MARKER)
        self.logger.info("{} : {}".format(self.END_MARKER, elapsed_pre_post))
        if self.on_sound_cue_bell:
            ch = self.sound_cue_bell.play(loops=1)  #channel playing
            while ch.get_busy():
                pygame.time.delay(100)
        self.logger.debug("Elapsed time from pygame.init(), in ms: {}".format(pygame.time.get_ticks()))

        self.loading_screen(text="\n\n\nTarefas concluidas. Muito obrigado.....")

        #RESET
        #stop audio playback
        pygame.mixer.stop()
        #Reset state vars - NEED RESET IN POST MAINLOOP
        self.init()





    # 4th method: play_tick method - called several time per second - from feedback start till it stops - depends on the FPS variable - default value of 30 - PygameFeedback Class
    def tick(self):
        #IMPORTANT: process any event that comes and run the number of frames per second default is self.FPS=30
        PygameFeedback.tick(self)

        #UPDATE TICK TIMES
        eticktime = self.tick_clock.tick()  #ms : elapsed milliseconds have passed since the previous call
        self.tick_time =  eticktime/ 1000. + self.tick_time #s
        self.logger.debug("Tick Time: {}".format(self.tick_time))
#        self.logger.debug("elapsed_tick_time: {}".format(self.elapsed))

        #IMPORTANT: PROCESS any on control event
        if self.eegTuple:
            if self.PROTOCOL_TYPE=="NFT":
                self.logger.debug("On Control Event")
                s = time.time() #s

                #FEEDBACK
                if self.PROTOCOL_DESIGN == "ABA":
                    if self.STIM_COUNTER >=(self.STIM_TIME*(1/3)) and self.STIM_COUNTER <(self.STIM_TIME*(2/3)):
                        condition="invert"
                        if self.feedback_bars:
                            symbol = self.generate_feedback_bars(self.eegTuple, condition=condition)
                            self.present_symbols(symbol)
                        if self.feedback_sounds: self.generate_feedback_sounds(self.eegTuple, condition=condition)
                        if self.B_condition_flag <1:
                            self.send_lsl("B_condition")
                            self.B_condition_flag =+1
                    else:
                        condition="normal"
                        if self.feedback_bars:
                            symbol = self.generate_feedback_bars(self.eegTuple, condition=condition)
                            self.present_symbols(symbol)
                        if self.feedback_sounds: self.generate_feedback_sounds(self.eegTuple, condition=condition)
                        if self.A_condition_flag <2:
                            self.send_lsl("A_condition")
                            self.A_condition_flag =+1
                else:
                    condition="normal"
                    #TODO: INIFFICIENT - GENERATION SHOULD be in the pre_mainloop - the bars should be only updated
                    if self.feedback_bars:
                        symbol = self.generate_feedback_bars(self.eegTuple, condition=condition)
                        self.present_symbols(symbol)
                    if self.feedback_sounds: self.generate_feedback_sounds(self.eegTuple, condition=condition)


                self.eegTuple = {} #reset tuple
                e = time.time()
                el = e-s
                self.logger.debug("delay_time_to_present: {}".format(el))

        #IMPORTANT: PROCESS stimulus
        if self.audiostimulus:
            #self.logger.debug("Audio Stimulus STIM_COUNTER: {}".format(self.STIM_COUNTER))
            oldcode=False
            if oldcode:
                if self.STIM_COUNTER == float(0):
                    self.logger.debug("Audio Stimulus: {}".format(self.audiostimulus))
                    self.present_symbols(self.audioStim_sb)
                    ch = self.audioStim_ob.play(loops=self.audiostimulus_loop)  #channel playing
    #                while ch.get_busy():
    #                    pygame.time.delay(100)
            else:
                 self.logger.debug("TICK Audio Stimulus : {}".format(self.audiostimulus))
                 self.present_symbols(self.audioStim_sb)
                 self.audioStim_ob.play(loops=self.audiostimulus_loop)  #channel playing
                 self.audiostimulus=None

        #IMPORTANT: PROCESS Likert scale
        if self.PROTOCOL_TYPE == "likert":
            self.wait_for_pygame_event()
            if self.keypressed:
                key = self.lastkey_unicode
                self.keypressed = False
                if key not in self.key_target:
                    self.logger.warning( "Wrong key pressed.")
                    return
                else:
                    self.logger.info("lastkey: {}".format(self.lastkey))
                    self.logger.info("lastkey_unicode: {}".format(self.lastkey_unicode))
                    self.send_lsl("keypress_{}".format(self.lastkey_unicode))
                    self.on_stop()

        #STOP CONDITION
        self.STIM_COUNTER = eticktime/ 1000. + self.STIM_COUNTER #s
        self.logger.debug("Audio Stimulus: {}".format(self.audiostimulus))
        self.logger.debug("stimCounter: {}".format(self.STIM_COUNTER)) #s
        self.logger.debug("elapsed: {}".format(self.elapsed))
        if self.STIM_COUNTER > self.STIM_TIME: #s
            self.on_stop()


    def pause_tick(self):
        pass

    def play_tick(self):
        pass

    #CONTROL EVENTS INTERACTION
    def on_control_event(self, data):
        self.logger.debug("\n>> ON_CONTROL_EVENT")
        # this one is equivalent to:
        # self.eegTuple = self._data
        self.eegTuple = data
        self.logger.info("\n>> data: {}".format(self.eegTuple))

    #INIT: additional pygame
    def init_pygame(self):
        PygameFeedback.init_pygame(self)  #INIT screen display and screen clock
        #ADDITIONAL INIT
        #1st.update screen with BACKGROUND CANVAS
        self.update_screen()
        #Draw envelop line - for litle canvas
        full_rect= pygame.Rect(0,0,self.presentation_rect.width,self.presentation_rect.height)
        pygame.draw.rect(self.presentation, self.WHITE, full_rect, 5)
        self.screen.blit(self.presentation, self.presentation_rect)
        #INIT mouse
        pygame.mouse.set_visible(False)
        #INIT AUDIO
        pygame.mixer.init(44100, -16, 2, 4096)  # init sound engine
        pygame.mixer.set_num_channels(20) #number of chs
        if self.START_WAIT_FOR_KEY:
            self.logger.debug("#BUG #SOLVED: Fullscreen mode does not work properly - some workarrounds - self.wait_for_key()")
            self.wait_for_key(txt="\n\nVamos comecar a experiencia")
        self.loading_screen()



    def init_graphics(self):
        """
        Called after init_pygame.

        """
        #IMPORTANT - INIT heavy stuff
        #update screen with BACKGROUND CANVAS
        self.update_screen()
        if self.START_WAIT_FOR_KEY:
            self.logger.debug("#BUG #SOLVED: Fullscreen mode does not work properly - some workarrounds - self.wait_for_key()")
            self.wait_for_key(txt=self.INIT_TEXT)
        self.loading_screen()

        self.logger.debug("#TODO put this in init_graphics() function")
        #plant the random seed in the beginning
        if self.random_seed:
            random.seed(self.random_seed)


        #INIT symbols graphics
        if self.PROTOCOL_TYPE=="likert":
            pass  #dont change INIT TEXT
        else:
            self.INIT_TEXT = self.STIMULUS_TEXT
        if self.INIT_TEXT:
            self.initSymbol = self.generate_text_symbols(self.INIT_TEXT)
        else:
            self.initSymbol = None
        if self.END_TEXT:
            self.endSymbol = self.generate_text_symbols(self.END_TEXT)
        else:
            self.endSymbol = None

        init_feedback = False
        if init_feedback:
             if self.feedback_bars:
                 self.initSymbol = self.generate_feedback_bars(self.data_mockup, condition="normal")
        #INIT Sounds
        self.sound_ch_n=pygame.mixer.get_num_channels() #generally 8 chs
        if self.on_sound_cue_bell:
            self.sound_cue_bell = pygame.mixer.Sound(os.path.join(self.stimulusDIR,"a_tone.ogg"))
        if self.on_sound_cue_point:
            self.sound_cue_point = pygame.mixer.Sound(os.path.join(self.stimulusDIR,"point.ogg"))
        if self.feedback_sounds:
            self.sound_feedback_ch = pygame.mixer.find_channel(True) #find free ch and use , True uses the longest
            self.sound_feedback_reward= pygame.mixer.Sound(os.path.join(self.stimulusDIR,"c1_ots_atmospad.ogg"))
            self.sound_feedback_inhibit= pygame.mixer.Sound(os.path.join(self.stimulusDIR,"c2_ots_atmospad.ogg"))
            self.sound_feedback_reward.set_volume(1)
            self.sound_feedback_inhibit.set_volume(1)
            self.sound_feedback_ch.set_volume(1)

        #INIT Stimulus
        self.logger.debug("INIT audiostimulus VAR: {}".format(self.audiostimulus))
        if self.audiostimulus:
            self.audioStim_ob = pygame.mixer.Sound(os.path.join(self.stimulusDIR, self.audiostimulus))
            self.logger.debug("INIT audio object: {}".format(self.audioStim_ob))
            self.audioStim_sb = None
#            if self.INIT_TEXT:
#                self.audioStim_sb = self.generate_text_symbols(self.INIT_TEXT)

        if self.videostimulus:
            pass
        if self.imagestimulus:
            pass

    def on_quit(self):
        self.loading_screen(text="\n\n\nTarefas concluidas. Muito obrigado.....")
        self.send_lsl('END')#Just to be sure to terminate
        time.sleep(10)

        PygameFeedback.on_quit(self)  #quit mainloop if not yet, and dont go to postmainloop(only stop goes to mainloop)
        pygame.mixer.quit()
        # parent-quiting pygame correctly
        PygameFeedback.post_mainloop(self)
        # Total number of items processed - Limited
        #logger information
        self.logger.warn("QUITTING FEEDBACKCLASS")




    """Specific"""
    #-----------------------
    #EVENT: Keyboard, mouse interaction
    #-----------------------
    def wait_for_key(self, blittext=True, txt="yah ma men"):
        """
        Similar to check key, but if no key was pressed, the
        function waits for key input
        """
        simple=False
        if blittext:
            if self.PROTOCOL_TYPE=="likert":
                text =  "\n\n\n!Carregue ENTER para responder!"
            else:
                self.logger.debug("#be careful about unicode, because I need unicode text - text that is sent from pyffcommunication is already unicode, and to concatenate you need to use unicode caracters")
                if isinstance(txt, unicode):
                    text = txt + unicode("\n\n\n!Carregue ENTER para começar!","utf-8")
                else:
                    text = txt + "\n\n\n!Carregue ENTER para começar!"
            if simple:
                font = pygame.font.Font(None, self.fontheight)
                textimage = font.render(text, True, self.color)
                textrect = textimage.get_rect(center=self.screenCenter)
            else:
                textimage = self.generate_text_symbols(text)
                textrect = textimage.get_rect(center=self.screenCenter)

            self.screen.blit(textimage, textrect)
            pygame.display.flip()
        #Important part to solve the fullscreen
        pygame.event.clear()            # Clear the old events
        while 1:
            pygame.time.delay(100)
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                #if event.type is (pygame.KEYDOWN):
                    return event.key


    def loading_screen(self,text="\n\n\n\n\n\n\n\n\nCarregando tarefa....."):
        #LOADING SCREEN
        textimage = self.generate_text_symbols(text)
        textrect = textimage.get_rect(center=self.screenCenter)
        self.screen.blit(textimage, textrect)
        pygame.display.flip()
        pygame.event.clear()            # Clear the old events







    #-----------------------
    #GENERATE: GRAPHIC SYMBOLS STIMULUS, AUDIO STIMULUS, VIDEO STIMULUS
    #-----------------------

    #GENERATE GRAPHICS
    def generate_text_symbols(self, text, text_rect=None, simple=False):
        self.logger.info("GENERATING PYGAME TEXT SYMBOLS")
        text_font = pygame.font.Font(None, self.fontheight)  #fonts text
        self.logger.debug("!!TEXT TYPE!! : {}".format(type(text)))
        text_string = text
        if not isinstance(text, unicode):
            text_string = unicode(text, "utf-8") #unicode string - needed to put accented characters in python 2.7
        #update screen
        if self.updatescreen:
            self.update_screen()

        #CREATE RECT BASED on BACKGROUND - if text_rect= None
        if not text_rect:
            margins_width =int(self.presentation_rect.width*self.marginratio)
            margins_height =int(self.presentation_rect.height*self.marginratio)
            text_rect = pygame.Rect((self.presentation_rect.left, self.presentation_rect.top, self.presentation_rect.width - margins_width,  self.presentation_rect.height - margins_height))
        self.logger.debug("text_rect: {}".format(text_rect))

        if simple:
            self.logger.warning("#BUG: Not working - test other way")
            text_image = text_font.render(text_string, True, self.color)
            symbol = pygame.Surface((text_rect.size)) #need () to work
            symbol.fill(self.backgroundColor)
            symbol_center =symbol.get_rect().center
            text_image_rect = text_image.get_rect(center=symbol_center)
            symbol.blit(text_image, text_image_rect)
        else:
            symbol = render_textrect(text_string, text_font, text_rect, self.color, self.backgroundColor, justification=1)
        # Create simple text symbol
        #font = pygame.font.Font(None, self.fontheight)  #fonts text
        #self.symbol = font.render(self.INIT_TEXT, True, self.color)

        return symbol

    def generate_feedback_bars(self, data, condition="normal"):
        """
        data example: {'reward_bands': {'alpha': {'feedback_ch': 'Pz', 'feedback': 1.4156414080256676e-12, 'threshold_mean': 2.547767102262791e-12, 'feedback_units': 'V', 'threshold_ch': 'Pz', 'feedback_std': 2.527619872288862e-13, 'band': (8, 12), 'threshold': 1.4543761897095011e-12, 'threshold_std': 6.116296657479971e-14, 'feedback_mean': 1.4156414080256676e-12, 'threshold_units': 'V'}}, 'inhibit_bands': {'theta': {'feedback_ch': 'Pz', 'feedback': 5.150103398999269e-12, 'threshold_mean': 2.8166815588628684e-12, 'feedback_units': 'V', 'threshold_ch': 'Pz', 'feedback_std': 4.741406906378323e-12, 'band': (4, 8), 'threshold': 4.140409981618913e-12, 'threshold_std': 5.83478635248156e-13, 'feedback_mean': 5.150103398999269e-12, 'threshold_units': 'V'}, 'beta': {'feedback_ch': 'Pz', 'feedback': 5.421192460884977e-13, 'threshold_mean': 5.356556416499489e-13, 'feedback_units': 'V', 'threshold_ch': 'Pz', 'feedback_std': 3.0262489570356274e-13, 'band': (15, 35), 'threshold': 1.2252325338031387e-12, 'threshold_std': 2.99952047616384e-13, 'feedback_mean': 5.421192460884977e-13, 'threshold_units': 'V'}}}
        """
        #update screen
        if self.updatescreen:
            self.update_screen()
        #TODO:GENERATE one first time than use the same, change only - create update function
        reward_bands = dictfinditem(data, "reward_bands")
        inhibit_bands = dictfinditem(data, "inhibit_bands")
        self.logger.debug("reward_bands:{}".format(reward_bands))

        #***SYMBOLS***
        reward_bar_symbols=[]
        inhibit_bar_symbols=[]
        add_point = [] #bolean
        if reward_bands:
            for band_key in reward_bands:
                try:
                    band_value = reward_bands.get(band_key, "not found" )
    #                band_range = band_value.get("band", "not found" )
    #                rest_mean = band_value.get("rest_mean", "rest_mean not found")
    #                rest_std = band_value.get("rest_std", "rest_std not found")
    #                feed_mean = band_value.get("feed_mean", "feed_mean not found")
    #                feed_std = band_value.get("feed_std", "feed_std not found")
                    #
                    threshold = band_value.get("threshold", "threshold not found")#rest_mean + 1*rest_std
                    updateValue = band_value.get("feedback", "feedback not found")#feed_mean
                    #POINT SYSTEM CHECK UP
                    if (condition=="normal" and updateValue>threshold) or (condition=="invert" and updateValue<threshold):
                        add_point.append(True)
                    else:
                        add_point.append(False)
                    #reward symbol
                    reward_bar_symbols.append(self.generate_bar_symbol(threshold, updateValue, threshold_factor=0.2, condition=condition, widthP=0.1, heightP=0.5, bartype="reward"))
                except Exception as e:
                    self.logger.error('Some error in reward bands: {}; band_key {}, not a band?'.format(e, band_key))

        if inhibit_bands and self.show_inhibit_bands:
            for band_key in inhibit_bands:
                try:
                    band_value = inhibit_bands.get(band_key, "not found" )
    #                band_range = band_value.get("band", "not found" )
    #                rest_mean = band_value.get("rest_mean", "rest_mean not found")
    #                rest_std = band_value.get("rest_std", "rest_std not found")
    #                feed_mean = band_value.get("feed_mean", "feed_mean not found")
    #                feed_std = band_value.get("feed_std", "feed_std not found")
                    #
                    threshold = band_value.get("threshold", "threshold not found")#rest_mean + 1*rest_std
                    updateValue = band_value.get("feedback", "feedback not found")#feed_mean
                    #POINT SYSTEM CHECK UP
                    if updateValue<threshold:
                        add_point.append(True)
                    else:
                        add_point.append(False)
                    #inhibit symbol
                    inhibit_bar_symbols.append(self.generate_bar_symbol(threshold, updateValue, threshold_factor=0.7, condition="normal", widthP=0.05, heightP=0.25, bartype="inhibit"))
                except Exception as e:
                    self.logger.error('Some error in inhibit bands: {}; band_key {}, not a band?'.format(e, band_key))


        #generate point symbol
        if self.POINTS_COUNTER == 0 and self.show_points:
            self.point_symbol=self.generate_points_symbol(str(self.POINTS_COUNTER))
            #Bonus point in the biggining - in this way it does not enter again in this if
            self.POINTS_COUNTER=1
        if all(add_point) and self.show_points:
            self.POINTS_COUNTER=self.POINTS_COUNTER+1
            self.point_symbol=self.generate_points_symbol(str(self.POINTS_COUNTER), widthP=0.2, heightP=0.1)

            #send marker before cue - this is considered an event
            self.send_lsl("point_"+str(self.POINTS_COUNTER))
            #play cue
            if self.on_sound_cue_point:
                ch = self.sound_cue_point.play()  #channel playing
#                while ch.get_busy():
#                    pygame.time.delay(100)
            #create textsymbol from counter


        #***SURFACES***
        #test multiple bars
        rb = reward_bar_symbols
        self.logger.debug("rb:{}".format(rb))
        rb_holder_surface = None
        if rb:
            #surface size
            width, height = rb[0].get_size() #there are all the same
            spacing = int((1/5)*width)
            rb_holder_surface = pygame.Surface((width*len(rb)+spacing*(len(rb) - 1) , height))
            self.logger.debug("holder_surface: {}".format(rb_holder_surface))
            for n, s in enumerate(rb):
                rb_holder_surface.blit(s, (n*(width+spacing),0))

        ib = inhibit_bar_symbols
        self.logger.debug("ib:{}".format(ib))
        ib_holder_surface = None
        if ib:
            #surface size
            width, height = ib[0].get_size() #there are all the same
            spacing = int((1/5)*width)
            ib_holder_surface = pygame.Surface((width*len(ib)+spacing*(len(ib) - 1) , height))
            self.logger.debug("holder_surface: {}".format(ib_holder_surface))
            #TODO:
            for n, s in enumerate(ib):
                ib_holder_surface.blit(s, (n*(width+spacing),0))


        #point_symbol is already a surface

        ##FINAL SURFACE
        final_holder_s = None
        #bar surface
        bar_holder_s = None
        if rb_holder_surface and ib_holder_surface:
            rb_width, rb_height = rb_holder_surface.get_size()
            ib_width, ib_height = ib_holder_surface.get_size()
            #create the bar holder
            margin = int(self.presentation_rect.width*self.marginratio)
            w=self.presentation_rect.width - margin
            h=rb_height
            bar_holder_s = pygame.Surface((w , h))
            bar_holder_s.fill(self.backgroundColor)
            #blit the surfaces
            half_w = int(w/2)
            center_of_half = int(half_w/2)
            half_h = int(h/2)
            #position
            if self.bar_position=="1":
                bar_holder_s.blit(rb_holder_surface, (half_w - int(rb_width/2)-int(rb_width/10), 0))
                bar_holder_s.blit(ib_holder_surface, (half_w + int(ib_width/2)+int(ib_width/10), half_h))
            elif self.bar_position=="2":
                bar_holder_s.blit(rb_holder_surface, (half_w - int(rb_width)-int(rb_width/10), 0))
                bar_holder_s.blit(ib_holder_surface, (half_w + int(ib_width)+int(ib_width/10), 0))
            elif self.bar_position=="3":
                bar_holder_s.blit(rb_holder_surface, (center_of_half - int(rb_width/2), 0))
                bar_holder_s.blit(ib_holder_surface, (half_w + center_of_half - int(ib_width/2), 0))

        elif rb_holder_surface:
            rb_width, rb_height = rb_holder_surface.get_size()
            #create the bar holder
            margin = int(self.presentation_rect.width*self.marginratio)
            w=self.presentation_rect.width - margin
            h=rb_height
            bar_holder_s = pygame.Surface((w , h))
            bar_holder_s.fill(self.backgroundColor)
            #blit the surfaces
            half_w = int(w/2)
            center_of_half = int(half_w/2)
            half_h = int(h/2)
            bar_holder_s.blit(rb_holder_surface, (half_w - int(rb_width/2), 0))

        else:
            self.logger.error("BARs Holder ERROR - continuing")

        #point_holder_s and final
        point_holder_s=None
        if bar_holder_s and self.point_symbol:
            p_width, p_height = self.point_symbol.get_size()
            b_width, b_heigth = bar_holder_s.get_size()
            #create the point holder
            w=b_width
            h=p_height
            point_holder_s = pygame.Surface((w , h))
            point_holder_s.fill(self.backgroundColor)
            #blit the surfaces
            half_w = int(w/2)
            center_of_half = int(half_w/2)
            half_h = int(h/2)
            #position
            point_holder_s.blit(self.point_symbol, (half_w - int(p_width/2), 0))

            #create tfinal holder
            w=b_width
            h=b_heigth+p_height
            spacing = int((1/20)*h)
            final_holder_s = pygame.Surface((w , h+spacing))
            final_holder_s.fill(self.backgroundColor)
            #blit the surfaces
            final_holder_s.blit(bar_holder_s, (0,0))
            final_holder_s.blit(point_holder_s, (0,b_heigth+spacing))
        else:
            final_holder_s = bar_holder_s

        return final_holder_s


    def generate_bar_symbol(self, threshold, updateValue, threshold_factor=0.5, condition="invert", widthP=0.04, heightP=0.1, bartype="reward"):
        #update screen parameters
        if self.updatescreen:
            self.update_screen()
        #colors to use
#        BLACK = self.BLACK
        GREY = self.GREY
        WHITE = self.WHITE
        BLUE =  self.BLUE
        GREEN = self.GREEN
        RED =   self.RED

        if threshold == 0:
            self.logger.error("#BUG: THRESHOLD EQUALS ZERO????, using threshold based in pudateValue - always ")
            threshold = updateValue*2


        self.logger.info("Generating PYGAME BARs")
        #COLORS
        bar_color = GREY
        envelop_color = WHITE
        s_envelop_color = envelop_color #save original envelop color
        if bartype=="reward":  #reward cue with colors
            if updateValue > threshold :
                bar_color = GREEN
                if threshold == 0:
                    threshold = int (updateValue/2)
            else:
                bar_color = RED
        else:
            if updateValue < threshold :
                bar_color = GREEN
            else:
                bar_color = RED
        if condition == "invert": #downregulation (bar shrinks, envelop bar augment) -
            if bar_color == GREEN: envelop_color = RED
            if bar_color == RED: envelop_color = GREEN
            bar_color = s_envelop_color
        #rect_surface display values (constant)
        rect_surface=(int(self.presentation_rect.width*(widthP)), int(self.presentation_rect.height*(heightP)))
        #bar surface holder
        bar_surface = pygame.Surface(rect_surface)
        b_width, b_height = bar_surface.get_size()
        self.logger.debug("bar_surface: {}".format(bar_surface))

        #bar Height conversion - px <-> value
        max_h_px = b_height
#        max_h_v = threshold * 3  #ONLY THAT CAN CHANGE
        thres_h_v = abs(threshold)
        thres_factor = threshold_factor
        thres_h_px = int(thres_factor*max_h_px) #int((thres_h_v* max_h_px)/max_h_v)  #= int((1/3.)*max_h_v)
        self.logger.debug("THRESHOLD:{}".format(thres_h_v))
        up_h_v = thres_h_v + (updateValue - threshold)  #updateValue
        self.logger.debug("UPDATE VALUE FEEDBACK - thres_h_v + (updateValue - threshold):{}".format(thres_h_v))
        up_h_px = int(up_h_v*(thres_h_px/float(thres_h_v))) #int( max_h_px*(up_h_v/max_h_v))
        if condition =="invert": #downregulation (bar shrinks, envelop bar rises)
#            max_h_v = (3/2)*thres_h_v
            thres_h_px = int((1-thres_factor) * max_h_px)
            up_h_px = int(up_h_v*(thres_h_px/float(thres_h_v))) #int(max_h_px*(up_h_v/max_h_v))
        if up_h_px<0: up_h_px=0
        if up_h_px>max_h_px: up_h_px=max_h_px
        #create bar rectangles
        self.logger.debug("color: {} ".format(bar_color))
        left, top = 0, 0
        self.logger.debug("left,top: {}, {}".format( left, top))
        full_rect = pygame.Rect(left,top,b_width,b_height)
        up_rect = pygame.Rect(left,top,b_width, up_h_px)
        self.logger.debug("rect: {}".format(up_rect))
        #draw bars into the surface
        envelop_bar = pygame.draw.rect(bar_surface, envelop_color, full_rect, 0)
        update_bar = pygame.draw.rect(bar_surface, bar_color, up_rect, 0)
        threshold_line = pygame.draw.line(bar_surface, BLUE, [left, thres_h_px], [b_width, thres_h_px], 2)
        envelop_line = pygame.draw.rect(bar_surface, s_envelop_color, full_rect, 1)
        self.logger.debug("bar_surface: {}".format(bar_surface))
        self.logger.debug("envelop_bar: {}".format(envelop_bar))
        self.logger.debug("update_bar: {}".format(update_bar))
        self.logger.debug("threshold_line: {}".format(threshold_line))
        self.logger.debug("envelop_line: {}".format(envelop_line))
        #rotate the surface - (0,0) px is in the left and top corner
        if condition == "invert":
            pass
        else:
            bar_surface = pygame.transform.rotate(bar_surface, -180)

        return bar_surface

    def generate_points_symbol(self, points_txt, widthP=0.2, heightP=0.1):
        #rect_surface display values (constant)
        left, top = 0, 0
        width, height=int(self.presentation_rect.width*(widthP)), int(self.presentation_rect.height*(heightP))
        self.logger.debug("i_width, i_height: {},{}".format(width, height))
        text_rect = pygame.Rect((left, top, width, height))

        #point symbol

        point_symbol = self.generate_text_symbols(points_txt, text_rect=text_rect, simple=True)
        p_width, p_height = point_symbol.get_size()
        self.logger.debug("p_width, p_height: {},{}".format(p_width, p_height))

        #point surface holder
        rect_surface=(int(width), int(height)) #NEED to be in brakets (,)
        point_surface = pygame.Surface(rect_surface)
        p_width, p_height = point_surface.get_size()
        self.logger.debug("point_surface: {}".format(point_surface))

        full_rect = pygame.Rect(left,top, width, height)
        envelop_color = self.WHITE
        point_surface.blit(point_symbol, (0,0) )
        envelop_line = pygame.draw.rect(point_surface, envelop_color, full_rect, 5)

        self.logger.debug("envelop_line: {}".format(envelop_line))


        return point_surface

    def generate_circle_symbol(self, threshold, updateValue):
        pass


    #GENERATE AUDIO - MOT USING IT
    def generate_feedback_sounds(self, data, condition="normal", method='simple'):
        """
        Generate and present feedback sounds

        method:
            simple, choose sound for on_target vs off_targe
        TODO: Change
        """
        #TODO:GENERATE one first time than use the same, change only - create update function
        reward_bands = dictfinditem(data, "reward_bands")
        inhibit_bands = dictfinditem(data, "inhibit_bands")
        self.logger.debug("reward_bands:{}".format(reward_bands))

        if method=='simple': #Check if subject is on_target and choose the feedback sound
            on_target = [] #bolean
            if reward_bands:
                for band_key in reward_bands:
                    try:
                        band_value = reward_bands.get(band_key, "not found" )
                        threshold = band_value.get("threshold", "threshold not found")#rest_mean + 1*rest_std
                        updateValue = band_value.get("feedback", "feedback not found")#feed_mean
                        #ON TARGET SYSTEM CHECK UP
                        if (condition=="normal" and updateValue>threshold) or (condition=="invert" and updateValue<threshold):
                            on_target.append(True)
                        else:
                            on_target.append(False)
                    except Exception as e:
                        self.logger.error('Some error in reward bands: {}; band_key {}, not a band?'.format(e, band_key))

            if inhibit_bands and self.show_inhibit_bands:
                for band_key in inhibit_bands:
                    try:
                        band_value = inhibit_bands.get(band_key, "not found" )
                        threshold = band_value.get("threshold", "threshold not found")#rest_mean + 1*rest_std
                        updateValue = band_value.get("feedback", "feedback not found")#feed_mean
                        #ON Target SYSTEM CHECK UP
                        if updateValue<threshold:
                            on_target.append(True)
                        else:
                            on_target.append(False)
                    except Exception as e:
                        self.logger.error('Some error in inhibit bands: {}; band_key {}, not a band?'.format(e, band_key))
            #present/play
            strategy=2
            fade_in_out=10 #ms
            if all(on_target) and not self.on_play_reward:
                self.on_play_reward=True
                self.on_play_inhibit=False


                if strategy==1: #BUG: STOPPED SOME TIMES DURNING NFT
                    self.sound_feedback_ch.fadeout(fade_in_out)#ms prevent "dread audio cliff of noise" #https://stackoverflow.com/questions/32435091/prevent-popping-at-end-of-sound-in-pygame-mixer
                    self.sound_feedback_ch.play(self.sound_feedback_reward, loops=-1, fade_ms=fade_in_out)  #channel playing

                if strategy==2:
                    self.sound_feedback_inhibit.fadeout(fade_in_out)
                    self.sound_feedback_reward.play(loops=-1, fade_ms=fade_in_out)

#                while ch.get_busy():
#                    pygame.time.delay(100)
            if not all(on_target) and not self.on_play_inhibit:
                self.on_play_reward=False
                self.on_play_inhibit=True

                if strategy==1: #BUG: STOPPED SOME TIMES DURNING NFT
                    self.sound_feedback_ch.fadeout(fade_in_out)#ms prevent "dread audio cliff of noise"
                    self.sound_feedback_ch.play(self.sound_feedback_inhibit, loops=-1, fade_ms=fade_in_out)

                if strategy==2:
                    self.sound_feedback_reward.fadeout(fade_in_out)
                    self.sound_feedback_inhibit.play(loops=-1, fade_ms=fade_in_out)
                #channel playing
#                while ch.get_busy():
#                    pygame.time.delay(100)



    #GENERATE VIDEO



    #-----------------------
    #UPDATE SCREEN AND BACGROUND RECT IF RESIZE:
    #-----------------------
    def update_screen(self):
        self.screenWidth, self.screenHeight = self.screen.get_rect().size
        self.screenCenter = self.screen.get_rect().center  #(self.screenWidth/2,self.screenHeight/2)
        self.screen_rect = self.screen.get_rect(center=self.screenCenter)
        self.logger.debug("screen_size: ({},{})".format(self.screenWidth,self.screenHeight))
        self.logger.debug("screenCenter: {}".format(self.screenCenter))
        self.logger.debug("screen_rect: {}".format(self.screen_rect ))
        #REINIT screensize to match  correct values
        self.screenSize = [self.screenWidth, self.screenHeight]
        #CANVAS SIZE
        self.logger.info("#BUG #SOLVED : SIZE - integer - pixels")
        self.canvasWidth,self.canvasHeight = int(self.screenSize[0]/1.5), int(self.screenSize[1]/1.5)
        self.logger.debug("canvasWidth,canvasHeight: {},{}".format(self.canvasWidth,self.canvasHeight ))
        #CREATE BACKGROUND CANVAS surface to work instead of the screen
        self.logger.warning("#BUG #TODO: cant use backgound blit only - could help performance")
        self.background = pygame.Surface( (self.canvasWidth, self.canvasHeight) )
        self.background.fill(self.backgroundColor)
        self.background_rect = self.background.get_rect(center=self.screenCenter )
        self.logger.debug("background surface: {}".format(self.background))
        # Background for whole screen (needs lots of time to paint, use self.background in most cases)
        self.all_background = pygame.Surface( (self.screenWidth,self.screenHeight) )
        self.all_background.fill(self.backgroundColor)
        self.all_background_rect = self.all_background.get_rect(center=self.screenCenter )
        #RECTANGLE to put presentation(x, y, w, h) -> Use the rectangle that you want
        self.presentation = self.background
        self.presentation_rect = self.background_rect
        #text Fontheight relative to presentation -imagine the number of lines that you want
        self.fontheight = int(self.background_rect.height/15.)
        #ONLY BLIT when necessary
#        self.screen.blit(self.all_background,self.all_background_rect)
#        pygame.display.flip()

    #-----------------------
    #PRESENT: GRAPHIC SYMBOLS STIMULUS, AUDIO STIMULUS, VIDEO STIMULUS
    #-----------------------
    def present_symbols(self, symbol):
        """Present the current symbols to the screen
            NOTE: USE only need to paint if somthing changes
        """
        if symbol:
            #symbol = self.symbol
            self.logger.debug("symbol: {}".format(symbol))
            symbol_rect = symbol.get_rect(center=self.screenCenter)
            self.screen.blit(symbol,symbol_rect)
            pygame.display.flip()  #Update the full display Surface to the screen
            #pygame.display.update()  #without this, fullscreen wont work
            if self.FIRST_FLIP:
                #self.send_lsl(self.START_FLIP)
                self.FIRST_FLIP = False
            #self.send_udp(self.START_TRIAL)
            #self.send_lsl(self.START_TRIAL)
            self.logger.info("Presenting...")






"""
additional functions outside class
"""


#Draw text with pygame
def show_message(self, text, box=False):
    """
    Uses pygame to puts text on the screen. Optionally, the size and color
    of the message can be provided. The text will be centered.
    If box is false, text will be a single line, otherwise it will be presented
    in a textbox
    """
    import pygame
    if not box:
        self.screen.blit(self.background, self.background_rect)
        font = pygame.font.Font(None, self.textsize)
        textimage = font.render(text, True, self.textcolor);
        textrect = textimage.get_rect(center=(self.screenWidth / 2, self.screenHeight / 2))
        self.screen.blit(textimage, textrect)
        pygame.display.flip()


class TextRectException:
    def __init__(self, message = None):
        self.message = message
    def __str__(self):
        return self.message

def render_textrect(string, font, rect, text_color, background_color, justification=0):
    """Returns a surface containing the passed text string, reformatted
    to fit within the given rect, word-wrapping as necessary. The text
    will be anti-aliased.

    Takes the following arguments:

    string - the text you wish to render. \n begins a new line.
    font - a Font object
    rect - a rectstyle giving the size of the surface requested.
    text_color - a three-byte tuple of the rgb value of the
                 text color. ex (0, 0, 0) = BLACK
    background_color - a three-byte tuple of the rgb value of the surface.
    justification - 0 (default) left-justified
                    1 horizontally centered
                    2 right-justified


    Returns the following values:

    Success - a surface object with the text rendered onto it.
    Failure - raises a TextRectException if the text won't fit onto the surface.
    """

    import pygame

    final_lines = []

    requested_lines = string.splitlines()

    # Create a series of lines that will fit on the provided
    # rectangle.

    for requested_line in requested_lines:
        if font.size(requested_line)[0] > rect.width:
            words = requested_line.split(' ')
            # if any of our words are too long to fit, return.
            for word in words:
                if font.size(word)[0] >= rect.width:
                    raise TextRectException, "The word " + word + " is too long to fit in the rect passed."
            # Start a new line
            accumulated_line = ""
            for word in words:
                test_line = accumulated_line + word + " "
                # Build the line while the words fit.
                if font.size(test_line)[0] < rect.width:
                    accumulated_line = test_line
                else:
                    final_lines.append(accumulated_line)
                    accumulated_line = word + " "
            final_lines.append(accumulated_line)
        else:
            final_lines.append(requested_line)

    # Let's try to write the text out on the surface.

    surface = pygame.Surface(rect.size)
    surface.fill(background_color)

    accumulated_height = 0
    for line in final_lines:
        if accumulated_height + font.size(line)[1] >= rect.height:
            raise TextRectException, "Once word-wrapped, the text string was too tall to fit in the rect."
        if line != "":
            tempsurface = font.render(line, 1, text_color)
            if justification == 0:
                surface.blit(tempsurface, (0, accumulated_height))
            elif justification == 1:
                surface.blit(tempsurface, ((rect.width - tempsurface.get_width()) / 2, accumulated_height))
            elif justification == 2:
                surface.blit(tempsurface, (rect.width - tempsurface.get_width(), accumulated_height))
            else:
                raise TextRectException, "Invalid justification argument: " + str(justification)
        accumulated_height += font.size(line)[1]

    return surface


"""
Dict Methods
"""
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
    fb = feedbackclass()
    try:
        fb.on_init()
        #patch logger
        logging.basicConfig(level=logging.DEBUG)#show console logger
        #if you want a log handler file (disabled=False) :
        #import neuroprime.src.functions.myfunctions as my
        #loggername=fb.logger.name
        #fb.logger = my.setlogfile(modulename=loggername, setlevel=logging.DEBUG, disabled=False)

        fb.on_play()
        fb.on_stop()
        time.sleep(10)
        fb.on_quit()
    except:
        fb.logger.error("ERROR FEEDBACK: {}".format(fb.caption))
        fb.on_stop()
        fb.on_stop()
        time.sleep(10)
        fb.on_quit()