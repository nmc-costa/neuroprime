#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Wed Dec  6 10:10:29 2017

Script:
    Simulation of actichamp amplifier
    Multichannel time series
    Meta-data LSL

acticap_10_20_new_design_uol = ['Fp1', 'Fz', 'F3', 'F7', 'FT9', 'FC5', 'FC1', 'C3','T7','TP9', 'CP5', 'CP1', 'Pz', 'P3', 'P7', 'O1', 'Oz', 'O2', 'P4', 'P8', 'TP10', 'CP6','CP2', 'Cz','C4', 'T8', 'FT10', 'FC6','FC2', 'F4', 'F8','Fp2']

@author: nm.costa
"""
from __future__ import (absolute_import, division, print_function)
#from builtins import * #all the standard builtins python 3 style #unicode pylsl problem

import os
import random
import time
import numpy as np
from scipy import signal
from pylsl import StreamInfo, StreamOutlet, local_clock

from outlet_actichamp_save import save_outlet

# My functions
#import neuroprime.src.utils.myfunctions as my
#import logging
#logging_level=logging.DEBUG
#logger = my.setlogfile(modulename=__name__, setlevel=logging_level, disabled=True)
"""
-------------------------------------------------------------------------------
EEG data
-------------------------------------------------------------------------------
"""

# first create a new stream info (here we set the name to ActiChamp,
# the content-type to EEG, 32 channels, 500 Hz, and float-valued data) The
# last value would be the serial number of the device or some other more or
# less locally unique identifier for the stream as far as available (you
# could also omit it but interrupted connections wouldn't auto-recover).
sampleRate = 1000
channel_number = 32
info = StreamInfo('Actichamp-0', 'EEG', channel_number, sampleRate, 'float32', 'myuid2424')

# append some meta-data
chns = info.desc().append_child("channels")
acticap_10_20_new_design_uol = ['Fp1', 'Fz', 'F3', 'F7', 'FT9', 'FC5', 'FC1', 'C3','T7','TP9', 'CP5', 'CP1', 'Pz', 'P3', 'P7', 'O1', 'Oz', 'O2', 'P4', 'P8', 'TP10', 'CP6','CP2', 'Cz','C4', 'T8', 'FT10', 'FC6','FC2', 'F4', 'F8','Fp2']
for label in acticap_10_20_new_design_uol:
    ch = chns.append_child("channel")
    ch.append_child_value("label", label)
    ch.append_child_value("unit", "microvolts")
    ch.append_child_value("type", "EEG")
info.desc().append_child_value("manufacturer", "Brain Products")
cap = info.desc().append_child("cap")
cap.append_child_value("name", "ACTICAP_CMA_32_NO_REF")
cap.append_child_value("size", str(channel_number))
cap.append_child_value("labelscheme", "10-20")


# next make an outlet; we set the transmission chunk size to 10 samples and
# the outgoing buffer size to 360 seconds (max.)
outlet = StreamOutlet(info, 10, 360)




"""
-------------------------------------------------------------------------------
Markers
-------------------------------------------------------------------------------
"""
# first create a new stream info (here we set the name to MyMarkerStream,
# the content-type to Markers, 1 channel,
# and string-valued data) The last value would be the locally unique
# identifier for the stream as far as available, e.g.
# program-scriptname-subjectnumber (you could also omit it but interrupted
# connections wouldn't auto-recover). The important part is that the
# content-type is set to 'Markers', because then other programs will know how
#  to interpret the content
infoMARKER = StreamInfo('Actichamp-markers', 'Markers', 1, 0, 'string', 'myuidw43536')

# next make an outlet
outletMARKER = StreamOutlet(infoMARKER)
#markernames = ['Actichamp-M1', 'Actichamp-M2', 'Actichamp-M3', 'Actichamp-M4', 'Actichamp-M5', 'Actichamp-M6']









"""
-------------------------------------------------------------------------------
Sending ...
-------------------------------------------------------------------------------
"""



#Saving configuration
SAVE =False
if SAVE:
    save=save_outlet()
    save.configure(channel_number=channel_number,fs=sampleRate)
    file_name='outlet_data_'+time.strftime("%d%m%Y") + '_' + time.strftime("%Hh%Mm")
    filedir='C:/Users/admin.DDIAS4/Desktop/e1_data_debug'#'/Users/nm.costa/Desktop/e1_data_debug'#'C:/Users/admin.DDIAS4/Desktop/e1_data_debug'
    filepath=os.path.join(filedir,file_name)
    save.start(filename=filepath)

print("now sending data ...")
start_time=local_clock() #s
counter_time=start_time #s
marker_step=1 #s
elapsed_time=local_clock()-start_time #s
counter_marker_number=0
sample_counter=0
stop_outlet=marker_step*1000#float('inf')#marker_step*1000 #s

while elapsed_time<=stop_outlet:

    start_loop=local_clock()
    """
    DATA
    """
    # get a time stamp in seconds (we pretend that our samples are actually
    # 125ms old, e.g., as if coming from some external hardware),
    #BUG: NOT a good IDEA - because the client stamp is measured against this value, if you want to correct, do that in the client #Incorrect: sample_stamp = [local_clock()-0.125]
    sample_stamp = [local_clock()] #don't correct for the possible hardware delay - because it is constant

    # make a new random 8-channel sample; this is converted into a
    # pylsl.vectorf (the data type that is expected by push_sample)

    Fs = sampleRate # amp sample rate
    f = 10 #sine alpha hz
    A=100 #JUST to HAVE some understandable numbers
    x=sample_counter
    y = A * np.sin(2 * np.pi * f * x / Fs) #random: np.array( random.random()); sine: np.sin(2 * np.pi * f * x / Fs); signal.square(2 * np.pi * f * x / Fs)
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
    Markers
    """
    elapsed_counter=local_clock()-counter_time
    marker=[]
    marker_stamp=[]
    if elapsed_counter >=marker_step:
        # send a marker every marker_step s
        marker_stamp=sample_stamp
        marker=['marker_step: '+str(marker_step)+', local_clock: '+str(local_clock())+', marker_number: '+ str(counter_marker_number)]
        outletMARKER.push_sample(marker, marker_stamp[0])
        print('MARKER:'+str(marker))
        counter_time=local_clock() #advance counter
        counter_marker_number+=1

    if SAVE:
        """
        SAVE DATA
        """
        print('******************SAVING**************')
        sample,sample_stamp, marker=save.get_data(sample,sample_stamp,marker, marker_stamp)
        print('SAVED_SAMPLE_STAMP: {}'.format(sample_stamp))
        print('SAVED_SAMPLE: {}'.format( sample))
        print('SAVED_MARKER: {}'.format(marker))
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
outletMARKER.__del__


