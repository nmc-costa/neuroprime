# -*- coding: utf-8 -*-
"""
Created on Fri May 03 17:02:39 2019



@author: nm.costa
"""
from __future__ import (absolute_import, division, print_function)
from builtins import * #all the standard builtins python 3 style - input(), to work running a Python script in interactive session

__version__ = '6.2+dev'
"""
#TODO: version 7 needs to be clean - send everything to driver(even the stop and close specific files), don't touch the ampdecorator - add buffer writing to file in driver - need to separate in a simple(remove everyting not needed to work ) and complex version, save the 2 versions as a tutorial
#Pycorder rda not needed
#Pycnbi not needed
#save buffers should not be in ampdecorator but in driver to make everything congruent and easier to update
#validate methods: reconfigure is enough to make everything working even after close_stream()
#same problem of open and close streams - from the first time you pull_chunk, the data starts to get queryied and I don't know how to resart it - and close stream breaks things?#SOLVED: present solution reconfigure again before opening new stream - this way you can use close_stream
"""

import os
import libmushu
import libmushu.driver.labstreaminglayer #necessary to load the drivers
import pylsl
import json
import struct
import numpy as np
import time
import datetime

import cPickle as pickle #faster
# My functions
import neuroprime.src.utils.myfunctions as my
#Module logger
import logging
logging_level=logging.INFO
logger = logging.getLogger(__name__)
logger.setLevel(logging_level)
logger.info('Logger started.')




