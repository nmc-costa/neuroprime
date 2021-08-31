# -*- coding: utf-8 -*-

"""
Created on Sun May 13 20:32:34 2018

SCRIPT:
    INIT Presentation and Acquisition

@author: nm.costa
"""

from __future__ import print_function, division


__version__="3.0"

import time
import datetime
import os
import sys
import numpy as np


#signal acquisition
import neuroprime.src.signal_acquisition.mushu_patch as patch



#signal processing
import wyrm
from wyrm import io #dont remove - wyrm when first time imported forgets to include subpackages


#multiprocessing to open new python process in mac os
import multiprocessing



# My functions
import neuroprime.src.utils.myfunctions as my

# My classes

#LOGGING
import logging
logging_level=logging.INFO
##script main logger
logger = logging.getLogger(__name__)
logger.setLevel(logging_level)

##multiprocess logger
multiprocessing.log_to_stderr()
logger = multiprocessing.get_logger()
logger.setLevel(logging.DEBUG)



#coping objects
import copy




class initbciclass(object):

    def __init__(self, simulate=False, replayamp=False, filetoreplay=None, realtimereplay=True, inlet_sleep_time=float(0.0005), max_inlet_samples=1024, inlet_block_time=None, filelogger=False, logfolder='logfolder'):
        #Class logger
        loggername=self.__class__.__name__
        self.logger = logging.getLogger(loggername)
        self.logger.setLevel(logging_level)
        ##file_logger
        if filelogger: 
            logpath=my.get_test_folder(foldername=logfolder)
            my.sethandlerfile(modulename=loggername, setlevel=logging.INFO, filepath=logpath)
        #my.all_logs_enabler(disable=True) #disable all other logs

        #INLET defs
        self.max_inlet_samples = max_inlet_samples ##MAX INLET SAMPLES THAT WILL BE PULLED #1024 is pylsl pull_chunk standard of max samples pulled
        self.inlet_block_time= inlet_block_time #s - directly implement block buffer in the amp.get_data() function of mushu
        self.inlet_sleep_time = inlet_sleep_time #s - sleep time between pull chunks

        #Replay data
        self.replayamp=replayamp
        self.filetoreplay=filetoreplay
        self.realtimereplay=realtimereplay
        self.replaytime=None

        #SIMULATE AMPLIFIER in other process
        self.simulate = simulate
        if self.simulate:
            import platform
            if platform.system()=='Windows':
                self.logger.debug("#BUG windows multiprocessing error")
                self.logger.debug("#BUG #TODO : Windows multiprocessing has some problems -  use simulate=False,  go to functions -> simulateActichamp and run the scripts for simulation")
                raise RuntimeError("Windows Not Working the simulate")
            self.p_data = multiprocessing.Process(target=self.init_actichamp_data_simulation)  # can also pass parameters
            self.p_marker = multiprocessing.Process(target=self.init_actichamp_marker_simulation)
            self.p_data.start()  # start process
            self.p_marker.start()  # start process

        #INIT VARS
        self.init()




    def init(self):
        """
        Global Constants - INIT all class Variables and constants

        Change vars on child class
        """
        self.logger.info("***init***")
        #self.logger.debug("#TODO CHANGE initbciclass to initbciclass")
        self.logger.debug("#TODO implement solution to init_acquisition in all files")

        ###INIT PROTOCOL SAVING VARS###
        self.SAVE = False #True or False -
        self.SAVE_TASK=True # True | False - Save method:  False, saving all the session in one file(WORKING - but has time restrictions, test performance); True, save each task in one file
        self.FOLDER_DATA = '/Users/nm.costa/Desktop/testData'  # folder to save data: None=Find foler; Windows: 'E:/BCI_NC/data' #self.logger.debug("#BUG #SOLVED : Use foward slash in windows, because backward slash is not working")
        self.GROUP = 'EG'  #EG or CG
        self.TASK = '' #
        self.SUBJECT_NR = 1
        self.SESSION_NR = 1
        self.BLOCK_NR = 1
        self.TASK_NR = 1
        self.TOTAL_BLOCK_NR=1
        self.subtask = "" #it should be changed in each protocol function


        ###INIT PRESENTATION VARS###

        #PARAMETERS PRESENTATION VARS (PYFF)
        self.logger.debug("#LIMITATION -  loopfeedbackclass inits pygame outside pre_mainloop, therefore main display parameters cant be updated in this class, like caption, fullscreen - to change go directly to feedbackclass")

        self.presType = "pyff"
        self.PYFF_HOST = '127.0.0.1' # Windows needs address 127.0.0.1 #the PC that has the self.pyff running, or None if is in the same PC
        self.FEEDBACK_APP = "loopfeedbackclass"
        self.PYFF_MARKER_STREAM = 'PyffMarkerStream'  #defined in pyff FEEDBACK.py class
