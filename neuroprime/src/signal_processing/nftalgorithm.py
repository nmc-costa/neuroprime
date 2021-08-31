# -*- coding: utf-8 -*-
"""
Created on Sun Jun 17 16:29:25 2018

NOTE:
    Wyrm: Faster (no advanced functions)
    MNE: Slower (advanced functions) - specially creating raw array takes time


1.Load continuous data:
        1.1Choose Channels to process:
        1.2.Choose Data interval
    2.Preprocessing:
        2.1Filter:
        2.2Subsample:
    3.Processing:
        3.1 Remove noisy Channels:No
        3.2 AVERAGE reference:No
        3.3 ICA: No
        3.4 Segmentation Epochs: 1s window (for analysis) / 5 = 200 ms
        3.5 Remove baseline:No
        3.6 Artifact detection/rejection:Yes
        3.7 PSD:
            3.7.1 FFT 0.98Hz resolution
            3.7.2 10% hanning window with variance correction
        3.8 Alpha Peak detection
        3.9 BANDS
            Delta Band: 0.2-4 hz (standard)
            Theta Band: IAF–6 Hz to IAF–3 Hz(standard: 4-7Hz)?
            Alpha Band: Lower Alpha = IAF‐2 Hz to IAF; upper Alpha = IAF to IAF+2 Hz (standard:8-12)?
            SMR BAND: individual = IAF+2Hz to IAF  + 4hz (standard 12– 15 Hz for SMR NF protocol)?
            Beta Band: 21–35 Hz (standard)
        3.10 Thresholds
            SMR baseline threshold: mean of SMR power during rest state of 1s window of Cz;
            theta and beta baseline threshold: mean + 1 SD of theta or beta power during rest state of Fz
            Upper Alpha Threshold: mean  Lower alpha of Pz;
            Lower Alpha Threshold:  mean power + 1 SD during rest state of Pz
ONLINE NEUROFEEDBACK
Same pipeline but the segmentation of data  is done online in a circular ringbuffer of one second and update data in 200 ms.


#TODO:
    Blockbuffer and ringbuffer they don't need to be updated. It only makes sense to reset processing class after the loop. reset_class can be done by init_methods() again or using initial_state class


@author: nm.costa
"""
from __future__ import division

__version__="3.3+dev"
#import math
import copy
import numpy as np
import mne
import math
import os
#import sys
import time
#MY FUNCTIONS
import neuroprime #to get neuroprime_dir = os.path.abspath(neuroprime.__file__)
from  neuroprime.src.signal_processing.eegpipeline import eegpipeline as pipelineobject  # Best way if you want to use other pipline
import  neuroprime.src.signal_processing.eegfunctions as eeg
import  neuroprime.src.utils.myfunctions as my

#LOGGING
import logging
#Module logger
logging_level=logging.INFO
logger = logging.getLogger(__name__)
logger.setLevel(logging_level)
logger.info('Logger started.')

#Debbuging
#import pdb