#1.CONFIGURE AMP: driver patch for markers
def libmushu_labstreaminglayer_configure(self, **kwargs):
    """Configure the  connection to lsl and rda streams.

    This method looks for open lsl streams and picks the first `EEG`
    and `Markers` streams and opens lsl inlets for them.

    Note that lsl amplifiers cannot be configured via lsl, as the
    protocol was not designed for that. You can only connect (i.e.
    subscribe) to devices that connected (publishing) via the lsl
    protocol.

    UPDATE:
        kwargs interpretation added
        Also looks for RDA stream
        timeout for stream searchs
        NOTE:
            RDA stream inlet has an independent thread
            LSL stream has internal queue buffer
                LSL Buffer restarts queuing samples when open_stream() and can be droped using close_stream()
                Each time you pull a sample you are removing them from the buffer
                max_buflen will be 5s because this is real_time and each time a timeout occurs the task should start again just to be safe - closed loop task can be biased if you wait more than that when showing feedback
            start() - open_stream(); stop - close_stream();
            #BUG in data could have been from lack of open_stream() whenever a new experiment starts

    """
    modulename=libmushu.driver.labstreaminglayer.__name__
    logger = logging.getLogger(modulename)
    logger.setLevel(logging_level)
    logger.debug("****patch_libmushu_labstreaminglayer_configure****")


    #Vars INIT (Kwargs var can be changed)
    self.add_buffer=True #add data to the buffers #always on - simplifies data management

    #get_data()
    self.max_samples = kwargs.get("max_samples", 1024) #create buffer blocks of 1024 samples; Note: if not found the key, put 1024
    self.get_data_sleeptime = kwargs.get("get_data_sleeptime", float(0.0005)) #default 0.5ms query - get_data sleep time before asking for next chunk

    #OPEN STREAMS:
    self.stream_type=kwargs.get("stream_type", 'EEG') #string: it should be equal to the type defined in the outled
    self.stream_server=kwargs.get("stream_server", 'lsl') #LSL, pycorder_rda or None ; None waits till lsl or pycorder_rda stream appers
    self.lsl_inlet=kwargs.get("lsl_inlet", None)#lsl inlet object
    self.lsl_amp_name=kwargs.get("lsl_amp_name", None)#string - lsl amp name
    self.pycorder_rda_inlet=kwargs.get("pycorder_rda_inlet", None)#rda inlet object
    self.lsl_marker_inlet=kwargs.get("lsl_marker_inlet", None)#lsl inlet object
    self.lsl_marker_name=kwargs.get("lsl_marker_name", None)
    self.lsl_addmarker_inlet=kwargs.get("lsl_addmarker_inlet", None)#lsl inlet object
    self.lsl_addmarker_name=kwargs.get("lsl_addmarker_inlet", None)#lsl inlet object
    self.lsl_save_buffers=kwargs.get("lsl_save_buffers", True)#boolean true/false
    self.lsl_save_buffer_pycnbi=kwargs.get("lsl_save_buffer_pycnbi", None)#boolean true/false
    self.block_time=kwargs.get("block_time", None)#s , get_data block till you get the right amount of data
    self.inlet_max_buflen=kwargs.get("inlet_max_buflen", 360) #s , Intlet max_buflen, default:360 s ; NOTE: Real time buflen can be low, because you are using and saving data right away - Test before!

    #STREAM MANUAL added Vars
    #manual offsets
    self.rda_amp_offset=kwargs.get("rda_amp_offset", 50e-3)#s #source: 2015 press release BVP (50-100ms)
    self.lsl_amp_offset=kwargs.get("lsl_amp_offset", None) #s #source:2017 press release BVP (1.21+-0.5 ms) ->default uses time_correction from lsl
    self.lsl_marker_offset=kwargs.get("lsl_amp_offset", None)
    #assert to have the two offsets - if not using automatic time_correction()
    if not self.lsl_amp_offset: self.lsl_marker_offset =None#assert
    if not self.lsl_marker_offset: self.lsl_amp_offset =None
    #manual refs
    self.amp_ref_channels=kwargs.get("amp_ref_channels", [])

    #STREAMs CALCULATE offsets
    self.test_lsl_offset=kwargs.get("test_lsl_offset", True)
    self.lsl_time_offset=None #lsl time offset is calculated by pulling chunks as fast as possible, formula: local_clock() -last_timestamp_sample
    self.max_offset=0.05 #50ms



    #STREAMs Validation on start()
    self.validate_offsets=False #validate only offsets - #WARNING It opens streams queu, you need to reopen again after this
    self.validate_configure=True#Necessary because I still don't now how to restart queued data, unless configuring again
    self.validate_get_data=False #validate get_data() method buffering first window - optinal

    #STREAMs Validation on get_data()
    self.check_for_markers=False #Use this to check after a timeout the markers are present (should only be used if all presentations use markers)

    #CLOSE STREAMs in ampdecorator
    self.close_stream=False#self.validate_configure #with reconfigure activated you can close streams

    #if amp is ready to get_data
    self.ready = False #true when the start is valid

    #INIT Watchdog
    self.watchdog=my.Timer()

    #TIMEOUTS
    self.receive_marker_timeout=kwargs.get("receive_marker_timeout", 30) #s if using markers_buffer check at timeout if you have any marker in the buffer -> return something to be picked
    TIMEOUT = 60*5 #s  #timeout to wait for streams to come alive




    #Opening AMP streams
    if not self.lsl_inlet and not self.pycorder_rda_inlet:
        logger.debug('\n>>******Opening {} stream******'.format(self.stream_type))
        # pycorder_rda THREAD
        pycorder_rda_inlet_connected=False
        if self.stream_type=='EEG' and (not self.stream_server or self.stream_server =="pycorder_rda"):
            from neuroprime.src.signal_acquisition.rda_client.pycorder_rda_client_nogui import RDA_Client
            self.pycorder_rda_inlet = RDA_Client()
            #default values
            self.pycorder_rda_inlet.HOST = 'localhost'
            self.pycorder_rda_inlet.PORT = 51244           #: 32-Bit data port single precision
            self.pycorder_rda_inlet.ADDR = (self.pycorder_rda_inlet.HOST, self.pycorder_rda_inlet.PORT)
            self.pycorder_rda_inlet.connectClient() #Thread loop in wait mode -connect
            pycorder_rda_inlet_connected=False

        #TIMEOUT to find AMP stream
        self.watchdog.reset()
        while self.watchdog.sec() < TIMEOUT and ( (not self.lsl_inlet and not pycorder_rda_inlet_connected) or (self.lsl_inlet and pycorder_rda_inlet_connected)):
            logger.warning('\n>> *****WAITING {} STREAM: ******'.format(self.stream_type))

            if self.lsl_inlet and pycorder_rda_inlet_connected: logger.warning('#WARNING: Please close one of the server streams, use only one, pycorder_rda or LSL ')
            # pycorder_rda server
            if self.stream_type=='EEG' and (not self.stream_server or self.stream_server =="pycorder_rda"):
                logger.warning('\n>> Waiting pycorder_rda stream...')
                if self.pycorder_rda_inlet.client_thread_state==2: #connected
                    logger.warning('pycorder_rda client CONNECTED to server...')
                    logger.warning('\n>> Waiting START MESSAGE...')
                    if self.pycorder_rda_inlet.serverDataValid:#server data valid
                        pycorder_rda_inlet_connected=True
            # LSL server
            if not self.stream_server or self.stream_server =="lsl":
                logger.warning('\n>> Waiting LSL {} stream...'.format(self.stream_type))
                if not self.lsl_amp_name:
                    self.lsl_amp_name, self.lsl_amp_serial, self.lsl_inlet = my.choose_lsl(streamtype=self.stream_type)
                elif self.lsl_amp_name:
                    self.lsl_amp_serial = "N/A"
                    self.lsl_inlet = my.return_stream_inlet(self.lsl_amp_name, streamtype=self.stream_type, max_buflen=self.inlet_max_buflen, wait_time=0.01) #None if it does not find

            #STOP if found
            if (self.lsl_inlet and not pycorder_rda_inlet_connected) or (not self.lsl_inlet and pycorder_rda_inlet_connected):
                #STOP while
                break

            time.sleep(1)
        else:
            logger.error('\n>> ERROR : Timeout {}s occurred while acquiring data. Amp driver bug?'.format(TIMEOUT))
            raise



        #test lsl offset performance
        if self.lsl_inlet and self.test_lsl_offset:#note this turns configure slower and you already oppened the stream the first time
            self.lsl_time_offset, stream_valid, restart_configure=my.test_lsl_inlet_offset(self.lsl_inlet, max_offset=self.max_offset)
            if restart_configure: raise RuntimeError('Timeout occurred to pull samples. Check if amp is sending data!')
            if not stream_valid: raise RuntimeError('Offset: {}  > Max_offset : {}. Check lsl amp'.format(self.lsl_time_offset, self.max_offset))

        #assert for only one EEG stream - NOTE: In localhost is impossible to start in pycorder at the same time you start actichamp lsl app - this will only occur if sending from two computers, or an unwanted EEG stream is openned exteriorly
        assert ((self.lsl_inlet and not pycorder_rda_inlet_connected) or (not self.lsl_inlet and pycorder_rda_inlet_connected))
        if self.lsl_inlet and not pycorder_rda_inlet_connected and self.pycorder_rda_inlet: #reset pycorder_rda_inlet if not in use
            self.pycorder_rda_inlet.disconnectClient()
            self.pycorder_rda_inlet = None
            logger.debug('lsl_inlet: {}'.format(self.lsl_inlet))
        if not self.lsl_inlet and pycorder_rda_inlet_connected:
            self.lsl_inlet = None
            logger.debug('pycorder_rda_inlet: {}'.format(self.pycorder_rda_inlet))

        #UPDATE - ADD STREAM RECEIVER PYCNBI
        if self.lsl_inlet and self.lsl_save_buffer_pycnbi:
            from pycnbi.stream_receiver.stream_receiver import StreamReceiver
            # connect to EEG stream server
            self.sr = StreamReceiver(amp_name=self.lsl_amp_name, amp_serial=self.lsl_amp_serial, eeg_only=True)
            #eeg_only=True, does not add CH0 as 'TRIGGER' where the markers are saved, this way you only get the data from pull chunk




    # open marker stream (only using LSL)
    if not self.lsl_marker_inlet:
        logger.debug('\n>>******Opening Marker stream******')
        #TIMEOUT to find EEG stream
        self.watchdog.reset()
        while self.watchdog.sec() < TIMEOUT and not self.lsl_marker_inlet:
            logger.warning('\n>>*****WAITING LSL MARKER STREAM: *****')
            # LSL
            if not self.lsl_marker_name:
                self.lsl_marker_name, self.lsl_marker_serial, self.lsl_marker_inlet = my.choose_lsl(streamtype="Markers")
            elif self.lsl_marker_name:
                self.lsl_marker_serial = "N/A"
                self.lsl_marker_inlet = my.return_stream_inlet(self.lsl_marker_name, streamtype='Markers', max_buflen=100, wait_time=0.01)

            #STOP
            if self.lsl_marker_inlet:
                break
            time.sleep(1)
        else:
            logger.error('\n>> ERROR : Timeout {}s occurred while acquiring data. MARKER stream bug?'.format(TIMEOUT))
            raise



    #UPDATE add additional markers
    if not self.lsl_addmarker_inlet:
        if self.lsl_addmarker_name: #only get additional if you provide the name
            logger.debug('\n>>******Opening Additional Marker stream******')
            #TIMEOUT to find EEG stream
            self.watchdog.reset()
            while self.watchdog.sec() < TIMEOUT and not self.lsl_addmarker_inlet:
                logger.warning('\n>>*****WAITING LSL MARKER STREAM: *****')
                # LSL
                self.lsl_addmarker_inlet = my.return_stream_inlet(self.lsl_marker_name, streamtype='Markers', wait_time=1.0)
                #STOP
                if self.lsl_addmarker_inlet:
                    break
                time.sleep(1)
            else:
                logger.error('\n>> ERROR : Timeout {}s occurred while acquiring data. Additional MARKER stream bug?'.format(TIMEOUT))
                raise



    #info EEG stream only affer server starts sending data
    if self.lsl_inlet:
        info = self.lsl_inlet.info()
        self.lsl_info_json={}
        try:
            xml=my.formatxml(info.as_xml())
            self.lsl_info_json=my.parseXmlToJson(xml)
        except:
            pass

        self.n_channels = info.channel_count()
        try:
            self.ch_names = my.lsl_channel_list(self.lsl_inlet)#UPDATE ADDED CH LIST
            self.channels = self.ch_names
        except:
            self.channels = ['Ch %i' % (i+1) for i in range(self.n_channels)]
        self.fs = info.nominal_srate()
        self.sampling_interval = 1 / self.fs #s
    if self.pycorder_rda_inlet:
        self.n_channels = self.pycorder_rda_inlet.channelCount
        try:
            self.ch_names = self.pycorder_rda_inlet.channelNames
            self.channels = self.ch_names
        except:
            self.channels = ['Ch %i' % (i+1) for i in range(self.n_channels)]
        self.sampling_interval = 1e-6*self.pycorder_rda_inlet.samplingInterval #us -> s
        self.fs = 1 / self.sampling_interval  #todo - make something like process_input

    #block get_data
    if self.block_time:
        self.block_size = int(max(self.block_time * self.fs, 5)) #samples
        #PATCH pycorder - worhing
        bs=self.block_size
        if self.pycorder_rda_inlet:
            def resetBuffers(self, block_size=bs):
                # string buffer for samples
                self.data_buffer = []
                # buffer sizes
                self.data_count = 0
                # calculate block size in samples for a 50ms block
                self.block_size = block_size#max(self.data.sample_rate * 0.05, 5)
            import types
            self.pycorder_rda_inlet.resetBuffers = types.MethodType(resetBuffers, self.pycorder_rda_inlet)
    else:
        self.block_size = None





    logger.debug('Initializing LSL time correction...') #it takes some time in the beginning - serves to estimate delay offset from the outlet
    if self.lsl_inlet: self.lsl_inlet.time_correction()
    if self.lsl_marker_inlet: self.lsl_marker_inlet.time_correction()
    if self.lsl_addmarker_inlet: self.lsl_addmarker_inlet.time_correction()#UPDATE


    logger.debug('\n>> Configuration done!')