#random seed
        self.random_seed = None  #None, random based on clock; 1234, to obtain same values to test
        #RESTART PRESENTATION and ACQUISITION - NOT NEEDED ANYMORE - DEPRECATED - MUSHU PATCH
        self.restart = False

        #PROTOCOL PRESENTATION VARS
        self.logger.debug("#NOTE : PROTOCOL PRESENTATION VARS - CAN AND SHOULD BE CHANGED IN CHILD CLASS")
        self.START_WAIT_FOR_KEY = True
        self.PROTOCOL_TYPE = "TEST"
        self.PROTOCOL_DESIGN = "TEST"
        self.START_MARKER = "START"
        self.END_MARKER = "END"
        self.show_inhibit_bands= False
        self.feedback_bars=True
        self.feedback_sounds=True
        #stimulus
        self.INIT_TEXT = "initbciclass is greeting you!"#presentation init screen - instructions screen
        self.STIM_TIME = 10
        self.STIMULUS_TEXT = "\n\nPermaneca atento e tente relaxar (respire)"
        self.audiostimulus = None  #file to use as audio stimulus - randomize and play - time the stimulus
        self.videostimulus = None
        self.imagestimulus = None

        #PROTOCOL FOR EYES()
        self.protocol_eyes="eyes_open" #"eyes_open" | "eyes_closed"

        ###INIT PARAMETER ACQUISITION VARS###
        self.logger.debug("#NOTE #WARNING : PARAMETERS ACQUISITION VARS - !!CAN NOT!! BE CHANGED IN CHILD CLASS- they need to remain the same over the cycles - if not, they give errors when using multiple child class")

        #Channels Names Montage (WARNING : SERVER NEEDS TO CONCORD WITH THIS)
        self.acticap_10_20_new_design_uol = ['Fp1', 'Fz', 'F3', 'F7', 'FT9', 'FC5', 'FC1', 'C3','T7','TP9', 'CP5', 'CP1', 'Pz', 'P3', 'P7', 'O1', 'Oz', 'O2', 'P4', 'P8', 'TP10', 'CP6','CP2', 'Cz','C4', 'T8', 'FT10', 'FC6','FC2', 'F4', 'F8','Fp2']
        self.ch_names = self.acticap_10_20_new_design_uol
        self.amp_ref_channels =['Cz'] #[] no-ref montage; ['Fp1', 'Fp2'] - server ref chs, add them to the data

        #Configure AMP connection vars
        self.stream_server='lsl' #lsl ; pycorder_rda
        self.stream_type='EEG' #type of strem; depends on stream outled def
        self.lsl_amp_name= 'BrainVision RDA'#'BrainVision RDA'#'Actichamp-0'##None: asks user for input; lsl AMP Stream name: 'Actichamp-0' or 'BrainVision RDA'
        self.chunksize= 50#samples #Server ChunkSize Samples amp driver - actichamp lsl app 10 samples; rda app is 50 samples, => samplerate=1000hz  50ms
        self.lsl_marker_name= self.PYFF_MARKER_STREAM #None: asks user for input; lsl MARKER stream name : self.PYFF_MARKER_STREAM or 'BrainVision RDA Markers'
        self.lsl_save_buffers=True #save data buffers to backup the data
        self.inlet_max_buffer=360 #s default 360s; NOTE: smaller buffers were giving problems - also, signal acquisition always reconfigures in start(), therefore having a big buffer in real time should be no problem

        self.blocksize_samples_replay = self.chunksize  #INLET samples same as lslamp get data(1024) or min corresponding to chunksize
        self.logger.debug("CHUNK SIZE - The number of samples per chunk emitted by the driver -- a small value will lead to lower overall latency but causes more CPU load")
        self.logger.debug("chunksize trades off latency vs. network overhead - good range for the default value is between 5-30 milliseconds - resulting in an average latency that is between 2.5-15 ms and an update rate between 200-30 Hz")
        self.logger.debug("BLOCKSIZE_SAMPLES Replay are the number of samples that get_data() will return")










    def init_io(self):
        """
        init all input/output mehtods
        """
        self.logger.info("***init_io***")
        start_time = time.time()

        #filename
        # SAVING -CREATES FOLDER and PATHS to FOLDER
        self.update_file_path()

        end_time = time.time()
        elapsed_time = end_time-start_time
        self.logger.info("***init_io***ELAPSED TIME: {}".format(elapsed_time))


    def update_file_path(self):
        """
        USE everytime you need to recreate filepath
        """
        self.EEG_PATH, self.FILENAME_EEG_DATA, self.FILENAME_EEG_PATH = my.create_file_path(SAVE=self.SAVE, FOLDER_DATA=self.FOLDER_DATA, GROUP=self.GROUP, TASK=self.TASK, SUBJECT_NR=self.SUBJECT_NR, SESSION_NR=self.SESSION_NR, BLOCK_NR=self.BLOCK_NR)
        self.logger.info("CURRENT FILE PATH: {}".format(self.FILENAME_EEG_PATH))

    def serialize(self, objectname=None):
        self.logger.info("***serialize***")
        start_time = time.time()

        #serialize class object - save init vars
        if self.SAVE:
            try:
                classname=self.__class__.__name__
                if objectname:
                    subtask=objectname
                else:
                    if hasattr(self, 'subtask'):
                        if self.subtask:
                            subtask=self.subtask
                        else:
                            subtask=classname
                    else:
                        subtask=classname
                my.serialize_object(self, self.EEG_PATH, self.FILENAME_EEG_DATA+"_"+subtask+"_vars", method='json')
            except Exception as e:
                self.logger.error("Class object vars not serialized and saved, errors: {}; {}".format(e, copy.error.message))
                self.logger.debug("#BUG #SOLVED - thread.lock objects like multiprocessing or logger cant be serialized - so, be careful, remove logger or processes")
                pass


        end_time = time.time()
        elapsed_time = end_time-start_time
        self.logger.info("***serialize***ELAPSED TIME: {}".format(elapsed_time))






    def init_presentation(self, presType="pyff"):
        self.logger.info("***init_presentation***")
        start_time = time.time()


        if presType=="pyff":
            #TEST if self.pyff is ACTIVE and connected by sensing feedback pyffmarker
            TIMEOUT = 120 #s
            self.watchdog=my.Timer()
            self.watchdog.reset()
            self.pyff_marker_inlet = None
            while self.watchdog.sec() < TIMEOUT and not self.pyff_marker_inlet:
                self.logger.warning("\n>> Pyff Waiting for connection...")
                #S.Presentation INIT
                self.pyff = wyrm.io.PyffComm(self.PYFF_HOST) #Create pyff communication
                self.pyff.send_init(self.FEEDBACK_APP)
                time.sleep(5)
                #Sniff pyff connection
                self.test_pyff_connection()
                if self.pyff_marker_inlet: break
                self.pyff.quit()
            else:
                self.logger.error("\n>> Pyff CONNECTION ERROR: Timeout ocurred: {}s!".format(self.watchdog.sec()))
                self.pyff.quit()
                raise
            #set init vars - first init
            self.set_pyff_vars()

        if presType == "psychopy":
            pass #TODO: IMPLEMENT

        self.logger.debug("PRESENTATION INITIATED")
        end_time = time.time()
        elapsed_time = end_time-start_time
        self.logger.info("***init_presentation***ELAPSED TIME: {}".format(elapsed_time))

    def test_pyff_connection(self):
        #TEST if self.pyff is ACTIVE by sensing feedback pyffmarker and return the marker inlet
        self.pyff_marker_inlet = my.return_stream_inlet(self.PYFF_MARKER_STREAM, streamtype='Markers', wait_time=3)

    def set_pyff_vars(self):
        """
        USE this function to set protocol pyff vars instead of  self.pyff.set_variables
        WHY standardize the protocol vars that can be changed in the feedback app
        """
        self.logger.info("***set_pyff_vars***")
        start_time = time.time()

        init_vars_dict = {'PROTOCOL_TYPE': self.PROTOCOL_TYPE, 'PROTOCOL_DESIGN': self.PROTOCOL_DESIGN, 'START_MARKER' : self.START_MARKER, 'END_MARKER': self.END_MARKER, 'INIT_TEXT': self.INIT_TEXT, 'STIM_TIME' : self.STIM_TIME,'STIMULUS_TEXT': self.STIMULUS_TEXT, "audiostimulus": self.audiostimulus, "videostimulus": self.videostimulus, "imagestimulus": self.imagestimulus, "START_WAIT_FOR_KEY": self.START_WAIT_FOR_KEY , "show_inhibit_bands": self.show_inhibit_bands, "feedback_bars": self.feedback_bars, "feedback_sounds": self.feedback_sounds}

        self.logger.debug("!!init_vars_dict!!: {}".format(str(init_vars_dict)))

        #SET
        #time.sleep(3)#Wait for pygame to stop -
        self.pyff.set_variables(init_vars_dict)
        #time.sleep(3) # - wait before play

        end_time = time.time()
        elapsed_time = end_time-start_time
        self.logger.info("***set_pyff_vars***ELAPSED TIME: {}".format(elapsed_time))




        self.logger.debug("#BUG #SOLVED: SET VARIABLES CORRECTLY in PYFF- Need to wait some time for the pygame quits properly in pyff - maybe needs self.pyff.stop() to impose stop() on PYFF")
        self.logger.debug("#NOTE #WARNING pyff vars need to allways be set a new - all of them - however in the childs of this class you cant change certaint variables")






    def init_acquisition(self):
        self.logger.info("***init_acquisition***")
        start_time = time.time()

        if self.replayamp:
            #ask for file to replay
            filepath=self.filetoreplay
            filenamepath, filetype =os.path.splitext(filepath)
            if not self.filetoreplay:
                filepath=my.get_file_path()
            if not os.path.exists(filepath):
                self.logger.error("filepath wrong:{}")
                raise
            #righ now only working for .meta files
            if not filetype==".meta":
                self.logger.error("Beware, can only use .meta files for now")
                raise
            cnt = wyrm.io.load_mushu_data(filepath)
            timeaxis=-2
            self.replaytime = int(np.rint( (cnt.axes[timeaxis][-1]-cnt.axes[timeaxis][0])*(10**-3) )) #s

            #INIT AMP
            self.amp = patch.libmushu.get_amp('replayamp')

            if self.realtimereplay:
                #data: format
                self.amp.configure(data=cnt.data, marker=cnt.markers, channels=cnt.axes[-1].tolist(), fs=cnt.fs, realtime=True, blocksize_samples=self.blocksize_samples_replay)
            else:
                self.amp.configure(data=cnt.data, marker=cnt.markers, channels=cnt.axes[-1].tolist(), fs=cnt.fs, realtime=False, blocksize_samples=self.blocksize_samples_replay)

            self.logger.debug("#NOTE: Cant use markers from lsl stream in replay")

        else:
            #S.Acq INIT->Configure
            #1.INIT
            self.amp = patch.libmushu.get_amp('lslamp')
            #Coniguration connection
            self.amp.configure(stream_type=self.stream_type, stream_server=self.stream_server, lsl_amp_name=self.lsl_amp_name, lsl_marker_name=self.lsl_marker_name, block_time=self.inlet_block_time, get_data_sleeptime=self.inlet_sleep_time, lsl_save_buffers=self.lsl_save_buffers, inlet_max_buffer=self.inlet_max_buffer, amp_ref_channels=self.amp_ref_channels ) #timeout forever till find the proper streams
            self.logger.debug('Changing some configuration variables')
            self.amp.amp.max_samples=self.max_inlet_samples #Number of samples pulled from stream

            try:
                self.logger.info("Channels From Amplifier Mushu: {}".format(self.amp.get_channels()))
            except:
                self.logger.warning("#BUG : libmushu if not updated from github has troubles in windows - see readme")
                pass

            #CONVENTION: SIMPLIFY CH MANAGEMENT - server amp chs need to be a subset of defined montage ch_names
            amp_chs=self.amp.get_channels()
            if not set(self.amp_ref_channels).issubset(self.ch_names) and set(self.amp_ref_channels).issubset(amp_chs):
                raise AssertionError("\n>> Server AMP REfs Problem:  \n>> self.amp_ref_channels: {} \n>> self.ch_names: {}; \n>> self.amp.amp.channels {}; \n>> See if amp ref is really the one you want!".format(self.amp_ref_channels,self.ch_names, amp_chs))
            #CONVENTION: ch_names=amp_chs   # to simplify nftalgorythm
            if set(amp_chs).issubset(self.ch_names):
                self.ch_names=amp_chs#update to new names that are inside the initial self.ch_names
            else:
                raise AssertionError("\n>> Server AMP CHs different from initbciclass ch_names: \n>> self.ch_names: {}; \n>> self.amp.amp.channels {}; \n>> Change ch_names to match what is comming from the stream".format(self.ch_names, amp_chs))




        #START AMP
        #only when saving full session
        if not self.SAVE_TASK:
            self.update_file_path()
            if self.FILENAME_EEG_PATH:
                self.amp.start(filename=self.FILENAME_EEG_PATH)
            else:
                self.amp.start()
            assert self.amp.received_samples == 0



        self.logger.debug("AQUISITION INITIATED")
        end_time = time.time()
        elapsed_time = end_time-start_time
        self.logger.info("***init_acquisition***ELAPSED TIME: {}".format(elapsed_time))







    def init_actichamp_data_simulation(self):
        from neuroprime.src.utils.simulate import sendDataAchamp

    def init_actichamp_marker_simulation(self):
        from neuroprime.src.utils.simulate import sendMarkerAchamp


    def on_init(self):
        """
        INIT METHODS - used for giving possibility to change init vars -
        """
        self.logger.info("\n>> ***on_init***")
        try:
            #Start input output method after changing parameters if you want
            self.init_io()
            #Start PRESENTATION
            self.init_presentation(presType=self.presType)
            #start Acquistion
            self.init_acquisition()
        except Exception as e:
            self.on_quit()
            raise RuntimeError("\n>> BCI on_init had problems, possible bug: {}".format(e))
        self.logger.info('\n>> BCI METHODS INITIATED!')

    def restart_init(self, oldcode=False):
        self.logger.info("***restart_init***")
        #self.on_init() #not needed init_io
        #Start PRESENTATION
        self.init_presentation(presType=self.presType)
        #start Acquistion
        self.init_acquisition()
        self.logger.info('BCI METHODS RESTARTED')



    def on_stop(self, ampstop=True, pyffstop=True):
        self.logger.info("***on_stop***")
        #1.stop pyff - the first to be initiated
        try:
            if pyffstop:
                if self.pyff:
                    self.pyff.stop() #Normally pyff app goes to on_stop first, -needed for on_quit
        except Exception as e:
            self.logger.error("on_stop Pyff STOP error: {}".format(e))
            pass
        #2.stop amp - init after pyff
        try:
            if ampstop:
                if self.amp:
                    self.logger.debug("#BUG dont use try: and except to stop amp that is in another try and stop - and stoping amp has priority to stop pyff - also dont use time.sleep in stop")
                    self.amp.stop()
        except Exception as e:
            self.logger.error("on_stop AMP STOP error: {}".format(e))
            pass

        self.logger.warning("ON_STOP BCI STATE: ")
        try:
            self.logger.warning(">> BLOCK_NR: {}".format(self.BLOCK_NR))
            self.logger.warning(">> TASK_NR: {}".format(self.TASK_NR))
            self.logger.warning(">> GROUP: {}".format(self.GROUP))
            self.logger.warning(">> SUBJECT_NR: {}".format(self.SUBJECT_NR))
            self.logger.warning(">> SESSION_NR: {}".format(self.SESSION_NR))
        except Exception as e:
            self.logger.warning("No State available, error: {}".format(e))





    def on_quit(self):
        """
        only use on_quit at the end of everything
        """
        self.logger.info("***on_quit***")
        #1st stop
        try:
            self.on_stop()
        except:
            pass
        #Presentation
        try:
            if self.pyff:
                time.sleep(5)
                self.pyff.quit()
        except Exception as e:
            self.logger.error("on_quit Pyff QUIT error: {}".format(e))
            pass
        #acquisition - libmushu
        try:
            self.logger.debug("#BUG - for some reason stopping the lslamp and starting again breaks get_data - using multiple streams and also in only one stream - seems related to time.sleep outside - I thought that removing tcp server ended the problem, but it did not - solution ?? - 1. maybe remove self.amp.stop() from libmushu ampdecorator.on_stop(); 2. the problem only occurs because of on_nft_bci ")
            if self.amp:
                self.amp.amp.stop()
        except Exception as e:
            self.logger.error("on_quit AMP QUIT error: {}".format(e))
            pass

        #simulate
        if self.simulate:
            self.p_data.terminate() # terminate process
            self.p_marker.terminate() # terminate process
            print ('PROCESS TERMINATED')
            sys.stdout.flush()




    def on_loop(self, restart=False, method="simple", serialize=False):
        """
        ON LOOP

        Loop of the task: start, get data and close
        """
        ###START
        try:
            #RESTART PRESENTATION and ACQUISITION
            if restart:
                self.restart_init()

            ##AMP MUSHU
            #UPDATE/RESET
            if self.SAVE_TASK:
                self.update_file_path() #update filename with BLOCK_NR
                #validate and start streams
                if self.FILENAME_EEG_PATH:
                    self.amp.start(self.FILENAME_EEG_PATH+'_'+self.subtask) #adding subtask name

                else:
                    self.amp.start() #block untill driver start is ready
                assert self.amp.received_samples == 0
            else:
                time.sleep(3) #Wait before set new vars -Necessary

            ##PYFF
            #set init vars
            self.set_pyff_vars()


            #play loop
            #*******LOOP TYPE****
            if method=="simple": self.simple_loop()
            if method=="closed_loop": self.closed_loop()
            #***************

            if not self.SAVE_TASK:
                self.on_stop(ampstop=False)
            else:
                self.on_stop(ampstop=True) #Needed to stop file saving and closing streams for each task loop
        except Exception as e:
            self.logger.error("\n>> ON_LOOP ERROR: {}".format(e))
            #handle the closing if something started
            self.on_quit()
            raise
        #serialize vars
        if serialize and self.SAVE: self.serialize()

    def simple_loop(self, play_presentation=True):
        start_time = time.time()
        self.logger.info("start_time: {}".format(start_time))

        #STREAM NAMES
        amp_name="AMP PID"
        marker_name="MARKER"
        try:
            if self.amp.amp.lsl_amp_name:
                amp_name=self.amp.amp.lsl_amp_name
            if self.amp.amp.lsl_marker_name:
                marker_name=self.amp.amp.lsl_marker_name
        except:
            pass


        #PYFF (NOTE: It needs to be here so you can use it when you please)
        if play_presentation:
            #play presentation - show task
            self.pyff.play()

        ##GET/SAVE DATA
        STOP = False
        timer = my.Timer(autoreset=True)
        fs = self.amp.get_sampling_frequency()
        server_buffer_time=self.chunksize/ fs #server mininimum buffer time
        next_sec = 1
        current_len_samples=0
        while not STOP:
            loop_start_time=time.time()
            #GET DATA
            samples, markers = self.amp.get_data()  #PROBLEMS running it two times in a row
            if markers: #LOG RIGHT AWAY THE MARKERS
                for m in markers:
                    t0_data=self.amp.amp.duration #ms
                    self.logger.info("\n>> {} : {}s, {}".format(marker_name,(t0_data + m[0])/1000, m[1]))#absolute timestamp s


            #STOP
            if self.END_MARKER in [m for _, m in markers]:
                STOP = True
                break
            #STOP with replayamp
            if self.replayamp:
                for _, m in markers:
                    if m.find("END")>-1:
                        break
                elapsed_time = time.time() - start_time
                if elapsed_time>self.STIM_TIME:
                    STOP = True
                    break
            #if only has 'END' in the name - for Multiprocessing and for presentation debug
            if self.END_MARKER=='END':
                end='END'
                if any([m.upper().find(end)>-1 for _, m in markers]):
                    STOP = True
                    break

            #SLEEP
            timer.sleep_atleast(server_buffer_time) #sleep at least the time that the chunk in the server needs to buffer

            #LOG INFO
            try:
                if self.amp.received_samples > 0:
                    sample_duration = self.amp.received_samples / fs #s
                    loop_elapsed = time.time() - loop_start_time
                    loop_duration = time.time() - start_time
                    if len(samples)>0:
                        current_len_samples=len(samples)
                    if sample_duration > next_sec:
                        datetime_duration = datetime.timedelta(seconds=int(sample_duration))
                        self.logger.info("\n>> {} {} DATETIME: {} \n>> Received Samples Duration: {} s\n>> Loop Duration: {} s \n>> Loop Elapsed time: {} s \n>> Samples received : {} \n>> get_data chunk average : {} \n>> Sample Rate: {}".format(amp_name, self.amp.amp.pid, datetime_duration, sample_duration, loop_duration, loop_elapsed, self.amp.received_samples, current_len_samples, fs))
                        next_sec += 1
            except:
                pass


        #LOG last time after loop breaks
        try:
            if self.amp.received_samples > 0:
                datetime_duration = datetime.timedelta(seconds=int(sample_duration))
                self.logger.info("\n>> {} {} DATETIME: {} \n>> Received Samples Duration: {} s\n>> Loop Duration: {} s \n>> Loop Elapsed time: {} s \n>> Samples_received : {} \n>> get_data chunk average : {} \n>> Sample Rate: {}".format(amp_name, self.amp.amp.pid, datetime_duration, sample_duration, loop_duration, loop_elapsed, self.amp.received_samples, current_len_samples, fs))
        except:
            pass
        #LOG elapsed time
        elapsed_time = time.time() - start_time
        self.logger.info("ELAPSED TIME :{}".format(elapsed_time))


    def closed_loop():
        """
        Close loop function

        Add in child class if you want to use - see nftclass for example
        """
        pass

    def on_play_check(self, **kwargs):
        """
        on_play with check

        Check for raised errors in on_play and pause BCI

        NOTE:**kwargs to pack and unpack for different class
        """
        while True:
            try:
                self.on_play(**kwargs) # Mushu path raises error if timeout
                return
            except (Exception and KeyboardInterrupt) as e:
                op=input('??? Exception Ocurred: {} ??? \n\n>> Do you want to restart task: enter 1 \n>> If Not, close the program: enter 2\n>>  '.format(e))
                op=str(op)
                if op=='1':
                    #STOP CLASS - Acquisition and Presentation reset
                    if not self.SAVE_TASK:
                        self.on_stop(ampstop=False)#dont stop amp
                    else:
                        self.on_stop(ampstop=True) #Needed to stop file saving and closing streams for each task loop
                    continue

                else:
                    raise RuntimeError("User choose option {} , close the program!".format(op))


    def on_play(self):
        """
        Play session Methods

        Change this function to suit your needs in child class
        WARNING: always add self.update_file_path()
        """
        ###UPDATE/RESET
        self.update_file_path()#WARNING: NECESSARY
        self.start_time = time.time()


        #RE-INIT some VARS if wanted
        #presentation init screen
        self.INIT_TEXT = "\nVamos iniciar initbciclass.py!"
        self.STIM_TIME = 10 #s
        #TEST 1
        self.subtask='test_1'
        self.STIMULUS_TEXT ="\n\n\n\n\n\n\n\n\n\n"+self.subtask+'\n Duration: '+str(self.STIM_TIME)
        self.START_MARKER = "START_"+self.subtask
        self.END_MARKER = "END_"+self.subtask
        self.on_loop()
        #TEST 2
        self.subtask='test_2'
        self.STIMULUS_TEXT ="\n\n\n\n\n\n\n\n\n\n"+self.subtask+'\n Duration: '+str(self.STIM_TIME)
        self.START_MARKER = "START_"+self.subtask
        self.END_MARKER = "END_"+self.subtask
        self.on_loop()


