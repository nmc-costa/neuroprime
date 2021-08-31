# -*- coding: utf-8 -*-
"""
Created on Mon Sep 09 13:14:30 2019

@author: nm.costa
"""
from __future__ import (absolute_import, division, print_function) #unicode_literals - more info needed to addapt; absolute_import does not let you to import from current folder, need to specify from the main package neuroprime...
from builtins import * #all the standard builtins python 3 style

import os
import mne
import wyrm
import numpy as np
import time

# My functions
import neuroprime.src.utils.myfunctions as my
import neuroprime.src.signal_processing.eegfunctions as eeg





def test_1():
    save = False
    plot = True
    on_filter = True  # DC Offset
    rereference = False
    ref_channels = ['Fp1']  # or average
    
    #load data from sample folder
    folderdir = 'e2_sample'
    filename = "EG_S001_REST_ss01_b01_08102019_14h13m_rest_1"
    filetype = ".meta"
    filepath = my.get_filetoreplay(folderdir=folderdir, filename=filename, filetype=filetype)

    
    # wyrm test data: mushu2wyrm
    raw_wyrm = my.load_mushu_data(filepath) #format: raw_wyrm.data samples x channels
    if on_filter:
        order=4
        fs_n= raw_wyrm.fs / 2
        l_freq, h_freq=1, 40#bandpass
        b, a = wyrm.processing.signal.butter(order, [l_freq / fs_n, h_freq / fs_n], btype= 'band' )
        raw_m_2 = wyrm.processing.lfilter(raw_wyrm, b, a)
    if plot:
        spectrum = wyrm.processing.spectrum(raw_wyrm)
        psds=spectrum.data.transpose() #chs, psds
        freqs =spectrum.axes[0]
        fmax=freqs<40
        psds=psds[:,fmax]
        freqs=freqs[fmax]
        eeg.plot_psd(psds, freqs, log_scale=False)

    # mne test data: wyrm2mne or mushu2mne
    st=time.time()
    raw, event_id = my.raw_wyrm_to_mne(raw_wyrm) #raw, event_id = my.mushu_to_mne(filepath) 
    print("Event id 1: ", event_id)
    et=time.time()-st
    stim_ch_1 = raw.pick_types(stim=True)
    print("Time raw: ", et)
    
    raw_m=raw
    print(raw_m.ch_names)
    if on_filter:
        l_freq, h_freq = 1, None  # highpass
        raw_m.filter(l_freq, h_freq)
        l_freq, h_freq = None, 40  # lowpass
        raw_m.filter(l_freq, h_freq)
    if rereference:
        raw_m.set_eeg_reference(ref_channels=ref_channels, projection=False)
    if plot:
        picks = mne.pick_types(raw_m.info, eeg=True)
        raw_m.plot_psd(fmax=40, picks=picks)
        raw_m.pick_types(eeg=True).plot(n_channels=1)
    if save:
        filedir, filname, ext = my.parse_path_list(filepath)
        nfilename = filename + ".fif"
        out_filepath = os.path.join(filedir, nfilename)
        print('saving eeg fif'), nfilename
        raw_m.save(out_filepath)

    
    #simulate an online conversion 
    st=time.time()
    raw, event_id = my.online_raw_wyrm2mne(raw_wyrm)
    print("Event id 2: ", event_id)
    et=time.time()-st
    stim_ch_2=raw.pick_types(stim=True)
    print("Time online: ", et)
    
    print("Same : ", (stim_ch_1.get_data()==stim_ch_2.get_data()).all() )
#    print("Stim 1 : ", stim_ch_1.get_data().tolist() )
#    print("Stim 2 : ", stim_ch_1.get_data().tolist() )


if __name__ == "__main__":
    test_1()