def reconfigure(self, test_lsl_offset=False):
    self.configure(max_samples = self.max_samples,
                           get_data_sleeptime=self.get_data_sleeptime,
                           stream_type=self.stream_type,
                           stream_server=self.stream_server,
                           lsl_amp_name=self.lsl_amp_name,
                           lsl_marker_name=self.lsl_marker_name,
                           lsl_addmarker_name=self.lsl_addmarker_name,
                           lsl_save_buffers=self.lsl_save_buffers,
                           lsl_save_buffer_pycnbi=self.lsl_save_buffer_pycnbi,
                           block_time=self.block_time,
                           rda_amp_offset=self.rda_amp_offset,
                           lsl_amp_offset=self.lsl_amp_offset,
                           test_lsl_offset=test_lsl_offset,
                           lsl_marker_offset=self.lsl_marker_offset)



#2.START AMP: ampdecorator patch
def libmushu_ampdecorator_start(self, filename=None):
    modulename=libmushu.ampdecorator.__name__
    logger = logging.getLogger(modulename)
    logger.setLevel(logging_level)
    logger.debug("*****patch_libmushu_ampdecorator_start******")


    # 1.Prepare files for writing
    self.write_to_file = False
    if filename is not None:
        self.write_to_file = True
        filename_marker = filename + '.marker'
        filename_dat = filename + '.dat' #converted to .dat in myfunctions
        filename_meta = filename + '.meta'

        #UPDATE for BUFFERS - PASS this to driver
        filename_txt = filename + '.txt' #UPDATE SAVE IN TXT
        #UPDATE PYCNBI
        filename_pcl = filename + '_raw.pcl'
        filename_eve = filename + '_eve.txt'

        #test writability
        filedir=None
        try:
            #check filepath
            filedir, filenametype=os.path.split(filename) #dir where file is
            my.assure_path_exists(filedir)
            logger.info('>> Output filedir: %s' % (filedir))
            logger.info('>> Output filename: %s' % (filename))
            #check to not overwrite
            for filename in filename_marker, filename_dat, filename_meta, filename_txt, filename_pcl, filename_eve:
                if os.path.exists(filename):
                    logger.error('A file "%s" already exists, aborting.' % filename)
                    raise Exception
        except:
            raise RuntimeError('Problem writing to %s. Check permission.' % filename)

        #open file
        self.filedir=filedir
        self.fh_dat = open(filename_dat, 'wb')
        self.fh_marker = open(filename_marker, 'w')
        self.fh_meta = open(filename_meta, 'w', encoding="utf-8")

        try:#NOTE: driver specific
            if self.amp.lsl_save_buffers:
                #self.fh_txt = open(filename_txt, 'w')
                self.fh_pcl = open(filename_pcl, 'wb') #pickle object
                self.fh_eve = open(filename_eve, 'w')
        except:
            pass


        # write meta data  - json
        meta = {'Channels': self.amp.get_channels(),
                'Sampling Frequency': self.amp.get_sampling_frequency(),
                'Amp': str(self.amp),
                }
        try:
            meta['MANUAL_AMP_REF_CH']=self.amp.amp_ref_channels
            meta['lsl_info']=self.amp.lsl_info_json
        except:
            pass

        print(">> meta data:", meta)
        #UPDATE compatability to python 3 - https://stackoverflow.com/questions/36003023/json-dump-failing-with-must-be-unicode-not-str-typeerror
        self.fh_meta.write(unicode(json.dumps(meta, ensure_ascii=False)))
        #json.dump(meta, self.fh_meta, ensure_ascii=False, indent=4)

    """UPDATE REMOVED TCP SERVER(optional) - It uses a different process, so it does not interferes with the get_data() - use it if you want to send network markers - since processes don't share memory, Queue() is used to share data in producer/consumer pattern

    # start the marker server
    self.marker_queue = Queue()
    self.tcp_reader_running = Event()
    self.tcp_reader_running.set()
    tcp_reader_ready = Event()
    self.tcp_reader = Process(target=marker_reader,
                              args=(self.marker_queue,
                                    self.tcp_reader_running,
                                    tcp_reader_ready
                                    )
                              )
    self.tcp_reader.start()
    logger.debug('Waiting for marker server to become ready...')
    tcp_reader_ready.wait()
    logger.debug('Marker server is ready.')
    """

    #UPDATE Timer based on stream recorder - timer reset
    self.timer = my.Timer(autoreset=True)
    self.next_sec = 1
    # zero the sample counter
    self.received_samples = 0
    # 3.start the amp
    self.amp.start() #labstreaminglayer_start




