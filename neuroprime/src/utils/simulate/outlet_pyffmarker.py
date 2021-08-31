# -*- coding: utf-8 -*-
"""
Created on Fri May 03 17:08:40 2019

@author: nm.costa
"""
from __future__ import (absolute_import, division, print_function)
from builtins import * #all the standard builtins python 3 style
from pylsl import StreamInfo, StreamOutlet, local_clock

infoMARKER = StreamInfo('PyffMarkerStream', 'Markers', 1, 0, 'string', 'pyffmarker') #same as pyff deffenition

# next make an outlet
outletMARKER = StreamOutlet(infoMARKER)


print("now sending data ...")
start_time=local_clock() #s
counter_time=start_time #s
marker_step=1 #s
elapsed_time=local_clock()-start_time #s
counter_marker_number=0
stop_outlet=marker_step*1000#float('inf')#marker_step*1000 #s
while elapsed_time<=stop_outlet:
    sample_stamp = [local_clock()] #correcting for the possible hardware delay - it's irrelevant unless you know how mutch
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

    elapsed_time=local_clock()-start_time
marker_stamp= [local_clock()]
marker=['END']
outletMARKER.push_sample(marker, marker_stamp[0])
print('MARKER:'+str(marker))
#DESTROY OUTLETS
    #this throws errors in inlet
    #Without destroy the stream is alive but not sending data
outletMARKER.__del__