"""MULTIPROCESSING AMP"""

class get_amp_subprocess(object):
    """
    Simple subprocess amp class
        Start amp in subprocess with simple_loop() just to save data

    sources:
        #https://stackoverflow.com/questions/2629680/deciding-among-subprocess-multiprocessing-and-thread-in-python
        #https://pymotw.com/2/multiprocessing/basics.html

    TODO:
        #SOLVED Multirpocessing on Windows - https://stackoverflow.com/questions/52763746/python-multiprocessing-issue-in-windows-and-spyder

    WARNING:
        On windows you need to run the code in cmd line - IDEs may not work
        Don't forget to clean up before calling the class:
            #clean up any old process
            import multiprocessing
            for p in multiprocessing.active_children():
                print("TERMINATING PROCESS: ", p.name, p.pid)
                p.terminate()#force termination
                p.join()#wait to terminate
    """

    def __init__(self, filepath=None, save_task=True, END_MARKER='END', process_name="CHILD_AMP" ):
        self.process_name=process_name
        self.save_task=save_task
        self.END_MARKER=END_MARKER
        if filepath:
            filedir, filename, ext = my.parse_path_list(filepath)
            self.filename=os.path.join(filedir,filename+'_'+process_name)
        else:
            self.filename=None

    def configure(self, stream_type='HRV', stream_server='lsl', lsl_amp_name='HRV', lsl_marker_name="PyffMarkerStream", lsl_save_buffers=True, inlet_max_buffer=360):
        #Warning: Inlet Max Buffer needs to be big,I had 3s and didn't work, some samples were not saved

        #Sharing state between processes¶ - Method: shared memory map Value
        self.run_loop = multiprocessing.Value('i', 0) #start False
        self.loop_started= multiprocessing.Value('i', 0) #start False
        self.kill= multiprocessing.Value('i', 0) #start False


        #start child process
        self.p = multiprocessing.Process(name=self.process_name, target=self.worker, args=(self.run_loop, self.loop_started, self.kill, self.save_task, self.filename, self.END_MARKER, stream_type, stream_server, lsl_amp_name, lsl_marker_name, lsl_save_buffers, inlet_max_buffer))
        self.p.daemon=True #To exit the main process even if the child process p didn't finished - less constrictions between processes?
        self.p.start() #start process



    def worker(self, run_loop, loop_started, kill, save_task=True, filename=None, END_MARKER='END', stream_type='HRV', stream_server='lsl', lsl_amp_name='HRV', lsl_marker_name="PyffMarkerStream", lsl_save_buffers=True, inlet_max_buffer=360):
        p = multiprocessing.current_process()
        print ('Starting:', p.name, p.pid)

        #Init amp
        amp = patch.libmushu.get_amp('lslamp')
        #config amp
        amp.configure(stream_type=stream_type, stream_server=stream_server, lsl_amp_name=lsl_amp_name, lsl_marker_name=lsl_marker_name, lsl_save_buffers=lsl_save_buffers, inlet_max_buffer=inlet_max_buffer)

        #init loop from initbciclass() - just to have the same simple_loop
        bci = initbciclass()
        bci.amp=amp
        bci.END_MARKER = END_MARKER

        #Start before main loop
        if not save_task: bci.amp.start(filename=filename)
        #loop to stay open until forcibly terminate
        tasknumber=0
        while True:
            if save_task and run_loop.value:
                tasknumber+=1
                fn=filename
                if fn:
                    fn=fn+'_'+str(tasknumber)
                #loop -you can use other custom loop
                try:
                    bci.amp.start(filename=fn)
                    loop_started.value=1 #true
                    bci.simple_loop(play_presentation=False)#get_data simple loop -ends by the stop marker
                    bci.amp.stop()#save files
                    #stop
                    run_loop.value=not run_loop.value#change state
                    loop_started.value=0 #false
                except Exception as e:
                    bci.amp.stop()#save files
                    loop_started.value=0
                    print("\n>> Multiprocessing Worker Problem: {}".format(e))
                    raise RuntimeError("\n>> Multiprocessing Worker Problem: {}".format(e))

            if not save_task: bci.simple_loop(play_presentation=False) #always getting data and not waitin for run_loop.value

            if kill.value:
                if not save_task: bci.amp.stop()
                print("\n>> KILLED WORKER.")
                kill.value=not kill.value
                break
        try:
            bci.amp.stop()
        except:
            pass





    def start(self):
        #if save by task wait
        if self.save_task:
            #Sharing state between processes¶ - Method: shared memory map Value
            self.run_loop.value = 1 #Start child loop
            #block main process till child process starts loop
            while True:
                if self.loop_started.value: break

        self.starttime = time.time()
        print ('\nSUBPROCESS:', self.p.name, self.p.pid)
        print('>>START - loop started at {} seconds'.format(self.starttime))


    def stop(self):
        #if save by task wait
        if self.save_task:
            #block main process till child finish the child loop
            while True:
                if not self.run_loop.value: break
        print ('\nSUBPROCESS:', self.p.name, self.p.pid)
        print('>>STOP - that took {} seconds'.format(time.time() - self.starttime))

    def terminate_loop(self):
        #force loop to terminate
        self.run_loop.value = 0 #don't do the loop and stop amp
        print ('\nSUBPROCESS:', self.p.name, self.p.pid)
        print('>>TERMINATE_LOOP - that took {} seconds'.format(time.time() - self.starttime))

    def on_quit(self):
        ##QUIT
        self.run_loop.value = 0
        self.kill.value=1 #terminate
        while True:
            if not self.kill.value: break #after kill value goes down
        #Child process still alive because of worker loop
        if self.p.is_alive():
            self.p.terminate() #force termination
            self.p.join() #wait to terminate
            print("Process ALive: ",self.p.is_alive())
        print ('\nSUBPROCESS:', self.p.name, self.p.pid)
        print('>>ON_QUIT - that took {} seconds'.format(time.time() - self.starttime))