def libmushu_labstreaminglayer_get_channels(self):
    """Get channel names.

    """
    return self.channels #UPDATE: you can also use self.ch_names - however be careful if your using CH # in some function




def libmushu_labstreaminglayer_start(self):
    """Open inlets and start buffers/QUEUEs - data needs to be temporarely saved before new push

    NOTE: Pycorder is implemented as a buffer and for now it gives all the samples in the buffer since last reset - it can overflow in the first get_data(). Because you don't have circular buffer #TODO

    LSL open_stream():
        All samples pushed in at the other end(server) from this moment onwards will be
        queued and eventually be delivered in response to pull_sample() or
        pull_chunk() calls.
        Throws a TimeoutError (if the timeout expires), or LostError (if the
        stream source has been lost).


    pull removes samples from buffer

    """
    modulename=libmushu.driver.labstreaminglayer.__name__
    logger = logging.getLogger(modulename)
    logger.setLevel(logging_level)


    #INIT vars
    self.ready = False #true when the start is valid

    self.received_samples=0 #reset sample counter

    #UPDATE - Buffers
    self.samples_buffer=[] #driver
    self.timestamps_buffer_ori=[] #original timestamps
    self.timestamps_buffer_tc=[] #time corrected timestamps
    self.tc_s_buffer=[] #time correction estimate from data block
    self.markers_buffer_ori=[]
    self.markers_buffer_tc=[]
    self.markers_buffer_mushu=[] #timestamps based on received_samples
    self.tc_m_buffer=[]
    self.received_samples_buffer=[] #received samples




    #UPDATE: ADD STREAM RECEIVER PYCNBI Reset buffer
    if self.lsl_inlet and self.lsl_save_buffer_pycnbi:
        self.sr.reset_buffer()

    ###VALIDATE STREAMS: Use to revalidate streams - After testing, it seams they are not needed after solving the problem of close stream
    #init
    stream_data_valid=False
    eeg_stream_valid=False
    marker_stream_valid=False
    restart_configure=False
    #options
    validate_offsets=self.validate_offsets #validate only offsets - #WARNING It opens streams queu, you need to reopen again after this
    validate_configure=self.validate_configure#Necessary because I still don't now how to restart queued data, unless configuring again
    validate_get_data=self.validate_get_data #use it if you want to buffer  before starting get_data and validate average stream offsets - #NOTE:Beware that this first data points will not be saved to file


    #VALIDATE STREAMs and OFFSETs
    if validate_offsets:
        #Reset possible buffer
        while not stream_data_valid:
            #check EEG stream
            if not eeg_stream_valid:
                if self.pycorder_rda_inlet and self.pycorder_rda_inlet.client_thread:
                    logger.warning('\n>> *****VALIDATING EEG RDA STREAM...(START BUTTON PYCORDER) ******')
                    if self.pycorder_rda_inlet.serverDataValid:#server data valid - needs to be clicked start button
                        eeg_stream_valid=True
                elif  self.lsl_inlet and self.lsl_amp_name:
                    logger.warning('\n>> *****VALIDATING EEG LSL STREAM... ******')
                    self.lsl_time_offset, eeg_stream_valid, restart_configure=my.test_lsl_inlet_offset(self.lsl_inlet, max_offset=self.max_offset, timeout=10)

                else: #something wrong in configure
                    #start again
                    restart_configure=True

            #check Marker Streams
            if not marker_stream_valid:
                if self.lsl_marker_inlet and self.lsl_marker_name:
                    logger.warning('\n>> *****VALIDATING MARKER LSL STREAM...******')

                    check_marker=False #TODO: not working -
                    if check_marker:
                        if self.lsl_marker_name.upper()=="pyffmarkerstream".upper():
                            marker_lsl_time_offset, marker_stream_valid, restart_configure=my.test_lsl_inlet_offset(self.lsl_marker_inlet, max_offset=self.max_offset)
                    else:
                        marker_stream_valid=True #other streams may forget to send marker when s.presentation inits - also for validation of stream you use open_stream() - NOTE:you could also double check for repeated streams
                else:
                    #something wrong in configure
                    #start again
                    restart_configure=True

            if eeg_stream_valid: logger.info('\n>> *****EEG STREAM VALID******')
            if marker_stream_valid: logger.info('\n>> *****MARKERS STREAMs VALID******')

            if eeg_stream_valid and marker_stream_valid:
                logger.warning('\n>> *****STREAMS VALID - STARTING EXPERIMENT ******')
                stream_data_valid=True
                break

            if restart_configure:
                break

            time.sleep(1)
        self.stop()

    if validate_configure:
        #reValidate Configuration (Reset streams) - the only solution right now to correctly restart the stream to prepare for opening again - test_lsl_offset=needs to be false to not open the stream before
        reconfigure(self, test_lsl_offset=False)

    #VALIDATE OPPENING STREAMS - Obligatory
    #Dont Reset the buffer(#WARNING it does not reset the buffer) - it also gives runtime errors if timeout is reach or the stream was deleted
    try:
        logger.info('\n>> Opening streams.')
        if self.lsl_inlet: self.lsl_inlet.open_stream(timeout=5)
        if self.lsl_marker_inlet: self.lsl_marker_inlet.open_stream(timeout=5)
        #UPDATE
        if self.lsl_addmarker_inlet: self.lsl_addmarker_inlet.open_stream(timeout=5)
        if self.pycorder_rda_inlet: self.pycorder_rda_inlet.stream_buffer=[] #reset
    except RuntimeError as e:
        logger.warning('\n>> Opening Streams INVALID, message: {}'.format(e))
        restart_configure=True
    except Exception as e:
        logger.warning('\n>> Opening Streams INVALID, message: {}'.format(e))
        restart_configure=True







    #VAlidate get_data
    #by getting Get winsec of initial data - GET samples and markers
    #Note does not work for marker - solution send initial
    if validate_get_data and self.add_buffer:
        winsec= 0.5 #s get_data of winsec
        winsize=int(max(winsec * self.fs, 5)) #samples
        try:
            logger.info('\n>> Waiting to fill initial buffer of length %d samples' % (winsize))
            good_offset=False
            while self.received_samples < winsize and not good_offset:
                self.get_data()

                #test offset
                if self.received_samples_buffer:
                    received_samples_buffer=np.array(self.received_samples_buffer)

                    samples_offset_mean = received_samples_buffer[:,-2].mean()#see below

                    if samples_offset_mean < self.max_offset:
                        good_offset=True
                    else:
                        good_offset=False
                        logger.error('\n>> OFFSET MEAN : {}'.format(samples_offset_mean))

                time.sleep(0.01) #10ms , appropriatte

            if not self.markers_buffer: logger.warning('No MARKER pulled from stream - maybe stream stop sending!')
            if not self.samples_buffer: raise RuntimeError('No SAMLES pulled from stream - it should have some samples')


        except Exception as e:
            logger.warning('\n>> Validating get_data INVALID, message: {}'.format(e))
            restart_configure=True




    if restart_configure:
        logger.warning('\n>> ******* STREAMS INVALID - RESTARTING CONFIGURE *******')
        reconfigure(self, test_lsl_offset=True)
        self.start()
        return

    self.ready = True

    self.pid=os.getpid() #process id
    if self.lsl_amp_name:
        logger.info('\n>> START RECEIVING DATA... \n>> STREAM: {} ; PID {})'.format(self.lsl_amp_name, self.pid)) #current process id
    else:
        logger.info('\n>> START RECEIVING DATA... \n>> STREAM_SERVER: {} ; PID {})'.format(self.stream_server, self.pid)) #current process id