class nftalgorithm(pipelineobject):

    def __init__(self, amp_fs=1000,  amp_chunksize=10, amp_chs=None, blocksize=12, blocksize_max=1024, window_time=1024, feature="SMR", ch_names=my.cap_chs_design, calculate_iaf=False, serialize_vars=None):
        pipelineobject.__init__(self)
        #ASSERT DATA PROPERTIES
        self.amp_fs=amp_fs #sampling freq
        self.ch_names=ch_names  #Ch names montage sequence
        self.amp_chs=amp_chs  #Chs that come from stream amplifier - It can be numeric or a subset of the ch_names - by convention use only subset
        if not self.amp_chs: self.amp_chs=self.ch_names
        assert self.amp_chs == self.ch_names #CONVENTION (simple to manage) : server amp chs = ch_names montage
        self.n_channels = len(self.amp_chs)

        self.serialize_vars =serialize_vars#serialize or not the data

        self.window_time=window_time#ms window to process data array





        #BUFFERS
        #blockbuffer - New data array - Save the incoming data, and processing data is of blocksize -
        #Assert: necessary for subsample online: assert blocksize based on subsample (decimation problem), decimation - Factor by which to downsample the data  - depends on the blocksize and sample - #TODO
        self.chunksize = amp_chunksize  #samples NOTE: see Actichamp APP for actual chunksize: for 1000Hz is 10samples(minimum), rda with 1000Hz in pycorder sends 50 samples
        self.blocksize=blocksize #samples = blocksec*amp_fs
        self.blocksize_max=blocksize_max #samples: the max block of input data if directly pushed from lsl is 1024 samples
        assert self.blocksize<=self.blocksize_max
        #assert self.chunksize<=self.blocksize

        #ringbuffer - Processing Window data array - (delay_samples+new_samples)append small chunks in each iteration of online loop and use this delaysamples plus the newsamples to classify
        #Assert:ringtime>=blocksize
        self.ringtime=self.window_time #ms
        self.blocktime=(self.blocksize/self.amp_fs) * 1000
        assert self.blocktime<=self.ringtime



        #ASSERT PROTOCOL
        #Chs to extract featueres
        self.feature=feature
        self.IAF=10 #default
        self.calculate_iaf=calculate_iaf
        self.ch_feature, self.ch_iaf = eeg.chs_to_extract_feature(rewardfeature=self.feature)
        if not self.calculate_iaf: self.ch_iaf=None



        #INIT
        self.init()
        #self.init_methods()  #Init methods afterwards if you want to reinit vars

    def init(self):
        """INIT VARS

        Units:
            EEG : Volts V
            Time: Miliseconds ms
            Frequency: Hertz Hz

        """
        ###INPUT_DATA
        #units (Standard: Volts)
        self.input_data_unit="uV"  #'V','uV', 'nV';  ORIGINAL UNITS for Actichamp: float32 microvolts
        self.indata={} #place to store input data



        ###PREPROCESSING
        #1.select_channels
        self.select_chs = ['Fp1', 'Fp2', 'Fz','Cz','Pz']  #CHs for processing
        self.remove_unselect_chs=True


        #2.filter
        self.fs_n = self.amp_fs / 2  #nyquist
        self.order=5 #NOTE: Minimum required filter order is 4. For better results a minimum filter order of 8 is recommended. - In examples of Bastian venthur, 5 filter order in online experiment
        self.filtertype="butter"
        self.l_freq = 60 #hz
        self.h_freq = 0.5 #Hz - NOTE:Removes DC offset= constant freqs

        #3.Dowsample/Subsample - SAMPLES -
        self.subsample=None #None | int value below self.amp_fs
        #3.1: Rereference data ()
        self.amp_ref_channels = [] #[] no-ref montage; ['Fp1', 'Fp2'] - add ref channels if they don't come
        self.ref_channels = [] #ref_channels= "average"  |  [] No-rereferencing | ['CH'] for rereference
        #4.Artifact detection continuous signal(blinks and saccades)
        self.rej_eog = None #["Fp1", "Fp2"] #uses mne algorithm to detect eog artifacts of fp1 and fp2

        #feedback and threshold
        self.threshold_reward_level=-0.38 #std (-0.38*std => 65% above)
        self.threshold_inhibit_level=1 #std
        self.feedback_reward_level=0 #std
        self.feedback_inhibit_level=0 #std

        #5.epoch
        #remove baseline and detrend
        self.baseline=(None, None) #all epoch remove baseline - removes DC offset or low freqs
        self.detrend=1 #Detrend signal for fft - 1=linear 0=dc offset
        #epoch to segment data                      #(periodic Events will be added based on epoch interval)
        tmin=0 #ms
        tmax=self.window_time #ms ; use window_time as a basis for the epoch definition
        self.epoch_ival=[tmin,tmax] #ms (self.event_segment-1*self.actual_ts -epoch interval arround segment - remove last ts because of zero
        self.epochpackage="wyrm_to_mne"
        #Artifact rejection: Epoch
        self.rej_max_peaktopeak = 100e-6 #V
        self.rej_min_peaktopeak = 0.5e-6 #V
        self.rej_proj = True  #reject projections of rereference, artifact detection SSP or ICA
        #Average epoch
        self.epoch_average=True

        ###BUFFERS


        ###PROCESSING
        self.pink_max_r2=0.85 #None  #0.95 , None - doesnt check for noise in signal


        ###DEBUG
        #PSD - see init_methods
        self.n_fft=1024
        self.n_per_seg=self.n_fft*1 #fft window size percentage
        self.n_overlap=int(math.ceil(self.n_per_seg *0.25))
        #Plots
        self.plotlog = False



    def init_vars_dialogue(self):
        """INIT JSON DIALOGUE - TO alter vars before init_methods
        based on init vars
        TODO: Example - use for example pyff method feedback controller
        """
        pass

    def init_methods(self):
        """INIT METHODS Vars

        Obrigatory use.

        Init methods - specific class init and assertion of vars.
        Before routine to consume less time.
        Start methods for online and offline routine.
        Use after init, so you can change init vars however you like

        NOTE: init methods use "online" protocol because it inits all the variables, even if you are using only offline. This is good because you can init the class simultaneous for online and offline

        NOTE: Useful to separate class initiation from final methods
        """
        #ASSERT Vars based on problems


        ###INPUT_DATA
        self.data_unit = self.input_data_unit
        #1.Converting units
        #MNE uses V and s the International System units
        self.convert_units_exp = None
        if not self.data_unit == 'V':
            exponent=eeg._unit_dict.get(self.input_data_unit, None) #The conversion dict uses V as exponent 1; so if you want to convert to other units use a scaling factor
            if not exponent: raise RuntimeError("Add exponent to _unit_dict!")
            self.convert_units_exp=(exponent, 'V') #None or (exponent, unit)



        ###PREPROCESSING

        #1.select_channels
        #reset vars
        self.select_chs_ordered=[]  #names
        self.ch_picks=[]  #index
        self.ch_feature_picks = [] #index
        self.ch_iaf_picks = []  #index
        #adding additional channels that will be used
        ch_names=copy.copy(self.ch_names)#WARNING: Needs copy to not substitute self.ch_names
        if self.amp_ref_channels and not set(self.amp_ref_channels).issubset(self.ch_names):
            #1.STIM ('STI 014 is added in mne')
            ch_names.append('STI 014')
            #2.REF
            for ch in self.amp_ref_channels: ch_names.append(ch) #append at the end (WARNING: this is how mne does it)
        #Select Ch picks
        self.select_chs_ordered, self.ch_picks, self.ch_feature_picks, self.ch_iaf_picks = eeg.select_ch_picks(ch_names_in_order=ch_names, select_chs=self.select_chs, ch_extract_feature=self.ch_feature, ch_extract_iaf=self.ch_iaf)

        #initial state picks - save initial picks, because picks can alter during the processing
        self.select_chs_ordered_intial, self.ch_picks_initial, self.ch_feature_picks_initial, self.ch_iaf_picks_initial = self.select_chs_ordered, self.ch_picks, self.ch_feature_picks, self.ch_iaf_picks


        #2. Filter
        logger.debug("low cutoff to be above 100Hz because high_frequency_artifacts:{band:(45, 60)} gives NaN values when using log10(psd)")
        number_chs = len(self.ch_names)
        #Filter coefficients - all channels zi
        #ONLINE & OFFLINE - NOTE: online to get also zi - online is the higher protocol
        self.b_l, self.a_l, self.zi_l = eeg.filterdesigncoeff(self.fs_n, number_chs, order=self.order, freq=self.l_freq, filterband='low', filtertype=self.filtertype, method="online", package="wyrm")
        self.b_h, self.a_h, self.zi_h=eeg.filterdesigncoeff(self.fs_n, number_chs, order=self.order, freq=self.h_freq, filterband='high', filtertype=self.filtertype, method="online", package="wyrm")
        #zi parameter that represents the initial conditions for the filter delays
        #SOURCE:https://depositonce.tu-berlin.de/bitstream/11303/4734/2/venthur_bastian.pdf
        #NOTE it also seems to be optional

        #3.Dowsample/Subsample
        #NOTE: assert subsampling based on the resolution you need for FFT
        assert float(self.amp_fs) >= float(1000) #1000hz
        if float(self.amp_fs) > float(1000): self.subsample=1000
        self.subsample_max=int(self.amp_fs)
        self.actual_fs=self.amp_fs
        if self.subsample:
            self.subsample=int(self.subsample)
            assert self.amp_fs % self.subsample ==0 #make sure they are multiples - this is easier for blockbuffer
            assert self.subsample <self.subsample_max
            assert self.subsample >=250 #Because EEG neuphysiological signals are relevant till 100Hz
            self.actual_fs=self.subsample
        self.actual_ts=int( (1/float(self.actual_fs))*(10**(3)))#ms

        #assert window samples



        #4.Artifact detection continuous signal(blinks and saccades)

        #5.Epoch
        #Epoch properties
        self.epoch_segment = self.epoch_ival[1]-self.epoch_ival[0] #ms
        self.epoch_samples = int(math.ceil(self.actual_fs*(self.epoch_segment*(10**(-3)))))# samples
        self.window_samples=int(math.ceil(self.actual_fs*(self.window_time*(10**(-3)))))# samples
        assert self.window_time % self.epoch_segment == 0
        assert self.epoch_samples<=self.window_samples



        #reset new samples - #necessary in online to check if you have epochs with newsamples
        self.newsamples=None



        ###BUFFERS
        #Assert data Buffers

        #update blocksize
        if self.subsample: #blocksize = n* original_fs/subsample to make sure you have the right number of samples to subsample
            ratio=self.amp_fs/self.subsample
            found = False
            i=1
            bsize=self.blocksize
            while not found:
                if bsize % ratio == 0:
                    found=True
                    break
                if bsize>=ratio*i and bsize<=ratio*(i+1):
                    bsize=ratio*i
                i+=1
            self.blocksize=bsize

        #update ringbuffer
        logger.debug("#NOTE add samples to ringtime depending of how you eeg.add_repetitive_events_wyrm(method='') - 'onset'- 'offset' - 'all' ; 'offset' and 'all' need an additional sample just to have space to add the last event")
        #NOTE: Using 'onset' in online, and 'all' in offline - offline has no blockbuffer or ringbuffer, so it should work
        self.ringtime=self.ringtime+1*self.actual_ts#add one more sample, just to make sure you can add events
        #TODO:assert ringtime for power of 2 because of n_fft??

        #assert again
        assert self.blocksize<=self.blocksize_max
        assert self.blocktime<=self.ringtime
        assert self.epoch_segment <=self.ringtime

        #Init buffers
        #ONLINE
        self.blockbuffer, self.ringbuffer = eeg.init_buffers(blocksize=self.blocksize, ringtime=self.ringtime, method="online", package="wyrm")




        ###PROCESSING

        #1.PSD
        """
            see:
                https://sapienlabs.co/factors-that-impact-power-spectrum-density-estimation/
            #TODO:
             test EEG signal and assert based on tests

        """
