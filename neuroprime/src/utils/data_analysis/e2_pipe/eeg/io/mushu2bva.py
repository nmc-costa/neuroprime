# -*- coding: utf-8 -*-
"""
Created on Wed Oct 16 15:50:33 2019

@author: nm.costa
"""
from __future__ import (absolute_import, division, print_function) #unicode_literals - more info needed to addapt; absolute_import does not let you to import from current folder, need to specify from the main package neuroprime...
from builtins import * #all the standard builtins python 3 style


import os
import scipy

import mne
from mne_io import write_raw_brainvision

import neuroprime.src.utils.myfunctions as my


import logging
logger = logging.getLogger(__name__)
logger.info('Logger started')


def get_filenamesequence(files_l, fileid_seq):
    ld=files_l #os.listdir(filesdir)
    fnseq={}
    for dn in fileid_seq:
        found=False
        for fn in ld:
            if not fn.find(dn)==-1:
                found=True
                fnseq[dn]=fn #Discriptor = NAme
                break
        if not found:
            fnseq[dn]= None
            logger.error("#ERROR: MISSING FILE WITH THE FOLLOWING DISCRIPTOR: "+dn)
    return fnseq

def mushu2bva(filepath, outdir, manual_amp_ref=['Cz'], save_event_id=True):
    #------
    filedir, filenametype=os.path.split(filepath)
    filename, filetype =os.path.splitext(filenametype)

    #load mushu data to mne
    raw, event_id = my.mushu_to_mne(filepath, ch_names=None, montage=None)
    #TODO:add manually the ref
    raw=mne.add_reference_channels(raw, manual_amp_ref)
    #Save in bva vhdr format
    nfilename = filename+".vhdr"
    out_filepath=os.path.join(outdir, nfilename)
    print ('saving eeg fif', nfilename)
    write_raw_brainvision(raw, out_filepath, events=True)
    if save_event_id: #WARNING: EVENT ID points not well reconstructed add better
        #save in mat event_id or in json
#        event_id_filepath = os.path.join(outdir, filename+"_event_id.mat")
#        print ('saving event_id', event_id_filepath)
#        scipy.io.savemat(event_id_filepath, event_id, oned_as='row')
        #save in json event id
        event_id_filepath = os.path.join(outdir, filename+"_event_id.txt")
        print ('saving event_id json', event_id_filepath)
        my.save_obj_json(event_id_filepath, event_id)


def test_1():
    dir_dataroot='C:/Users/admin.DDIAS4/Desktop/e2_data/EG/S001/REST'
    filename='EG_S001_REST_ss01_b01_16102019_11h15m_rest_ec_1'
    filepath=os.path.join(dir_dataroot, filename+'.meta')
    outdir=my.get_test_folder(foldername='e2_data_bva')
    mushu2bva(filepath, outdir)

def test_2(subject_list=[]):
    #---DATA DIR
    datadir=my.get_test_folder(foldername="e2_data")#
    outdir=my.get_test_folder(foldername='e2_data_bva')

    fileid_seq=["alpha_eo_3.meta"]
#                ["rest_ec_1.meta","rest_eo_2.meta","alpha_eo_3.meta", #b1
#                "rest_ec_4.meta", "rest_eo_4.meta","breathingv6_ec_4.meta", "breathingv6_eo_4.meta","imageryv6_ec_4.meta", "imageryv6_eo_4.meta","alpha_ec_5.meta","alpha_eo_5.meta",#b2
#                "rest_ec_6.meta", "rest_eo_6.meta","breathingv6_ec_6.meta", "breathingv6_eo_6.meta","imageryv6_ec_6.meta", "imageryv6_eo_6.meta","alpha_ec_7.meta","alpha_eo_7.meta",#b3
#                "rest_ec_8.meta", "rest_eo_8.meta","breathingv6_ec_8.meta", "breathingv6_eo_8.meta","imageryv6_ec_8.meta", "imageryv6_eo_8.meta","alpha_ec_9.meta","alpha_eo_9.meta",#b4
#                "rest_ec_10.meta", "rest_eo_10.meta","breathingv6_ec_10.meta", "breathingv6_eo_10.meta","imageryv6_ec_10.meta", "imageryv6_eo_10.meta","alpha_ec_11.meta","alpha_eo_11.meta",#b5
#                "rest_ec_12.meta","rest_eo_13.meta","alpha_eo_14.meta"#b6
#                ]

    #Factorial design folder analysis
    groupdir=datadir
    group_l=os.listdir(groupdir)
    for g in group_l:
        subjectdir=os.path.join(datadir, g)
        if not os.path.isdir(subjectdir): continue #test if is a folder
        subject_l=os.listdir(subjectdir)
        for s in subject_l:
            taskdir=os.path.join(subjectdir, s)
            if not os.path.isdir(taskdir): continue #test if is a folder
            if subject_list and s not in subject_list: continue
            task_l=os.listdir(taskdir)
            for t in task_l:
                filedir=os.path.join(taskdir, t)
                if not os.path.isdir(filedir): continue #test if is a folder
                file_l=[ name for name in os.listdir(filedir) if os.path.isfile(os.path.join(filedir, name)) ] #get only files
                #PROCESSING
                fnseq=get_filenamesequence(file_l, fileid_seq) #dict as no sequence
                true_fileid_seq=[]
                for dn in fileid_seq:
                    if dn in fnseq:
                        true_fileid_seq.append(dn.split(".")[0])
                for k in fnseq:
                    f=fnseq[k] #f.meta
                    if f: #if file exists
                        filepath = os.path.join(filedir, f)
                        mushu2bva(filepath, outdir, manual_amp_ref=['Cz'])


if __name__=="__main__":
    s_l=[]
    for i in range(38,64):
        s_l.append('S'+ '{num:03d}'.format(num=i))
    test_2(subject_list=s_l)