#4.STOP AMP
def libmushu_ampdecorator_stop(self):
    modulename=libmushu.ampdecorator.__name__
    logger = logging.getLogger(modulename)
    logger.setLevel(logging_level)
    logger.debug("************patch_libmushu_ampdecorator_stop**********************")


    # stop the amp
    try:
        if self.amp.close_stream:
            self.amp.stop() #bug
            """
           pylsl.close_stream(): "All samples that are still buffered or in flight will be dropped and transmission and buffering of data for this inlet will be stopped.
            """
    except:
        pass


    """UPDATE REMOVED TCP
     # stop the marker server
    self.tcp_reader_running.clear()
    logger.debug('Waiting for marker server process to stop...')
    self.tcp_reader.join()
    logger.debug('Marker server process stopped.')
    """

    #UPDATE -Save Buffers
    try: #NOTE: Driver Specific - necessary because not every driver uses the vars below
        if self.amp.lsl_save_buffers and self.amp.add_buffer and not self.amp.lsl_save_buffer_pycnbi and self.write_to_file and self.amp.lsl_inlet  :
            logger.info('\n>> Stop requested. Copying buffers')

            #all buffers
            data = {'signals':self.amp.samples_buffer,
                    'timestamps': self.amp.timestamps_buffer_tc,
                    'events':self.amp.markers_buffer_tc,
                    'sample_rate':self.amp.fs,
                    'ch_number':self.amp.n_channels,#Number of channels w/ events
                    'ch_names':self.amp.ch_names, #names
                    'ch_names_server': self.amp.channels,#format can be the same as ch_names or 'CH' if not working
                    'manual_amp_ref': self.amp.amp_ref_channels,
                    'sample_interval': self.amp.sampling_interval,
                    'timestamps_ori': self.amp.timestamps_buffer_ori,
                    'tc_s': self.amp.tc_s_buffer,
                    'events_ori': self.amp.markers_buffer_ori,
                    'events_mushu':self.amp.markers_buffer_mushu,
                    'tc_m': self.amp.tc_m_buffer,
                    'received_samples_info': self.amp.received_samples_buffer,
                    'lsl_info': self.amp.lsl_info_json
                    }


            logger.info('\n>> Saving raw data ...')
            st =time.time()
            pickle.dump(data, self.fh_pcl, 2) #necessary to not open twice
            et =time.time() - st
            logger.info('\n>> TIME TO SAVE : {}s \n>>RAW Saved to {} \n'.format(et, self.fh_pcl.name))


            #Save envents to txt
            st =time.time()
            for m in self.amp.markers_buffer_tc:
                self.fh_eve.write('%.6f\t0\t%s\n' % (m[0], m[1]))
            et =time.time() - st
            logger.info('\n>> TIME TO SAVE : {}s \n>>EVENTS Saved to {}\n'.format( et, self.fh_eve.name))






        #UPDATE - STREAM RECORDER PYCNBI - Save recording
        if self.amp.lsl_save_buffers and self.amp.lsl_save_buffer_pycnbi and self.write_to_file and self.amp.lsl_inlet:
            # record stop
            logger.info('\n>> Stop requested. Copying buffer')
            buffers, times = self.amp.sr.get_buffer()
            signals = buffers
            events = None

            # channels = total channels from amp, including trigger channel
            data = {'signals':signals, 'timestamps':times, 'events':events,
                    'sample_rate':self.amp.sr.get_sample_rate(), 'channels':self.amp.sr.get_num_channels(),
                    'ch_names':self.amp.sr.get_channel_names()}
            logger.info('Saving raw data ...')
            import pycnbi.utils.q_common as qc
            filepath=self.fh_pcl.name
            qc.save_obj(filepath, data)
            logger.info('Saved to %s\n' % filepath)

            if os.path.exists(self.filename_eve):
                from pycnbi.utils.add_lsl_events import add_lsl_events
                add_lsl_events(self.filedir, interactive=False)
            else:
                logger.info('Converting raw file into a fif format.')
                from pycnbi.utils.convert2fif import pcl2fif
                pcl2fif(filepath)

    except Exception as e:
        logger.warning("\n>> Couldn't save buffers! \n>>1. Probably didn't start acquisition; \n>>2. Probably using a driver that was not patched, \n>>2.Or a missing attribute is not inside the function reconfigure() \n>>ERROR MSG : {}".format(e))
        pass

    # close the files
    if self.write_to_file:
        logger.info('\n>> Closing files.')
        for fh in self.fh_dat, self.fh_marker, self.fh_meta:
            fh.close()
        #update
        try:
            if self.amp.lsl_save_buffers:
                for fh in self.fh_pcl, self.fh_eve: #self.fh_txt
                    fh.close()
        except:
            pass


