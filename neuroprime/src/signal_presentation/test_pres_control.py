#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Mon Jul 30 12:58:00 2018

@author: nm.costa
"""

import time

#import wyrm.processing as proc
from wyrm import io
#
import libmushu
# My functions
import neuroprime.src.utils.myfunctions as my

#1st: Start pyff; Start LSL amplifier streaming


#pyff vars
PYFF_HOST='127.0.0.1'
FEEDBACK_APP='loopfeedbackclass'
MARKER_STREAM = 'PyffMarkerStream'
#INIT Pyff communication - control->pyff app
pyff = io.PyffComm(PYFF_HOST)
#INIT and laod feedback app on feedback controller
pyff.send_init(FEEDBACK_APP)
#calls on_init()
time.sleep(1)
#get the pyff marker inlet
pyff_marker_inlet = my.return_stream_inlet(MARKER_STREAM, streamtype='Markers')

#1.INIT ACQUISITION
amp = libmushu.get_amp('lslamp')
#Coniguration
amp.configure()
amp.amp.max_samples=1024 #Number of samples pulled from stream
#PATCHING OBJECT
amp.amp.lsl_marker_inlet = pyff_marker_inlet #force pyffMarker instead of first marker stream that could be the amplifier amps
print('RE_Initializing time correction...')
amp.amp.lsl_marker_inlet.time_correction()
amp.amp.lsl_inlet.time_correction()


#START AMP only one time, can test using multiple times with new implementation
amp.start()


#SET VARIABLES OF FEEDBACK APP
START_MARKER = "START_TEST_1"
END_MARKER = "END_TEST_1"
INIT_TEXT = "TEST TEST 1 ...."
pyff.set_variables({'caption' : 'INIT Presentation', 'START_MARKER' : START_MARKER, 'END_MARKER': END_MARKER, 'STIM_TIME' : 10,'fullscreen':False, 'PROTOCOL_TYPE': 'INIT','INIT_TEXT': INIT_TEXT})
pyff.play()
while 1:
    samples, markers = amp.get_data()  #PROBLEMS running it two times in a row
    print("data: {}".format(samples))
    print("markers: {}".format(markers))
    if END_MARKER in [m for _, m in markers]:
        break

print("**********TERMINATE TEST 1*****************")
time.sleep(5)
#when breaks the cycle new one can begin

#SET VARIABLES OF FEEDBACK APP
START_MARKER = "START_TEST_2"
END_MARKER = "END_TEST_2"
INIT_TEXT = "TEST TEST 2 ...."
pyff.set_variables({'caption' : 'INIT Presentation', 'START_MARKER' : START_MARKER, 'END_MARKER': END_MARKER, 'STIM_TIME' : 10,'fullscreen':False, 'PROTOCOL_TYPE': 'INIT','INIT_TEXT': INIT_TEXT})
pyff.play()
while 1:
    samples, markers = amp.get_data()  #PROBLEMS running it two times in a row
    print("data: {}".format(samples))
    print("markers: {}".format(markers))
    if END_MARKER in [m for _, m in markers]:
        break

print("**********TERMINATE TEST 2*****************")
time.sleep(5)

#SET VARIABLES OF FEEDBACK APP
START_MARKER = "START_TEST_3"
END_MARKER = "END_TEST_3"
INIT_TEXT = "TEST TEST 3 ...."
pyff.set_variables({'caption' : 'INIT Presentation', 'START_MARKER' : START_MARKER, 'END_MARKER': END_MARKER, 'STIM_TIME' : 10,'fullscreen':False, 'PROTOCOL_TYPE': 'INIT','INIT_TEXT': INIT_TEXT})
pyff.play()
while 1:
    samples, markers = amp.get_data()  #PROBLEMS running it two times in a row
    print("data: {}".format(samples))
    print("markers: {}".format(markers))
    if END_MARKER in [m for _, m in markers]:
        break

print("**********TERMINATE TEST 3*****************")
time.sleep(5)

if __name__ == "__main__":
    pass
