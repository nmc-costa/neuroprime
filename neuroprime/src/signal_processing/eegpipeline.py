# -*- coding: utf-8 -*-
"""
Created on Sun Jun 17 16:29:25 2018

POSSIBLE PIPELINE
    0.SET variables->init()
    1.Load continuous data ->input_data() 
        1.1Choose Channels to process:
        1.2.Choose Data interval:
    2.Preprocessing->preprocessing()
        2.1Filter:
        2.2Subsample:
    3.Processing->processing()
        3.1 Remove noisy Channels:
        3.2 AVERAGE reference:
        3.3 ICA:
        3.4 Segmentation Epochs
        3.5 Remove baseline
        3.6 Artifact detection/rejection
        3.7 PSD:
            3.7.1 FFT resolution
            3.7.2 hanning window with variance correction
        3.8 Alpha Peak detection - Identify the IAF(individual Alpha frequency)
        3.9 BANDS
        3.10 Thresholds
            reward threshold: mean of SMR power during rest state of 1s window ;
            inhibit threshold: mean + 1 SD of theta or beta power during rest state of Fz
    4.Post_processing->postprocessing()
        If you need to organize something before outputing the data.
        It calls output_data()
    5.Output data->output_data()



@author: nm.costa
"""
#import eegfunctions
#import myfunctions as my
import logging
logger = logging.getLogger(__name__)
logger.info('Logger started')


class eegpipeline(object):
    def __init__(self):
#        logger.debug("#BUG #SOLVED - self cant have thread.lock objects like the logger from other class")
#        logger.debug("#TODO - use this base pipeline to put basic pipeline stuff")
        pass


    def init(self):
        "INIT VARS"
        pass

    def input_data():
        "INPORT/LOAD DATA"
        pass


    def preprocessing():
        "PREPROCESS DATA"
        pass

    def processing():
        "PROCESS DATA"
        pass

    def postprocessing():
        "RESULTS PROCESSING"
        pass
    
    def output_data():
        "EXPORT DATA"
        pass


if __name__=="__main__":
    pass
