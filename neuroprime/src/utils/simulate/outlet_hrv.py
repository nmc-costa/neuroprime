#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Tue Jul  2 10:51:03 2019

@author: nm.costa
"""
from __future__ import (absolute_import, division, print_function)
#from builtins import * #all the standard builtins python 3 style

import time
import numpy as np
from scipy import signal

from pylsl import StreamInfo, StreamOutlet, local_clock

sampleRate = 100
channel_number = 2
stream_type='HRV'
info = StreamInfo('HRV', stream_type, channel_number, sampleRate, 'float32', 'hrv123')

# append some meta-data
chns = info.desc().append_child("channels")
design= ['left', 'right']
assert channel_number ==len(design)
for label in design:
    ch = chns.append_child("channel")
    ch.append_child_value("label", label)
    ch.append_child_value("unit", "microvolts")
    ch.append_child_value("type", stream_type)
info.desc().append_child_value("manufacturer", "Mind Prober")

# next make an outlet; we set the transmission chunk size to 10 samples and
# the outgoing buffer size to 360 seconds (max.)
outlet = StreamOutlet(info, 10, 360)


print("now sending data ...")
start_time=local_clock() #s
counter_time=start_time #s
elapsed_time=local_clock()-start_time #s
counter_marker_number=0
sample_counter=0
stop_outlet=1000 #float('inf')#marker_step*1000 #s

while elapsed_time<=stop_outlet:

    start_loop=local_clock()
    """
    DATA
    """
    # get a time stamp in seconds (we pretend that our samples are actually
    sample_stamp = [local_clock()] #don't correct for the possible hardware delay - because it is constant

    # make a new  sample; this is converted into a pylsl.vectorf (the data type that is expected by push_sample)
    Fs = sampleRate # amp sample rate
    f = 0.2 #hz - signal freq - 1 Beat/s = 60 BPM, however HRV is more in the 0.2Hz
    A=100 #amplitude  - JUST to HAVE some understandable numbers
    x=sample_counter
    y = A * np.sin(2 * np.pi * f * x / Fs)  #random: np.array( random.random()); sine: np.sin(2 * np.pi * f * x / Fs); square: A * signal.square(2 * np.pi * f * x / Fs)
    sample_counter+=1
    sample=[]
    for i in range(channel_number):#same for all chs
        sample.append(y.tolist())


    # now send it
    outlet.push_sample(sample, sample_stamp[0])
    print('**********************OUTLET_DATA*******************')
    print('STAMP:'+str(sample_stamp))
    print('SAMPLE:'+str(sample))
    
    
    """
    Time simulate
    """
    #wait the same time as the sample rate before next iteration, to send  next sample
    end_loop_elapsed=local_clock()-start_loop
    if end_loop_elapsed<1/float(sampleRate):
        time.sleep((1/float(sampleRate))-end_loop_elapsed)

    elapsed_time=local_clock()-start_time



#DESTROY OUTLETS
    #this throws errors in inlet
    #Without destroy the stream is alive but not sending data
outlet.__del__
