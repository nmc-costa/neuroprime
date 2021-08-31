# -*- coding: utf-8 -*-

import os
import mne


dir_root='/Users/nm.costa/Desktop/'
filename='1_pycorder_1min'
filepath=os.path.join(dir_root, 'e1_debug_experiment_2/raw_pycorder_data', filename+'.vhdr')
raw = mne.io.read_raw_brainvision(filepath, preload=True)
out_filepath=os.path.join(dir_root, 'e1_debug_experiment_2/raw_pycorder_data', filename+'.fif')
raw.save(out_filepath)