#        if self.n_fft>self.window_samples: #NO zero-padding
#            self.n_fft=self.window_samples
#
#
#        #Test pink noise of PSD feature ch
#        logger.debug("# the FFT size (n_fft). Ideally a power of 2")
#        found = False
#        startpower = 8 #256 samples
#        if self.n_fft<=(2**startpower):
#            self.n_fft=2**startpower
#            found = True
#        i=0
#        while not found:
#            if self.n_fft>(2**(startpower+i)) and self.n_fft<=(2**(startpower+i+1)):
#                self.n_fft=2**(startpower+i+1)
#                found=True
#            i+=1
#
#        #DEFAULT FEATURES
#        self.n_per_seg=self.n_fft*1 #fft window size percentage
#        self.n_overlap=int(math.ceil(self.n_per_seg *0.25)) #fft window overlap
#
#        #TESTED FEATURES
#        if self.amp_fs>= 1000 and self.n_fft==1024:
#            self.n_per_seg=self.n_fft*1 #fft window size percentage
#            self.n_overlap=int(math.ceil(self.n_per_seg *0.25)) #fft window overlap




        #assert
        assert self.n_fft <= self.epoch_samples
        assert self.n_per_seg <= self.n_fft
        assert self.n_overlap <= self.n_per_seg
        #If n_per_seg is None n_fft is not allowed to be > n_times
        n_times=int(self.actual_fs*(self.ringtime*(10**(-3))))
        if self.n_fft> n_times and self.n_per_seg is None: raise AssertionError(' If n_per_seg is None n_fft is not allowed to be > n_times. If you want zero-padding, you have to set n_per_seg to relevant length. Got n_fft of {} while signal length is {}'.format(self.n_fft, self.n_times))# samples





        #Pink noise
        """Maximum R^2 allowed when comparing the PSD distribution to the
        pink noise 1/f distribution on the range 1 to 60 Hz.
        NOTE: Makes sense before starting experiment, but not during, because if it is noisy sometimes, that data will not appear
        You can have a not so mutch stringent value like 0.95
        """


        ###RESET Unspecific Vars

        self.close = False #Close algorithm if something is not correct



        ###STATE OBJECTS INIT - Important for loop

        #reset state vars
        self.online_step_state=None
        self.initial_state=None
        logger.debug("#BUG #SOLVED - self cant have thread.lock objectes like the logger from other class -")
        #init state vars
        self.online_step_state=copy.deepcopy(self)
        #Initial state saves initial config object class
        self.initial_state=copy.deepcopy(self)


        ###LOG INIT VARS
        logger.debug("\n>> *****INIT VARS: \n{}".format(my.parse_object_dict(self)))
        #serialize class vars
        if self.serialize_vars:
            try:
                classname=self.__class__.__name__
                filedir=self.serialize_vars
                my.serialize_object(self, filedir, classname+"_init_vars", method="json")
            except Exception as e:
                logger.error("Class object vars not serialized and saved, error: {}".format(e))



    def input_data(self, testingvars=True, package="wyrm"):
        logger.debug("INPORT/LOAD DATA")
        self.start_marker, self.end_marker = None, None

        if package=="wyrm":
            #OFFLINE
            if self.routine=="offline":
                if self.data is None:
                    self.data, self.start_marker, self.end_marker = eeg.load_data(self.filepath, self.filetype, package="wyrm")#format:wyrm data


                elif type(self.data) is np.ndarray:#input data
                    #format: mushu: data: numpy samples X channels; markers:list of tuples  [(absolute_m_timestamps, m_name),...]
                    self.data, _ = eeg.convert_data(self.data, markers=self.markers, amp_fs=self.amp_fs,in_data_unit=self.data_unit, amp_channels=self.amp_chs, method="mushu_to_wyrm")#format: wyrm
                    self.start_marker, self.end_marker = "START", "END" #DEFAULT MARKER DISCRIPTORS USED IN THIS FRAMEWORK


            #ONLINE
            #Newsamples  - online data -inportant for epoch to use all the newsamples
            self.newsamples=None #Reset
            if self.routine=="online":
                if type(self.data) is np.ndarray:#input data:
                    #format: mushu: data: numpy samples X channels; markers:list of tuples  [(relative_m_timestamps, m_name),...]
                    self.data, _ = eeg.convert_data(self.data, markers=self.markers, amp_fs=self.amp_fs, amp_channels=self.amp_chs,in_data_unit=self.data_unit, method="mushu_to_wyrm")#format: wyrm

                    #blockbuffer: make sure that the data is a multiple of blocksize - and updates current buffer decimation - Factor by which to downsample the data
                    self.data, self.blockbuffer = eeg.apply_blockbuffer(self.data, self.blockbuffer, method="online", package="wyrm")
                    if not self.data: #check if the data > blocksize, if not ask again for new data
                        self.continue_to_next_loop()
                        return
                else: #none;
                    self.continue_to_next_loop()
                    return

            #TEST VARS  - cross init class vars with data vars to see if its correct
            #amp_chs = server amp_chs - defined from the server data
            #data.chs can come offline, so if different stop and ask if the user wants to continue with deffintions from the app
            if testingvars:
                chanaxis=-1
                data_chs=self.data.axes[chanaxis].tolist()
                try:
                    assert(data_chs==self.amp_chs==self.ch_names)#data_chs vs ch_names vs server amp_chs
                    assert int(self.data.fs)==int(self.amp_fs)
                except Exception as e:
                    logger.error('Input data vars are different from init class, msg: {} \n>>data_chs :{}; \n>> amp_chs: {} ; \n>> ch_names: {}'.format(e, data_chs, self.amp_chs, self.ch_names))
                    if not (len(data_chs)==len(self.amp_chs)==len(self.ch_names)):
                        raise AssertionError('Input data vars are different from init class(check), msg: {}'.format(e))
                    else:
                        logger.warning("\n>> I assume you now what your doing, they have the same lenght! therefore data_chs==self.amp_chs==self.ch_names")
                        data_chs=self.amp_chs

            logger.debug("WYRM, DATA MAX, DATA MIN: {}, {}".format(np.amax(self.data.data), np.amin(self.data.data)))

            #CONVERT UNITS
            if self.convert_units_exp:
                self.data=eeg.convert_units(self.data, convertion=self.convert_units_exp, package="wyrm")
                logger.debug("WYRM, DATA MAX, DATA MIN: {}, {}".format(np.amax(self.data.data), np.amin(self.data.data)))
                self.data_unit =self.convert_units_exp[-1]

        assert self.data_unit=="V" #Standard Volts
        self.indata=copy.copy(self.data)
        logger.debug("!DATA LOADED!")


    def preprocessing(self):
        """
        TODO:
            Wyrm to MNE conversion is slow(~200ms), possible solutions:
                1.Create a saving structure more fast that directly uses realtime mne capabilities(go to site)
                2.Use only wyrm as it is simple and faster, however have to create functions


            So for now, online speed can't go below 200ms and is not constant
        """
        logger.debug("!!PREPROCESS DATA!!")

        package='wyrm'

        #2.Select Data Interval
        if self.routine=="offline":
            self.data=eeg.select_data_interval(self.data, self.start_marker, self.end_marker, method="markers", package=package)

        #3.Filter data
        logger.debug("#WARNING zi(initial filter delays!!!!) online component  updated to next cycle ")
        #low pass
        self.data, self.zi_l = eeg.filtering(self.data, self.b_l, self.a_l, self.zi_l, method=self.routine, package=package)
        #high pass
        self.data, self.zi_h = eeg.filtering(self.data, self.b_h, self.a_h, self.zi_h, method=self.routine, package=package)

        #4. Samples
        #Subsample data #from 500 to 100 points
        if self.subsample: #if None dont do subsample
            self.data = eeg.subsample(self.data, self.subsample, method=self.routine, package=package)
        #Newsamples : MAke sure they are before ringbuffer
        self.newsamples = self.data.data.shape[0]

        #5. Ringbuffer in preprocessing -online - needs to be after subsampling
        if self.routine=="online":
            #Apply ring buffer - to accumulate data
            self.data, self.ringbuffer = eeg.apply_ringbuffer(self.data, self.ringbuffer, method=self.routine, package=package)
            #Test if ringbuffer  - if not continue to next loop - can also test and wait for ringbuffer to get full, if not self.data or not self.ringbuffer.full:
            if not self.data and not self.ringbuffer.full:
                self.continue_to_next_loop()
                return


        #6.prepare events in wyrm - offline add epoch events
        self.data, self.marker_def = eeg.prep_epoch(self.data, self.epoch_ival, timeaxis=-2, newsamples=self.newsamples, start_marker=self.start_marker, end_marker=self.end_marker, method=self.routine, package=self.epochpackage)
        if not self.data:
            self.continue_to_next_loop()
            return  #empty cnt - return and get to next loop

        #8.Change data to MNE if wanted
        st=time.time()
        self.event_id=None
        if self.epochpackage=="wyrm_to_mne":

            package="mne"

            logger.debug("WYRM, DATA MAX, DATA MIN: {}, {}".format(np.amax(self.data.data), np.amin(self.data.data)))
            #CONVERT TO MNE - UNITS - VOLTS

            self.data, self.event_id = eeg.convert_data(self.data, ch_names=self.ch_names, in_data_unit=self.data_unit, method="raw_wyrm_to_mne")

            if self.plotlog:
                picks=mne.pick_types(self.data.info,eeg=True)
                logger.debug(
                    "MNE, DATA MAX, DATA MIN: {}, {}".format(
                    np.amax(self.data.get_data(picks=picks)),
                    np.amin(self.data.get_data(picks=picks))
                    ))
                eeg.plot_segment(self.data, time_ival=[10, 15], n_ch_max=10)
                logger.debug("#NOTE: Wyrm time units in ms; MNE time units in s -mne seems to undersand - but it seems data needs to be in V")
                logger.debug("RAW INFO: {}".format(self.data.info))
            #!!Do extra preprocessing with mne!! or Visualization

        et=time.time()-st
        logger.info("\n>> WYRM TO MNE: {}".format(et))

        #Re-reference the data (add also amp_ref_channels)
        st=time.time()
        #1.add amp ref manually
        self.data = eeg.rereference(self.data, ref_channels=self.ref_channels,amp_ref_channels=self.amp_ref_channels, package=package)
        #Artifact detection(Mark) - continuous signal - filter_lenght changes attenuation
        et=time.time()-st
        logger.info("\n>> REREFERENCE: {}".format(et))
        st=time.time()

        #Select Chs data - WARNING - ONLY AFTER REREFERENCE
        if self.remove_unselect_chs: #if rereference then can't select
            self.data = eeg.select_data_chs(self.data, self.ch_picks, package=package)
            #redo picks index based on new chs list
            self.select_chs_ordered, self.ch_picks, self.ch_feature_picks, self.ch_iaf_picks = eeg.select_ch_picks(ch_names_in_order=self.select_chs_ordered, select_chs=None, ch_extract_feature=self.ch_feature, ch_extract_iaf=self.ch_iaf)


        #remove blinks and saccades
        if self.rej_eog:
            filter_length_int = int( 1*(self.ringtime/1000.) ) #s
            if filter_length_int==0:
                filter_length_int=1
            filter_length = str(filter_length_int)+'s'  #using 1s to be very permissive
            self.data = eeg.artifact_detection_continuous(self.data, rej_eog=self.rej_eog, filter_length=filter_length, plotlog=False, method=self.routine, package=package)
            logger.debug("Raw Shape: {}".format(self.data.get_data().shape))




        #7.Epoch data - artifact detection in epoch and rejection of bad epochs based in all the marks
            #7.1.Create epoch - using event epo=102
            #7.2.Detrend and/or remove baseline;
            #7.3 reject continuous artifact annotations and projections

        self.data = eeg.epoch_data(self.data, self.epoch_ival, marker_def=self.marker_def, event_id=self.event_id, newsamples=self.newsamples, baseline=self.baseline, detrend=self.detrend, plotlog=False, method=self.routine, package=package)
        logger.debug("Epoch Shape: {}".format(self.data.get_data().shape))

        if not self.data:
            self.continue_to_next_loop()
            return

        #7.3.Artifact detection in epoch and rejection
        #reject additional bad epochs - rej_max_peaktopeak, rej_min_peaktopeak
        self.data=eeg.artifact_rejection_epoch(self.data, rej_max_peaktopeak=self.rej_max_peaktopeak, rej_min_peaktopeak=self.rej_min_peaktopeak, plotlog=False, package=package)
        logger.debug("Epoch Shape: {}".format(self.data.get_data().shape))
