# -*- coding: utf-8 -*-
"""
Created on Wed Oct 16 15:50:33 2019

@author: nm.costa
"""
from __future__ import (absolute_import, division, print_function) #unicode_literals - more info needed to addapt; absolute_import does not let you to import from current folder, need to specify from the main package phdproject...
from builtins import * #all the standard builtins python 3 style

import os
import scipy
import neuroprime.src.utils.myfunctions as my

dir_dataroot='C:/Users/admin.DDIAS4/Desktop/e2_data/EG/S001/REST'
filename='EG_S001_REST_ss01_b01_16102019_11h15m_rest_ec_1'
filepath=os.path.join(dir_dataroot, filename+'.meta')


#------
filedir, filenametype=os.path.split(filepath)
filename, filetype =os.path.splitext(filenametype)
#load mushu data to mne
raw, event_id = my.mushu_to_mne(filepath, ch_names=None, montage=None)
#TODO:add manually the ref
#Save in mne fif format
nfiledir=my.get_test_folder(foldername='e2_data_fif')
nfilename = filename+".fif"
out_filepath=os.path.join(nfiledir, nfilename)
print ('saving eeg fif', nfilename)
raw.save(out_filepath)
#save in mat event_id
event_id_filepath = os.path.join(nfiledir, filename+"_event_id.mat")
print ('saving event_id', event_id_filepath)
scipy.io.savemat(event_id_filepath, event_id, oned_as='row')