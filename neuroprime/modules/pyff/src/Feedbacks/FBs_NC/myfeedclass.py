#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Tue May  1 16:03:47 2018

@author: nm.costa
"""

from __future__ import division  #It creates int problems in older divisions

import sys
# Get src path
sys.path.append("../../")  # appending src folder to the path
import random
import time
import os
import pygame
from FeedbackBase.PygameFeedback import PygameFeedback

from pylsl import StreamInfo, StreamOutlet, local_clock

#myfunctions
#import functions.audiofunctions
#import functions.videofunctions

import logging
#set handler for this file
logging.basicConfig(level=logging.INFO)


class myfeedclass(PygameFeedback):
    currentDir = os.path.dirname(sys.modules[__name__].__file__) # Get current dir

    # 1st method - init called automatically when feedback is initialized - overwrite
    def init(self):
        #init method of the parent PygameFeedback class
        PygameFeedback.init(self)
        #SET logger level
        self.logger.setLevel(logging.DEBUG)
        self.logger.disabled=False
        self.logger.info("has_lsl : {}".format(self._has_lsl))
        self.logger.info("lsl_outlet : {}".format(self._lsl_outlet))
        #caption
        self.caption = "My Feedback class Presentation"
        
        # Markers -TRIGGER VALUES FOR THE PARALLELPORT (Numbers 1-250) or LSL (Strings)
        self.START_MARKER, self.END_MARKER = "START_EXP", "END_EXP"
        self.SHORTPAUSE_START, self.SHORTPAUSE_END = "SHORTPAUSE_START", "SHORTPAUSE_END"
        self.START_FLIP = "1sFLIP"
        self.FIRST_FLIP = False
        self.TEST_TICK = "TEST_TICK"
        self.TICK_COUNTER = 0
        
        #Protocol GLOBALS
        self.PROTOCOL = "eyes_closed"
        self.INIT_TEXT = "Presenting My Feedback Class. \nGreetings Muggles! \n\nPremaneca atento."
        self.END_TEXT = "YOU HAVE BEEN STIMULATED! \nI'LL BE BACK!"  #NOT NEEDED  -  TODO:Posso implementar
        

        # Color of the symbols
        self.color = [0, 0, 0]
        self.backgroundColor = [127, 127, 127]
        self.BLACK = (  0,   0,   0)
        self.WHITE = (255, 255, 255)
        self.BLUE =  (  0,   0, 255)
        self.GREEN = (  0, 255,   0)
        self.RED =   (255,   0,   0)
        # text Fontheight in pixels
        self.fontheight = 50
        
        #fullscreen
        self.fullscreen = False
        
        
        #Experiment
        self.randomize = True  #enable all randomization
        self.random_seed = 1234  #Random Seed Initialize the random number generator
        self.eegTuple={}
        self.barsSurface = False  #initially you don't have surface
        self.stimulusDIR = self.currentDir
        
        #stimulus
        self.STIM_TIME = 30
        self.STIM_COUNTER = 0
        self.audioStimulus = []  #file to use as audio stimulus - randomize and play - time the stimulus
        self.videoStimulus = []
        self.imageStimulus = []
        #TODO:use other type of stimulus
#        self.trials = 1
#        self.pauseAfter = 10
#        self.pauseDuration = 3000
        
        #Auditory Presentation feedback cues
        self.auditoryCues = True       # Auditory cues provided when bigning,ending, pause the feedback
        #STOP CONDITION
        self.STOP_TIME = self.STIM_TIME*2 # IF SOMETHING GOES Wrong it explodes the app program
        self.logger.info("Feedback successfully loaded: " + self.caption)
        
    def pre_mainloop(self):
        #INIT PARENT - Screen Surface
        PygameFeedback.pre_mainloop(self)
        #INIT audio
        pygame.mixer.init()  # init sound engine
        #plant the random seed in the beginning
        if self.random_seed:
            random.seed(self.random_seed)
        #INIT SURFACES
        #Rectangle to put presentation(x, y, w, h) - todo: use some precentage
        self.center_screen = self.screen.get_rect().center
        self.screen_rect = self.screen.get_rect(center=self.center_screen)
        self.logger.debug("center_screen: {}".format(self.center_screen))
        self.logger.debug("screen_rect: {}".format(self.screen_rect ))

        #IMPORTANT - init heavy stuff 
        #Generate symbols
        if self.INIT_TEXT:
            self.initSymbol = self.generate_text_symbols(self.INIT_TEXT)
        else:
            self.initSymbol = None
        if self.END_TEXT:
            self.endSymbol = self.generate_text_symbols(self.END_TEXT)
        else:
            self.endSymbol = None

        test = False
        if test:
            data = {'reward_bands': {'SMR': {'rest_std': 2.0, 'feed_ch': 'Cz', 'rest_mean': 5.0, 'rest_ch': 'Cz', 'band': (12, 15), 'feed_std': 2.0042279458290193778, 'feed_mean': 5.0098307837495849888}}, 'inhibit_bands': {'eye_blink': {'rest_std': 0.0, 'feed_ch': 'Cz', 'rest_mean': 3.0, 'rest_ch': 'Cz', 'band': (3, 5), 'feed_std': 1.0043954480592344027, 'feed_mean': 4.0095263753887948836}, 'high_frequency_artifacts': {'rest_std': 3.0, 'feed_ch': 'Cz', 'rest_mean': 5.0, 'rest_ch': 'Cz', 'band': (45, 60), 'feed_std': 2.0070225635503785603, 'feed_mean': 6.013347527314522167}}}
            self.symbol = self.generate_feedback_bars(data)
        #INIT Sounds
        if self.auditoryCues:
            self.sound = pygame.mixer.Sound(os.path.join(self.stimulusDIR,"a_tone.wav"))
        #INIT Stimulus
        if self.audioStimulus:
            self.audioStim_ob = pygame.mixer.Sound(os.path.join(self.stimulusDIR, self.audioStimulus))
            self.audioStim_sb = None
#            if self.INIT_TEXT:
#                self.audioStim_sb = self.generate_text_symbols(self.INIT_TEXT)
            #
        if self.videoStimulus:
            pass
        if self.imageStimulus:
            pass
        
        #------
        #Start Mainloop
        #------
        
        ## TIME 
        
        #STOP CONDITION
        #a QUIT event is scheduled. This event will appear in Pygame's event queue after the given time and marks the regular end of the Feedback
        pygame.time.set_timer(pygame.QUIT, self.STOP_TIME * 1000)
        
        #CLOCKS
        self.exp_clock = pygame.time.Clock()
        self.tick_clock = pygame.time.Clock()
        self.tick_time = 0
        start_tick = self.exp_clock.tick() / 1000.
        #send marker
        self.send_lsl(self.START_MARKER)
        #self.send_udp(self.START_MARKER)
        self.logger.debug("{} : {}".format(self.START_MARKER, start_tick))
        
        #Greetings Screen - The first GUI to appear - TODO: wait for keypress before starting
        self.present_symbols(self.initSymbol)
    
    def post_mainloop(self):
        self.logger.debug("Quitting pygame.")
        # time since the last call
        stop_tick = self.exp_clock.tick() / 1000.
        elapsed_pre_post = stop_tick
        #send marker
        #self.send_udp(self.END_MARKER)
        self.send_lsl(self.END_MARKER)
        self.logger.debug("{} : {}".format(self.END_MARKER, elapsed_pre_post))
        if self.auditoryCues:
            ch = self.sound.play(loops=1)  #channel playing
            while ch.get_busy():
                pygame.time.delay(100)
        self.logger.debug("Elapsed time from pygame.init(), in ms: {}".format(pygame.time.get_ticks()))
        #QUITING
        pygame.mixer.quit()
        # parent-quiting pygame correctly
        PygameFeedback.post_mainloop(self)
        # Total number of items processed - Limited
        #logger information
        self.logger.warn("Quitting pygame.")



    # 4th method: play_tick method - called several time per second - from feedback start till it stops - depends on the FPS variable - default value of 30 - PygameFeedback Class
    def tick(self):
        #IMPORTANT: process any event that comes and run the number of frames per second default is self.FPS=30
        PygameFeedback.tick(self)
        #UPDATE TICK TIMES
        eticktime = self.tick_clock.tick()  #elapsed milliseconds have passed since the previous call
        self.tick_time =  eticktime/ 1000. + self.tick_time 
        self.logger.debug("Tick Time: {}".format(self.tick_time))
#        self.logger.debug("elapsed_tick_time: {}".format(self.elapsed))
        #IMPORTANT: PROCESS any on control event
        if self.eegTuple:
            self.logger.debug("On Control Event")
            s = time.time()
            #self.generate_text_symbols(str(dictfinditem(self.eegTuple["reward_bands"]["SMR"], "feed_mean")))
            #TODO: INIFFICIENT - GENERATION SHOULD be in the pre_mainloop - the bars should be only updated 
            symbol = self.generate_feedback_bars(self.eegTuple)
#                self.logger.debug("symbol : {}".format(self.symbol))
            self.present_symbols(symbol)
            self.eegTuple = {} #reset tuple
            e = time.time()
            el = e-s
            self.logger.debug("delay_time_to_present: {}".format(el))
            

        #IMPORTANT: PROCESS stimulus
        if self.audioStimulus:
            self.logger.debug("Audio Stimulus")
            if self.STIM_COUNTER == 0: 
                self.present_symbols(self.audioStim_sb)
                ch = self.audioStim_ob.play(loops=-1)  #channel playing
#                while ch.get_busy():
#                    pygame.time.delay(100)

        #STOP CONDITION
        self.STIM_COUNTER = eticktime/ 1000. + self.STIM_COUNTER
        self.logger.debug("stimCounter: {}".format(self.STIM_COUNTER))
        self.logger.debug("elapsed: {}".format(self.elapsed))
        if self.STIM_COUNTER > self.STIM_TIME:
            self.on_stop()


    def pause_tick(self):
        pass
    
    def play_tick(self):
        pass
    
    def on_control_event(self, data):
        self.logger.debug("ON_CONTROL_EVENT")
        # this one is equivalent to:
        # self.eegTuple = self._data
        self.eegTuple = data
        self.logger.debug("data: {}".format(self.eegTuple))
        

    """Specific"""
    
    def generate_text_symbols(self, text):
        self.logger.info("GENERATING PYGAME TEXT SYMBOLS")
        my_font = pygame.font.Font(None, self.fontheight)  #fonts text
        my_string = text
        #update screen rect
        self.screen_rect = self.screen.get_rect(center=self.center_screen)
        my_rect = pygame.Rect(self.screen_rect.left, self.screen_rect.top, int(self.screen_rect.width*(1/2)), int(self.screen_rect.height*(1/2)) )
        symbol = render_textrect(my_string, my_font, my_rect, self.color, self.backgroundColor, 1)
        # Create simple text symbol
        #font = pygame.font.Font(None, self.fontheight)  #fonts text
        #self.symbol = font.render(self.INIT_TEXT, True, self.color)
        return symbol

    def generate_feedback_bars(self, data):
        """
        data example: {'reward_bands': {'SMR': {'rest_std': 0.0, 'feed_ch': 'Cz', 'rest_mean': 0.0, 'rest_ch': 'Cz', 'band': (12, 15), 'feed_std': 0.0042279458290193778, 'feed_mean': 0.0098307837495849888}}, 'inhibit_bands': {'eye_blink': {'rest_std': 0.0, 'feed_ch': 'Cz', 'rest_mean': 0.0, 'rest_ch': 'Cz', 'band': (3, 5), 'feed_std': 0.0043954480592344027, 'feed_mean': 0.0095263753887948836}, 'high_frequency_artifacts': {'rest_std': 0.0, 'feed_ch': 'Cz', 'rest_mean': 0.0, 'rest_ch': 'Cz', 'band': (45, 60), 'feed_std': 0.0070225635503785603, 'feed_mean': 0.013347527314522167}}}
        """
        #update
        self.screen_rect = self.screen.get_rect(center=self.center_screen)
        #TODO:GENERATE one first time than use the same, change only - create update function
        reward_bands = dictfinditem(data, "reward_bands")
        inhibit_bands = dictfinditem(data, "inhibit_bands")
        self.logger.debug("reward_bands:{}".format(reward_bands))
        reward_bar_symbols=[]
        inhibit_bar_symbols=[]
        if reward_bands:
            for band_key in reward_bands:
                band_value = reward_bands.get(band_key, "not found" )
                band_range = band_value.get("band", "not found" )
                rest_mean = band_value.get("rest_mean", "rest_mean not found")
                rest_std = band_value.get("rest_std", "rest_std not found")
                feed_mean = band_value.get("feed_mean", "feed_mean not found")
                feed_std = band_value.get("feed_std", "feed_std not found")
                threshold = rest_mean + 1*rest_std
                updateValue = feed_mean
                reward_bar_symbols.append(self.generate_bar_symbol(threshold, updateValue, widthP=0.1, heightP=0.5, reward=True))

        if inhibit_bands:
            for band_key in inhibit_bands:
                band_value = inhibit_bands.get(band_key, "not found" )
                band_range = band_value.get("band", "not found" )
                rest_mean = band_value.get("rest_mean", "rest_mean not found")
                rest_std = band_value.get("rest_std", "rest_std not found")
                feed_mean = band_value.get("feed_mean", "feed_mean not found")
                feed_std = band_value.get("feed_std", "feed_std not found")
                threshold = rest_mean + 1*rest_std
                updateValue = feed_mean
                inhibit_bar_symbols.append(self.generate_bar_symbol(threshold, updateValue, widthP=0.04, heightP=0.1, reward=False))
        
        #test multiple bars
        rb = reward_bar_symbols
        self.logger.debug("rb:{}".format(rb))
        rb_holder_surface = None
        if rb:
            #surface size
            width, height = rb[0].get_size() #there are all the same
            spacing = (1/5)*width
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
            spacing = (1/5)*width
            ib_holder_surface = pygame.Surface((width*len(ib)+spacing*(len(ib) - 1) , height))
            self.logger.debug("holder_surface: {}".format(ib_holder_surface))
            #TODO:
            for n, s in enumerate(ib):
                ib_holder_surface.blit(s, (n*(width+spacing),0))
                
        
        bar_holder_s = None
        if rb_holder_surface and ib_holder_surface:
            rb_width, rb_height = rb_holder_surface.get_size()
            ib_width, ib_height = ib_holder_surface.get_size()
            #create the final holder
            w=self.screen_rect.width
            h=rb_height
            bar_holder_s = pygame.Surface((w , h))
            bar_holder_s.fill(self.backgroundColor)
            #blit the surfaces
            half_w = int(w/2)
            center_of_half = int(half_w/2)
            bar_holder_s.blit(rb_holder_surface, (center_of_half - int(rb_width/2), 0))
            bar_holder_s.blit(ib_holder_surface, (half_w + center_of_half - int(ib_width/2), 0))
        elif rb_holder_surface:
            bar_holder_s = rb_holder_surface
        else:
            self.logger.error("BARs Holder ERROR")


        return bar_holder_s


    def generate_bar_symbol(self, threshold, updateValue, widthP=0.04, heightP=0.1, reward=True ):
        #update screen rect
        self.screen_rect = self.screen.get_rect(center=self.center_screen)
        BLACK = self.BLACK
        WHITE = self.WHITE
        BLUE =  self.BLUE
        GREEN = self.GREEN
        RED =   self.RED
        
        if threshold == 0:
            self.logger.error("THRESHOLD EQUALS ZERO????, using threshold based in pudateValue - always ")
            threshold = updateValue*2
            

        self.logger.info("Generating PYGAME BARs")
        if reward:
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
        #rect_surface
        rect_surface=(int(self.screen_rect.width*(widthP)), int(self.screen_rect.height*(heightP)))
        #bar surface holder
        bar_surface = pygame.Surface(rect_surface)
        b_width, b_height = bar_surface.get_size()
        self.logger.debug("bar_surface: {}".format(bar_surface))
        #bar values
        max_h = b_height
        max_h_v = threshold * 3
        thres_h = (1/3) * max_h
        thres_v = threshold
        up_v = updateValue 
        up_h = max_h*(up_v/max_h_v)
        #create bar rectangles
#        Surface = bar_surface
#        color = bar_color
        self.logger.debug("color: {} ".format(bar_color))
        left, top = 0, 0
        self.logger.debug("left,top: {}, {}".format( left, top))
        full_rect= pygame.Rect(left,top,b_width,b_height)
        up_rect = pygame.Rect(left,top,b_width, up_h)
        self.logger.debug("rect: {}".format(up_rect))
        #draw bars into the surface
        envelop_bar = pygame.draw.rect(bar_surface, WHITE, full_rect, 0)
        update_bar = pygame.draw.rect(bar_surface, bar_color, up_rect, 0)
        threshold_line = pygame.draw.line(bar_surface, BLACK, [left, thres_h], [b_width, thres_h], 2)
        envelop_line = pygame.draw.rect(bar_surface, BLACK, full_rect, 1)
        self.logger.debug("bar_surface: {}".format(bar_surface))
        #rotate the surface
        bar_surface = pygame.transform.rotate(bar_surface, -180)

        return bar_surface

    def generate_circle_symbol(self, threshold, updateValue):
        pass

    def init_audio_stimulus(self, audioStimulus):
        audioObjects = []
        for s_file in audioStimulus:
            sound_obj = pygame.mixer.Sound(os.path.join(self.stimulusDIR,s_file))
            audioObjects.append(sound_obj)
        #randomize
        if self.randomize:
            random.shuffle(audioObjects)

        return audioObjects


    def present_symbols(self, symbol):
        """Present the current symbols to the screen."""
        if symbol:
            self.screen.fill(self.backgroundColor)
            #symbol = self.symbol
            self.logger.debug("symbol: {}".format(symbol))
            self.screen.blit(symbol,
                             symbol.get_rect(center=self.screen.get_rect().center))
            pygame.display.flip()  #Update the full display Surface to the screen
            if self.FIRST_FLIP:
                #self.send_lsl(self.START_FLIP)
                self.FIRST_FLIP = False
            #self.send_udp(self.START_TRIAL)
            #self.send_lsl(self.START_TRIAL)
            self.logger.info("Presenting...")

"""
additional functions
"""

#Draw text with pygame
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
    fb = myfeedclass()
    try:
        fb.on_init()
        fb.on_play()
        fb.on_stop()
    except:
        fb.logger.error("ERROR FEEDBACK: {}".format(fb.caption))
        fb.on_stop()