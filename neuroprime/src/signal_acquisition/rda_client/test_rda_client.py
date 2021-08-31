# -*- coding: utf-8 -*-
"""
Created on Wed Apr 24 11:05:33 2019

@author: nm.costa
"""
from __future__ import print_function, division






import logging
logging.basicConfig(level=logging.DEBUG) #use to get all imported loggers

import time
import pylsl
import numpy


# STOP While after x iterations
STOP_COUNTER = 100


#TEST simple RDA performance
import simple_rda_client as RDA
simple_elapsed_time_a, simple_elapsed_time_a_lsl=RDA.main(stop_counter=STOP_COUNTER)



#TEST pycorder RDA performance
from pycorder_rda_client_nogui import RDA_Client
RDA = RDA_Client()

#default values
RDA.HOST = 'localhost'
RDA.PORT = 51244           #: 32-Bit data port
RDA.ADDR = (RDA.HOST, RDA.PORT)

RDA.connectClient()

counter = 0
previous_time=time.time()
previous_time_lsl=pylsl.local_clock()
elapsed_time_a=[]
elapsed_time_a_lsl=[]
while RDA.client_thread_running and counter<STOP_COUNTER:
    counter+=1
    current_time = time.time()
    current_time_lsl = pylsl.local_clock()
    elapsed_time=current_time-previous_time
    elapsed_time_lsl=current_time_lsl-previous_time_lsl
    previous_time = current_time
    previous_time_lsl = current_time_lsl
    print("local time:{}".format(current_time))
    print("local time LSL:{}".format(current_time_lsl))
    print("elapsed time:{}".format(elapsed_time))
    print("elapsed time LSL:{}".format(elapsed_time_lsl))
    print("RDA.data.eeg_channels: {}".format(RDA.data.eeg_channels))
    elapsed_time_a.append(elapsed_time)
    elapsed_time_a_lsl.append(elapsed_time_lsl)

RDA.disconnectClient()
elapsed_time_a=numpy.array(elapsed_time_a)
elapsed_time_a_lsl=numpy.array(elapsed_time_a_lsl)


print("Simple Average elapsed, time.time():{} ; pylsl.local_clock:{}".format(simple_elapsed_time_a.mean(), simple_elapsed_time_a_lsl.mean() ))
print("Average elapsed, time.time():{} ; pylsl.local_clock:{}".format(elapsed_time_a.mean(), elapsed_time_a_lsl.mean() ))
