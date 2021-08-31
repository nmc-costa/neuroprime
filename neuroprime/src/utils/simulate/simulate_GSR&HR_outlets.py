#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Mon Jul 15 12:07:59 2019

@author: nm.costa
"""
from __future__ import (absolute_import, division, print_function)
#from builtins import * #all the standard builtins python 3 style

import time
import numpy as np
from scipy import signal

from pylsl import StreamInfo, StreamOutlet, local_clock


stream_type='GSR'
sampleRate = 1 #Hz - gsr_value calculated from 100 Hz
channel_number = 5
info_gsr = StreamInfo('GSR', stream_type, channel_number, sampleRate, 'float32', 'gsr123')
# append some meta-data
chns = info_gsr.desc().append_child("channels")
design= ['flags','counter_gsr', 'gsr_lsb', 'gsr_msb', 'gsr_value']
assert channel_number ==len(design)
for label in design:
    ch = chns.append_child("channel")
    ch.append_child_value("label", label)
    ch.append_child_value("unit", "#")
    ch.append_child_value("type", stream_type)
info_gsr.desc().append_child_value("manufacturer", "Mind Prober")

# next make an outlet; we set the transmission chunk size to 1 samples and
# the outgoing buffer size to 360 seconds (max.)
outlet_gsr = StreamOutlet(info_gsr, chunk_size=0, max_buffered=360)


stream_type='HR'
sampleRate = 1 #Hz - gsr_value calculated from 100 Hz
channel_number = 6
info_hr = StreamInfo('HR', stream_type, channel_number, sampleRate, 'float32', 'hr123')
# append some meta-data
chns = info_hr.desc().append_child("channels")
design= ['flags','counter_hr', 'bpm_value', 'rr_lsb', 'rr_msb', 'rr_value']
assert channel_number ==len(design)
for label in design:
    ch = chns.append_child("channel")
    ch.append_child_value("label", label)
    ch.append_child_value("unit", "#")
    ch.append_child_value("type", stream_type)
info_hr.desc().append_child_value("manufacturer", "Mind Prober")

outlet_hr = StreamOutlet(info_hr, chunk_size=0, max_buffered=360)


print("now sending data ...")
start_time=local_clock() #s
counter_time=start_time #s
elapsed_time=local_clock()-start_time #s
counter_marker_number=0
sample_counter=0
stop_outlet=10000000 #float('inf')#marker_step*1000 #s

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
    y1 = A * np.sin(2 * np.pi * f * x / Fs)  #random: np.array( random.random()); sine: np.sin(2 * np.pi * f * x / Fs); square: A * signal.square(2 * np.pi * f * x / Fs)
    A=50
    f = 0.1
    y2 = A * np.sin(2 * np.pi * f * x / Fs)

    A=60
    f = 1
    y3 = A * np.sin(2 * np.pi * f * x / Fs)



    # now send it
    flags, counter_gsr, gsr_lsb, gsr_msb, gsr_value=01, sample_counter, y1,y2,y1*255 + y2
    sample=[flags, counter_gsr, gsr_lsb, gsr_msb, gsr_value]
    outlet_gsr.push_sample(sample, sample_stamp[0])
    flags,counter_hr, bpm_value, rr_lsb, rr_msb, rr_value= 1, sample_counter,y3, y1,y2,y1*255 + y2
    sample=[flags,counter_hr, bpm_value, rr_lsb, rr_msb, rr_value]
    outlet_hr.push_sample(sample, sample_stamp[0])

    sample_counter+=1
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
outlet_gsr.__del__
outlet_hr.__del__
