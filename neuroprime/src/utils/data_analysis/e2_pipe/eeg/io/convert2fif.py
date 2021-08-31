# -*- coding: utf-8 -*-
"""
Created on Thu Nov 22 11:42:38 2018


Convert data from mushu uV to fif uV

@author: nm.costa
"""


import logging
import os
import phdproject.maincode.src.functions.myfunctions as my
#import argparse
import mne
import numpy as np
from scipy import io

logger = logging.getLogger(__name__)
logger.info('Logger started')

def mne2mat(raw, event_id, eeg_filepath, events_filepath, event_id_filepath):
    'converts raw mne EEG data into MAT format;'
    'events are stored in an extra file in EEGLab mat format.'

    'pick only eeg channels if you dont need'
    picks = mne.pick_types(raw.info, meg=False,eeg=True, stim=False)
    data, time = raw[picks,:]
    print 'saving eeg to', eeg_filepath
    io.savemat(eeg_filepath, dict(data=data), oned_as='row')
    events = mne.find_events(raw, stim_channel='STI', shortest_event=0)

    # EEGLab event structure: type, latency, urevent
    # Event latencies are stored in units of data sample points relative to (0)
    # the beginning of the continuous data matrix (EEG.data).
    eeglab_events = [[event[2], event[0], 0] for event in events]
    eeglab_events = np.asarray(eeglab_events, dtype=int)

    print 'saving events to', events_filepath
    io.savemat(events_filepath, dict(data=eeglab_events), oned_as='row')

    print 'saving event_id', event_id_filepath
    io.savemat(event_id_filepath, event_id, oned_as='row')

def play(filepath, newfiledir, typeformat):
    logger.info("!PLAY!..."+filepath)
    filedir, filenametype=os.path.split(filepath)
    filename, filetype =os.path.splitext(filenametype)
    #load mushu data to mne
    raw, event_id = my.mushu_to_mne(filepath)

    if typeformat=="fif":
        #Save in mne fif format
        nfilename = filename+".fif"
        nfilepath=os.path.join(nfiledir, nfilename)
        print 'saving eeg fif', nfilename
        raw.save(nfilepath)
        #save in mat event_id
        event_id_filepath = os.path.join(nfiledir, filename+"_event_id.mat")
        print 'saving event_id', event_id_filepath
        io.savemat(event_id_filepath, event_id, oned_as='row')

    if typeformat=="mat":
        eeg_filepath = os.path.join(nfiledir, filename+"_eeg.mat")
        events_filepath = os.path.join(nfiledir, filename+"_events.mat")
        event_id_filepath = os.path.join(nfiledir, filename+"_event_id.mat")
        mne2mat(raw, event_id, eeg_filepath, events_filepath,event_id_filepath)


if __name__=="__main__":
    #---DATA DIR
    datadir='C:/Users/admin.DDIAS4/Desktop/e2_data'#"/Volumes/Seagate/e1_data_nft/data_to_process_2/rawdata_curated_1"#"/Users/nm.costa/Desktop/testdata"#"/Users/nm.costa/Desktop/testdata"#"C:/Users/admin.DDIAS4/Desktop/testdata"
    #---FACTORIAL DIR
    #Init vars
    filetype=".meta"
    #Factorial design folder analysis
    groupdir=datadir
    ngroupdir=os.path.dirname(groupdir) #using parent dir
    typeformat='fif'
    ngroupdir=os.path.join(ngroupdir, "raw_"+typeformat+"_format")
    my.assure_path_exists_all(ngroupdir)
    group_l=os.listdir(groupdir)
    groups_bands_d={}
    for g in group_l:
        subjectdir=os.path.join(groupdir, g)
        if not os.path.isdir(subjectdir): continue #test if is a folder
        nsubjectdir=os.path.join(ngroupdir, g)
        my.assure_path_exists_all(nsubjectdir)
        subject_l=os.listdir(subjectdir)
        subjects_bands_d={}
        for s in subject_l:
            taskdir=os.path.join(subjectdir, s)
            if not os.path.isdir(taskdir): continue #test if is a folder
            ntaskdir=os.path.join(nsubjectdir, s)
            my.assure_path_exists_all(ntaskdir)
            task_l=os.listdir(taskdir)
            tasks_bands_d={}
            for t in task_l:
                filedir=os.path.join(taskdir, t)
                if not os.path.isdir(filedir): continue #test if is a folder
                nfiledir=os.path.join(ntaskdir, t)
                my.assure_path_exists_all(nfiledir)
                file_l=[ name for name in os.listdir(filedir) if os.path.isfile(os.path.join(filedir, name)) ] #get only files
                for fn in file_l:
                    if fn and (filetype in fn):#all .meta files
                        filepath=os.path.join(filedir, fn)
                        play(filepath, nfiledir, typeformat)