if __name__ == "__main__":
    #replayamp
    replayamp=False
    #replay sample data
    filetoreplay=my.get_filetoreplay() #filepath

    #save folder dir
    test_folder_path=my.get_test_folder() #folderpath

    #1.Start Class
    bci = initbciclass(simulate=False, replayamp=replayamp, filetoreplay=filetoreplay, inlet_block_time=None)
    try:
        #REINIT and change VArs
        bci.SAVE = False
        bci.SAVE_TASK = False

        #Start dialogue
        info={'savefolder': test_folder_path, 'subject':1, 'session':1, 'exp_version': 1,
              'group': ['TEST','EG', 'CG', 'PILOT'], "technician": "Nuno Costa"}
        title='test experiment'
        fixed=['exp_version']
        newinfo=my.gui_dialogue(info=info,title=title,fixed=fixed)
        bci.FOLDER_DATA = newinfo['savefolder']
        bci.GROUP = newinfo['group']  #EG or CG
        bci.SUBJECT_NR = newinfo['subject']
        bci.SESSION_NR = newinfo['session']

        #INIT presentation and acquisition methods
        bci.on_init()
        bci.on_play()
        bci.on_quit()
    except Exception as e:
        bci.logger.error("\n>> SOMETHING WENT WRONG: {}".format(e))
        bci.on_quit()