#        pdb.set_trace()
        if not self.data:
            self.continue_to_next_loop()
            return

        et=time.time()-st
        logger.info("\n>> EPOCH PREPROCESSING: {}".format(et))

#        #7.4 Average all epochs in temporal only for ERPs
#        #average epochs - evoked type of data - 500 samples/s  0.2 =
#        if self.epoch_average:
#            self.data=eeg.epoch_average(self.data, plotlog=False, package=package)
#            logger.debug("Evoked Shape: {}".format(self.data.data.shape))
##            pdb.set_trace()
#            if not self.data:
#                self.continue_to_next_loop()
#                return







    def processing(self):
        "PROCESS DATA"
        ##1.PSD -
        #NOTE: only do psd in chs to extract(feature and iaf) - !LESS PROCESSING TIME!
        package="mne"
        picks= self.ch_feature_picks
        if package=="mne":
            #add iaf to picks if offline
            if self.routine=="offline":
                if self.ch_iaf:
                    picks = sorted(self.ch_feature_picks+self.ch_iaf_picks) #sort correctly the picks to maintain index intact
                    picks = list(set(picks)) #remove duplicates


            #GET chs psds of picks of all epochs
            #OFFLINE psds shape (n_epochs, n_channels, n_freqs)
            #ONLINE: (1, n_channels, n_freqs)
            self.psds, self.freqs, self.fftresolution, self.n_fft=eeg.psd(self.data, picks=picks, n_fft=self.n_fft, n_per_seg=self.n_per_seg, n_overlap=self.n_overlap, fmin=self.h_freq, fmax=self.l_freq, tmin=None, tmax=None, method="welch", package="mne")

            #AVERAGE epoch psds - psds shape (n_epochs, n_channels, n_freqs) => psd (n_channels, n_freqs)
            epochaxis = 0
            self.psd = self.psds.mean(epochaxis) #GET ONLY ONE PSD
            if self.plotlog:
                eeg.plot_psd(self.psd, self.freqs, psdtypeused="welch")

            #EPOCH PSD PICKS #redo picks index based on new data 
            self.psd_ch_feature_picks=None
            self.psd_ch_iaf_picks=None
            if picks:
                self.psd_select_chs_ordered, self.psd_picks, self.psd_ch_feature_picks, self.psd_ch_iaf_picks = eeg.select_ch_picks(ch_names_in_order=[self.select_chs_ordered[p] for p in picks], select_chs=None, ch_extract_feature=self.ch_feature, ch_extract_iaf=self.ch_iaf)

            
            #EPOCH FEATURE EXTRACTION 
            self.epoch_psd_feature_extraction(self.psd_select_chs_ordered, self.psd_picks, self.psd_ch_feature_picks, self.psd_ch_iaf_picks )



    def epoch_psd_feature_extraction(self, select_chs_ordered, picks, ch_feature_picks, ch_iaf_picks ):
        ##2.FEATURE EXTRACTION
        #1.prepare bands information - OFFLINE(No loop only one time); ONLINE(IF MISSING Reward bands calculate the first time -it saves )
        if not self.reward_bands:
            #1.get IAF offline
            if ch_iaf_picks: #only calculate if ch_iaf exists
                self.IAF = eeg.calculate_iaf(self.psd, self.freqs, picks=ch_iaf_picks, psdsmooth=True, alpha_fmin=8, alpha_fmax=12, pink_max_r2=self.pink_max_r2, ax=False)
            #2.get init bands
            self.bands = eeg.get_bands(self.IAF)
            self.reward_bands, self.inhibit_bands = eeg.get_reward_inhibit_bands(self.bands, rewardfeature=self.feature) #add to get_reward_inhibit_bands new features


        #2calculate features
        #2.1prepare psd for features to extract
        #2.1.1(average psd or specific ch)
        #2.1.2 TEst if psd of ch is noisy
        self.ch_feature_psd, self.noisysignal, self.ch_feature_name, self.psd_linregress = eeg.psd_prep_extraction(self.psd, self.freqs, picks=ch_feature_picks, ch_names_ordered=select_chs_ordered, psdsmooth=True, pink_max_r2=self.pink_max_r2, ax=self.plotlog)


        if self.noisysignal: #ruido pink noise
            logger.warning("WARNING: CHs picked {} for feature, have pink noise above {}".format(self.ch_feature, self.pink_max_r2))
            #choose to exit or not the routine:pass or return
            self.continue_to_next_loop()
            return
            #pass
        
        #3.2 get_features: update bands with new info
        self.reward_bands = eeg.get_band_features(self.ch_feature_psd, self.ch_feature_name, self.freqs, self.reward_bands, data_unit=self.data_unit, psdlogarithm=False, feature=self.feature, datatype=self.datatype, reward_level=self.reward_level, bandtype="reward")
        self.inhibit_bands = eeg.get_band_features(self.ch_feature_psd, self.ch_feature_name, self.freqs, self.inhibit_bands, data_unit=self.data_unit, psdlogarithm=False, feature=self.feature, datatype=self.datatype, inhibit_level=self.inhibit_level, bandtype="inhibit")


        logger.debug("#BUG #semisolved threshold and feedback scale not in same order - using 10*log10(psd) - feedback is allways above threshold - maybe use adaptive threshold to change this behaviour - not happy with how things are working")
        logger.debug("#BUG nan values of high artifact bands - maybe because of log10(psd) and because filter close to the data")




    def postprocessing(self):
        "RESULTS PROCESSING"
        #NOTE:IAF Only added if offline
        if self.routine=="offline":
            self.result={"inhibit_bands": self.inhibit_bands, "reward_bands": self.reward_bands , "IAF":self.IAF , "IAF_ch":self.ch_iaf, "psd_linregress":self.psd_linregress, "indata":self.indata}
            self.output_data()
            return

        if self.routine=="online":
            self.result={"inhibit_bands": self.inhibit_bands, "reward_bands": self.reward_bands, "IAF":self.IAF , "IAF_ch":self.ch_iaf, "psd_linregress":self.psd_linregress, "indata":self.indata}
            self.output_data()
            return


        #self.on_quit()

    def output_data(self):
        "EXPORT DATA"
        if self.routine=="offline":
            #serialize class vars
            if self.serialize_vars:
                try:
                    classname=self.__class__.__name__
                    filedir, filenametype=os.path.split(self.filepath)
                    filename, filetype =os.path.splitext(filenametype)
                    my.serialize_object(self, filedir, filename+"_"+classname+"_final_vars", method="json")
                except:
                    logger.error("Class object vars not serialized and saved, error: {}".format(copy.error.message))


        if self.routine=="online":
            #send features to presentation?? No, leave it to do in parent class
            return

    def continue_to_next_loop(self):
        logger.debug("\n>> !!!NEXT LOOP - PROCESSING NOT FINISHED!!!")
        self.close=True


    def set_initial_state(self):
        # INITIAL STATE
        logger.debug("#NOTE: INITIAL STATE OBJECT - IMPORTANT make a copy in the current class  with everythin initied,, !!BECAUSE IF YOU COPY THIS OBJECT IN NEXT USE IT DISAPEARS!! - TODO test if it works like this, use to return the class initial state - use when finished using - return in offline  -  maybe can't work in online because of online step state")
        #1 Get previous online step state -
        previous_initial_state = self.initial_state
        #2.pass the class to step state - protect previous with copy
        initial_state = copy.deepcopy(previous_initial_state)
        #3. add to class the online step state to be used in next iteration - ??using previous to maintain allways the same object even if the all class is changing??
        initial_state.initial_state = previous_initial_state
        #adding again online step just to be sure
        initial_state.online_step_state=self.set_online_step_state().online_step_state
        return initial_state

    def set_online_step_state(self):
        #ONLINE STEP STATE - loop state - INITIAL STATE + loop state vars updated
        logger.debug("ONLINE STEP STATE - loop state - Only Saves Variables that are needed for next loop  - after using it to reset class, you need to add it again - if not it desapears - TODO:maybe dont need copy to protect - add also initial state")
        #1 Get previous online step state -
        previous_online_step_state = self.online_step_state
        #2.pass the class to step state - protect previous with copy
        online_step_state = copy.deepcopy(previous_online_step_state)
        #3. add to class the online step state to be used in next iteration - ?can use previous or new because the object has the same information updated??
        online_step_state.online_step_state = online_step_state
        #adding again initial state just to be sure it remains
        online_step_state.initial_state = self.set_initial_state().initial_state

        return online_step_state

    def reset_class_state(self, routine="offline"):
        """
        online = online step state class - saves online state - some vars
        offline = initial state class - saves initial class state with all the vars

        Note:
            self.initial_state needs to be the last var to be inited - in that way you also save the initial state of online step state
            Online only can be reseted to initial state after the online experiment is finished(after the while is finished)
        """
        #1 Get previous states
        previous_online_step_state = self.online_step_state
        previous_initial_state = self.initial_state


        if routine=="online":
            #2.pass the class to state -needs copy because you cant mess with state object class
            #RESET STATE TO ONLINE STEP STATE
            resetclass = copy.deepcopy(previous_online_step_state)
            #3.mantain always same objects - initial state never updated - online state will have vars allways updated
            resetclass.online_step_state = previous_online_step_state
        else:
            #2.pass the class to initial state - using same object - initial state already has initial online_step state
            resetclass = copy.deepcopy(previous_initial_state)



        resetclass.initial_state = previous_initial_state

        return resetclass

    def reset_class(self, method="initial_state"):
        """
        Compilation of methods to reset the class

        #TEST reset_to_initial state and init_methods
        """
        resetclass = self #same object class

        #"reset_to_initial_state"
        if method=="initial_state": resetclass =self.reset_class_state(routine="offline")#new object - #working,

        #"reset_using_init_methods"
        if method=="init_methods": resetclass.init_methods() #same object #TODO:not tested - can't be used online, it  resets everything

        #"reset_to_step_state"
        if method=="step_state": resetclass=self.reset_class_state(routine=self.routine)#new object - Tested: working but a little bit complicated #TODO possibly not use it


    def pipelines(self, pipeline="step_state"):
        """
        Compilation of working pipelines to play the offline or online routine
        """
        processing_finished = False


        #WARNING: WORKING
        if pipeline=="step_state": #STEP Object- Reset all vars except the needed to the next loop

            #1.input_data
            st=time.time()
            self.input_data()
            et=time.time()-st
            logger.info("\n>> INPUT_DATA: {}".format(et))
            if self.routine=="online":#Vars not to reset for next loop when copying to new object
                self.online_step_state.blockbuffer=self.blockbuffer
                self.online_step_state.ringbuffer=self.ringbuffer
            if self.close: return processing_finished, self.reset_class_state(routine=self.routine)
            #2.preprocessing
            st=time.time()
            self.preprocessing()
            et=time.time()-st
            logger.info("\n>> PREPROCESSING: {}".format(et))
            if self.routine=="online":#Vars not to reset for next loop when copying to new object
                self.online_step_state.zi_l=self.zi_l
                self.online_step_state.zi_h=self.zi_h
            if self.close: return processing_finished, self.reset_class_state(routine=self.routine)
            #3.processing
            st=time.time()
            self.processing()
            et=time.time()-st
            logger.info("\n>> PROCESSING: {}".format(et))
            if self.close: return processing_finished, self.reset_class_state(routine=self.routine)
            #4.postprocessing
            st=time.time()
            self.postprocessing()
            et=time.time()-st
            logger.info("\n>> POSTPROCESSING: {}".format(et))
            if self.routine=="online":#Vars not to reset for next loop when copying to new object
                self.online_step_state.result=self.result
            if self.close: return processing_finished, self.reset_class_state(routine=self.routine)
 #new object

        #WARNING: NEEDs TESTING
        if pipeline=="initial_state": #Maintain initial object - hope everything is correctly reset and that the buffers and zi are updated to next loop

            #1.input_data
            self.input_data()
            if self.close: return processing_finished, self.reset_class_state(routine=self.routine)
            #2.preprocessing
            self.preprocessing()
            if self.close: return processing_finished, self.reset_class_state(routine=self.routine)
            #3.processing
            self.processing()
            if self.close: return processing_finished, self.reset_class_state(routine=self.routine)
            #4.postprocessing
            self.postprocessing()
            if self.close: return processing_finished, self.reset_class_state(routine=self.routine)


        #Finished
        processing_finished = True
        return processing_finished, self.reset_class_state(routine=self.routine)






    def play_routine(self, data=None, markers=None, reward_bands=None, inhibit_bands=None, filepath=None, filetype=None, taskname="nft", routine="offline"):

        #Init vars
        self.routine=routine
        self.data=data #mushu data
        self.markers=markers #mushu markers
        self.taskname=taskname #Deprecated only using datatype
        self.reward_bands=reward_bands
        self.inhibit_bands=inhibit_bands
        self.filepath=filepath
        self.filetype=filetype

        #assert vars
        if self.markers is None:self.markers=[] #assert markers
        #datatype fixed so you have always the same keys in reward and inhibit bands
        if routine=="offline":
            self.datatype="threshold"
            self.reward_level=self.threshold_reward_level
            self.inhibit_level=self.threshold_inhibit_level
        if routine=="online":
            self.datatype="feedback"
            self.reward_level=self.feedback_reward_level
            self.inhibit_level=self.feedback_inhibit_level


        #play processing pipeline

        try:
            processing_finished, updateclass = self.pipelines(pipeline="step_state")
        except BaseException as e:
            logger.error('\n>> Error during processing: {}'.format(e))
            processing_finished=False
        #just for peace of mind - reseting one more time
        updateclass=self.reset_class_state(routine=self.routine)


        return processing_finished, updateclass