def libmushu_labstreaminglayer_stop(self):
    """Close inlets.

    Drop the current data stream.

    All samples that are still buffered or in flight will be dropped and
    transmission and buffering of data for this inlet will be stopped. If
    an application stops being interested in data from a source.

    """
    modulename=libmushu.driver.labstreaminglayer.__name__
    logger = logging.getLogger(modulename)
    logger.setLevel(logging_level)
    logger.info('\n>> Closing streams.')
    try:
        if self.lsl_inlet: self.lsl_inlet.close_stream()
        if self.lsl_marker_inlet: self.lsl_marker_inlet.close_stream()
        #UPDATE
        if self.lsl_addmarker_inlet: self.lsl_addmarker_inlet.close_stream()
        if self.pycorder_rda_inlet: self.pycorder_rda_inlet.stop()
    except Exception as e:
        logger.warning('\n>> Streams didnt close properly, message: {}'.format(e))
        pass




#3.GET_DATA FROM AMP:
def libmushu_ampdecorator_get_data(self):
    """Get data from the amplifier.

    This method is supposed to get called as fast as possible (i.e
    hundreds of times per seconds) and returns the data and the
    markers.

    Returns
    -------
    data : 2darray
        a numpy array (time, channels) of the EEG data
    markers : list of (float, str)
        a list of markers. Each element is a tuple of timestamp and
        string. The timestamp is the time in ms relative to the
        onset of the block of data. Note that negative values are
        *allowed* as well as values bigger than the length of the
        block of data returned. That is to be interpreted as a
        marker from the last block and a marker for a future block
        respectively.

    """
    # get data and marker from underlying amp
    data, marker = self.amp.get_data()

    t = time.time()
    # length in sec of the new block according to #samples and fs
    block_duration = len(data) / self.amp.get_sampling_frequency()
    # abs time of start of the block
    t0 = t - block_duration
    # duration of all blocks in ms except the current one
    duration = 1000 * self.received_samples / self.amp.get_sampling_frequency()

    #UPDATE - True duration uses the timestamps instead of received_samples - however should not be used
#    try:
#        if self.amp.add_buffer and self.amp.true_duration:
#            duration=self.amp.true_duration #ms
#    except:
#        pass
#


    """UPDATE
    # merge markers
    tcp_marker = []
    while not self.marker_queue.empty():
        m = self.marker_queue.get()
        m[0] = (m[0] - t0) * 1000
        tcp_marker.append(m)
    marker = sorted(marker + tcp_marker)
    """


    # save data to files
    if self.write_to_file:
        for m in marker:
            self.fh_marker.write("%f %s\n" % (duration + m[0], m[1])) #absolute markers using the received files
        self.fh_dat.write(struct.pack("f"*data.size, *data.flatten())) #The EEG data is saved in binary form. Since the number- and ordering of EEG channels is fixed during a recording, we can write the values for each channel sample-wise to disk

        #UPDATE
        #self.fh_txt.write("SAMPLE_STAMP:{}\nSAMPLE_LENGTH:{}\nSAMPLE_MUSHU:{}\nSAMPLE_PYLSL:{}\nMARKERS:{}\n\n".format(timestamps,len(samples),samples,samples_inlet,marker) )

    self.received_samples += len(data)
    if len(data) == 0 and len(marker) > 0:
        logger.error('Received marker but no data. This is an error, the amp should block on get_data until data is available. Marker timestamps will be unreliable.')

    #data:numpy[samples, channels]; marker: list[[timestamps, marker_name], []]
    return data, marker




def libmushu_labstreaminglayer_get_data(self):
    """Receive a chunk of data an markers.

    Returns
    -------
    chunk, markers: Markers is time in ms since relative to the
    first sample of that block.

    """
    modulename=libmushu.ampdecorator.__name__
    logger = logging.getLogger(modulename)
    logger.setLevel(logging_level)
    #logger.debug("*******patch_libmushu_ampdecorator_get_data******")

    #reset
    data, marker, current_amp_offset, server_timestamp, local_timestamp = [],[],[],[],[]

    fs=self.get_sampling_frequency()


    #STREAM TIME CORRECTIONS
    #ESTIMATION of offet between inlet and outlet?? - to map  to current local clock in this machine, or to map to LSL lib clock??
    #time corresponds to first block sample t0
    tc_s=0 #s amp->server??
    tc_m=0 #s marker server-> ??
    tc_addm=0 #s addmarker server->
    #EEG
    if self.lsl_inlet:
        tc_s = self.lsl_inlet.time_correction() #amp offset
        if self.lsl_amp_offset: tc_s = self.lsl_amp_offset # NOTE: this is only correct if you

    if self.pycorder_rda_inlet: tc_s = -1*(self.rda_amp_offset) #amp offset amp->server->client (use to subtract)
    #Markers
    tc_m = self.lsl_marker_inlet.time_correction()#marker offset
    if self.lsl_addmarker_inlet: tc_addm =self.lsl_addmarker_inlet.time_correction()#addmarker offset

    #MARKERS ***************

    markers, m_timestamps = self.lsl_marker_inlet.pull_chunk(timeout=0.0, max_samples=self.max_samples)
    # flatten the output of the lsl markers, which has the form
    # [[m1], [m2]], and convert to string
    markers = [str(i) for sublist in markers for i in sublist]
    if self.lsl_addmarker_inlet:
        addmarkers, addm_timestamps = self.lsl_addmarker_inlet.pull_chunk(timeout=0.0, max_samples=self.max_samples)
        addmarkers = [str(i) for sublist in addmarkers for i in sublist]


    #DATA ***************

    self.watchdog.reset()
    timestamps = []
    data_count = 0
    if self.block_size: #block until certain size
        block_samples_buffer = []
        block_ts_buffer = []
        logger.info("\n>> Block Size: {}".format(self.block_size))

    #LOOP TIMEOUT #Block FUNCTIONS with timeout
    timeout= 10 #s  or use self.inlet_max_buflen
    while self.watchdog.sec() < timeout:

        #UPDATE - PYCORDER RDA , pycorder rda server, default: resolutions=uV, single precision float32
        if self.pycorder_rda_inlet and self.lsl_marker_inlet:
            #DATA - block function
            block_size = self.pycorder_rda_inlet.block_size #patch in configure
            if self.block_size: assert self.block_size == block_size
            logger.debug("Waiting for data to be available...")
            while not self.pycorder_rda_inlet.dataavailable:
                logger.debug("\n>> rda data_count: {}".format(self.pycorder_rda_inlet.data_count))
            local_timestamp=pylsl.local_clock()#s #ts of last sample of this block
            data_rda_d = self.pycorder_rda_inlet.data #format: dict object #NOTE: Assumes constant samplingInterval= 1.0e6 / data.sample_rate     # sampling interval in us; #format: numpy [channels][samples] with resolutions
            data_rda_buffer = np.array(self.pycorder_rda_inlet.stream_buffer)#push data since last_reset amp.start(); stream_buffer is an extended list of [samples][channels]
            self.pycorder_rda_inlet.stream_buffer=[]#reset
            """
            WARNING: Received samples vary, even using block_time, don't know if the stream buffer is working correctly. If working correctly, alot of samples are missed using the block while above
            #CHECK , If using the rda, do test please...
            """
            samples_inlet=data_rda_buffer#format: numpy [samples][channels] with resolutions
            samples=samples_inlet#format: numpy[samples, channels]
            #recontruct timestamps from local timestamp
            t0=local_timestamp-block_size/fs #1.local lsl timestamp t0 of rda arrival
            if len(samples)>0:
                timestamps=[t0+(i/fs) for i in range(block_size)]
            server_timestamp = local_timestamp - self.rda_amp_offset #it's an aproximation - because we can't measure it - unless we patch pycorder

            #TODO
            markers_rda_d = data_rda_d.markers #format: dict object - they are in absolute position - you need to put in relative position
            #marker = sorted (marker + markers_rda)




         #UPDATE - STREAM RECEIVER PYCNBI -  Actichamp lsl App: resolutions=uV, , single precision float32 (however SR has multiplier variable if you want to change,default=1 so the resolutions stays in uV)
        if self.lsl_inlet and self.lsl_marker_inlet and self.lsl_save_buffer_pycnbi:
            #DATA - block function
            #FROM STREAM REVEIVER - eeg_only=false, therefore CH0 is not the trigger
            #pull_chunk() block_size=1024 samples:(e.g. 1000hz samples take 1.024 s to acquire, so 1024 ms to update) - for 1000 hz -> block_time=1024ms - block_size constant
            samples_inlet, timestamps =self.sr.acquire()#format: numpy [samples][channels]
            local_timestamp=pylsl.local_clock()#s #ts of last sample of this block
            if len(timestamps)>0: server_timestamp = timestamps[-1]
            samples=samples_inlet##format: numpy[samples, channels]
            #samples=samples_lsl_pycnbi.reshape(-1, self.n_channels)##format: numpy [channels][samples] -
            tc_s_sr=self.sr.lsl_time_offset
            print('time_correction: %s, pycnbi_sr_lsl_offset: %s, ' % (tc_s,tc_s_sr))
            if self.sr.get_buflen() > self.next_sec:
                duration = str(datetime.timedelta(seconds=int(self.sr.get_buflen())))
                print('RECORDING %s' % duration)
                self.next_sec += 1
            #self.timer.sleep_atleast(0.01)


        #UPDATE - OLD mushu type of saving -  Actichamp lsl App - resolutions=uV , single precision float32
        if self.lsl_inlet and self.lsl_marker_inlet and not self.lsl_save_buffer_pycnbi:
            # get data and marker from underlying amp
            """UPDATE - instead of self.get_data() from libmushu.driver.labstreaminglayer pass all through here"""
            #DATA
            #pull_chunk(max_samples=self.max_samples) block_size=1024 samples:(e.g. 1000hz samples take 1.024 s to acquire, so 1024 ms to update) - for 1000 hz -> block_time=1024ms - block_size constant
            samples_inlet, timestamps = self.lsl_inlet.pull_chunk(timeout=0.0, max_samples=self.max_samples) #format: list [samples][channels]
            local_timestamp=pylsl.local_clock()#s #ts of last sample of this block
            if len(timestamps)>0: server_timestamp = timestamps[-1]
            samples = np.array(samples_inlet) #format:numpy[samples, channels]
            #samples = np.array(samples_lsl).reshape(-1, self.n_channels)  #UPDATE reshape(-1, self.n_channels)- if n_channels<len(chanaxis), it removes the channel and reshapes with more samples, if n_channels=len(chanaxis) does noting and if > gives error - MAKES NO SENSE FOR ME


        if len(timestamps)>0:# block until we actually have data
            data_count +=len(samples)
            if self.block_size : #wait to reach block_size
                block_samples_buffer.extend(samples.tolist())
                block_ts_buffer.extend(timestamps)
                if data_count>=self.block_size:
                    samples=np.array(block_samples_buffer)
                    timestamps=block_ts_buffer
                    break
            else:
                break

        #sleep time
        if self.get_data_sleeptime: time.sleep(self.get_data_sleeptime)

    else:
        logger.error('\n>> Timeout {}s occurred while acquiring data. Amp driver bug? Probably battery issues!'.format(timeout))
        raise RuntimeError('\n>> Timeout {}s occurred while acquiring data. Amp driver bug? Probably battery issues!'.format(timeout))