if __name__=="__main__":
    print("START")

    #SAMPLEDATA
    # replay sample data (using same for online and offline if you don't acquire data)
    folderdir = 'e2_sample'
    filename = "EG_S001_REST_ss01_b01_08102019_14h13m_rest_1"
    filetype = ".meta"
    filepath = my.get_filetoreplay(folderdir=folderdir, filename=filename, filetype=filetype)  # filepath
    data, start_marker, end_marker = eeg.load_data(filepath, filetype, package="wyrm")  # format:wyrm data
    chanaxis = -1
    data_chs = data.axes[chanaxis].tolist()

    #nftalgorithm convention amp_chs=ch_names=data_chs
    # amp_chs: the chs coming from the amp through the inlet (online)
    # ch_names: full montage ch names. If amp_chs in ch_names: ch_names=amp_chs
    # data_chs: nftalgorithm input data chs
    # as we are using a saved data file, then we use data_chs as the data.

    #DATA information - Manually put info of file to init algorithm parameters
    amp_fs=data.fs
    ch_names=amp_chs=data_chs
    feature="alpha"
    window_time=1024 #ms window to process data array

    nftproc=nftalgorithm(amp_fs=amp_fs, amp_chs=amp_chs, ch_names=ch_names, window_time=window_time, feature=feature)
    #change init vars before init methods if needed
    nftproc.init_methods()

    #OFFLINE processing



    try:
        routine="offline"
        nftproc.play_routine(filepath=filepath, filetype=filetype, taskname="rest",  routine=routine)
        #result
        print nftproc.result

    except Exception as e:
        logger.error("SOMETHING WENT WRONG: {}".format(e))
        raise