#        data=np.zeros((0, self.n_channels))
#        marker=[]
#        return data, marker


    # AMP offset - using last sample of block
    current_amp_offset = local_timestamp - server_timestamp

    # CORRECT MARKER TIMESTAMPS(tranform marker timstamp to relative, s->ms) based on first samples chunck timestamp - then use received sample number to put to local absolute
    #CHECK , LSL tc are negative??Why??are they relative to original time from the network??
    ori_m_timestamps= m_timestamps
    ori_timestamps=timestamps
    t0 = ori_timestamps[0] + tc_s #s #data block t0; LSL format: seconds
    m_timestamps = [(i + tc_m - t0) * 1000 for i in m_timestamps]#ms #relative

    data, marker = samples, list(zip(m_timestamps, markers))#UPDATE: Python 3 don't automatically pass zip to list
    #data format

    #UPDATE
    if self.lsl_addmarker_inlet:
        addm_timestamps = [(i + tc_addm - t0) * 1000 for i in addm_timestamps] #transform to relative
        addmarker=list(zip(addm_timestamps, addmarkers))#UPDATE: Python 3 don't suport zip operations
        marker = sorted(marker + addmarker)



    # duration of all blocks in ms except the current one
    self.duration = 1000 * self.received_samples / fs #ms #assuming constant timestamps - assuming no missing values


    #UPDATE - Absolute sample position - sample resolution 1/fs (1000Hz = 1ms resolution) - absolute
    m_indice = [round(self.received_samples + (m[0]*fs)/1000.)  for m in marker]
    list_markers=list(zip(marker+m_indice)) #have to zip(tc_m)

    #update received_samples
    self.received_samples += len(data)

    ## add data to buffer
    if self.add_buffer:
        #data
        block = data.tolist() #data is numpy array
        self.samples_buffer.extend(block) #list
        self.timestamps_buffer_ori.extend(list(ori_timestamps))
        tc_timestamps= [(i + tc_s ) for i in ori_timestamps] #s, time corrected timestamps
        self.timestamps_buffer_tc.extend(list(tc_timestamps)) #NOTE:absolute timestamps
        self.tc_s_buffer.append(tc_s) #tc_s float

        #True duration - duration based on timestamps
        t_1st_sample=self.timestamps_buffer_ori[0]+self.tc_s_buffer[0]#s
        t_current_block=t0#s
        self.true_duration=(t_current_block-t_1st_sample) *1000#ms

        #markers
        self.markers_buffer_ori.extend(list(zip(ori_m_timestamps, markers))) #s
        tc_m_timestamps= [(i + tc_m ) for i in ori_m_timestamps] #s, time corrected timestamps
        self.markers_buffer_tc.extend(list(zip(tc_m_timestamps, markers))) #s , NOTE:absolute timestamps
        abs_marker=[(self.duration+m[0], m[1]) for m in marker] #ms, absolute_marker - because buffer block initial time is the biginning
        self.markers_buffer_mushu.extend(abs_marker) #ms,  NOTE: The markers timestamps need to be absolute - there is no way to calculate aftwards from relative
        self.tc_m_buffer.append(tc_s) #float

        #received samples - present
        rs=list(zip([len(data)] , [self.received_samples], [current_amp_offset]))
        if self.lsl_inlet: rs=list(zip([len(data)] , [self.received_samples], [current_amp_offset], [tc_s]))
        self.received_samples_buffer.extend(rs) #list

        #tru


        #Check for presentation markers
        timeout=60*3 #s
        if self.received_samples/self.fs > timeout and not self.markers_buffer_ori:
            logger.error('\n>> Timeout {}s occurred. No marker in the task, buffer:{}. Marker stream bug, possibly more than one marker stream, or the subject didnt start the task?'.format(timeout, self.markers_buffer_ori))
            if self.check_for_markers: raise AssertionError('\n>> Timeout {}s occurred. No marker in the task, buffer:{}. Marker stream bug, possibly more than one marker stream, or the subject didnt start the task?'.format(timeout, self.markers_buffer_ori))
            pass


    #data:numpy[samples, channels]; marker: list[[relative_timestamps, marker_name], []]
    #NOTE: timestamps are relative to this block of data
    return data, marker




#driver patch fot replayamp #You can also use stream_
def libmushu_replayamp_get_data(self):
    """

    Returns
    -------
    chunk, markers: Markers is time in ms since relative to the
    first sample of that block.

    """
    if self.realtime:
        elapsed = time.time() - self.last_sample_time
        blocks = (self.fs * elapsed) // self.samples
        """UPDATE SAMPLEST TO INT"""
        logger.debug("#BUG #SOLVED REPLAYAMP Realtime - Not Working because of float//int devision yelds float - PATCHING solved by changing to int(samples)")
        logger.debug(" blocksize_samples : int - blocksize in samples")
        samples = int(blocks * self.samples)
    else:
        samples = self.samples
    elapsed = samples / self.fs
    self.last_sample_time += elapsed
    # data
    chunk = self.data[self.pos:self.pos+samples]
    #self.data = self.data[samples:]
    # markers

    # slow python version
    #markers = [x for x in self.marker if x[0] < elapsed * 1000]
    #self.marker = [x for x in self.marker if x[0] >= elapsed * 1000]
    #self.marker = [[x[0] - elapsed * 1000, x[1]] for x in self.marker]

    # fast numpy version
    mask = self.marker_ts < (elapsed * 1000)
    markers = list(zip(self.marker_ts[mask], self.marker_s[mask]))#update python 3 style
    self.marker_ts = self.marker_ts[~mask]
    self.marker_s = self.marker_s[~mask]
    self.marker_ts -= elapsed * 1000

    self.pos += samples
    return chunk, markers



















"""
********PATCHING**************
"""


import libmushu
"""PATCHING MODULE"""
"""PATCHING CLASS METHODS
Can be done directly before initing the class
"""
#patch ampdecorator
libmushu.AmpDecorator.start = libmushu_ampdecorator_start
libmushu.AmpDecorator.stop = libmushu_ampdecorator_stop
libmushu.AmpDecorator.get_data = libmushu_ampdecorator_get_data # for now nothing changed
#patch lslamp
from libmushu.driver.labstreaminglayer import LSLAmp
libmushu.driver.labstreaminglayer.LSLAmp.configure=libmushu_labstreaminglayer_configure
libmushu.driver.labstreaminglayer.LSLAmp.start=libmushu_labstreaminglayer_start
libmushu.driver.labstreaminglayer.LSLAmp.stop=libmushu_labstreaminglayer_stop
libmushu.driver.labstreaminglayer.LSLAmp.get_data = libmushu_labstreaminglayer_get_data
libmushu.driver.labstreaminglayer.LSLAmp.get_channels=libmushu_labstreaminglayer_get_channels
#patch replayamp
from libmushu.driver.replayamp import ReplayAmp
libmushu.driver.replayamp.ReplayAmp.get_data=libmushu_replayamp_get_data





"""
FAQS:

***PATCHING OBJECT METHODS***
Solution for methods that can't be changed directly, need to be patch after initing the class in the script
e.g methods that are not directly visible on the module because they are only imported afterwards:
#libmushu.driver.labstreaminglayer.LSLAmp.configure=libmushu_labstreaminglayer_configure - DONT WORK
#libmushu.driver.replayamp.ReplayAmp.get_data=libmushu_replayamp_get_data

  OR

  AS you can see above, using from and import works fine to patch as it seems


  Thefore this new version of patching is more simple and tidy :)


***PATCHING FUNCTIONS***

HOW TO USE THEM
PATCHING CLASSES METHODS - Change class methods
-Need to call the class then using it, e.g.:
    class Dog:
        def bark(self):
            print 'Woof!'
    def newbark(self):
        print 'Wrooof!'
    # Replace an existing method
    Dog.bark = newbark

Or(they function the two ways)

PATCHING OBJECTS METHODS - change  methods on the fly after initiation of the class
- After calling the class, e.g:
    def herd(self, sheep):
        self.run()
        self.bark()
        self.run()
    import types
    border_collie = Dog()
    border_collie.herd  = types.MethodType(herd, border_collie)


"""

