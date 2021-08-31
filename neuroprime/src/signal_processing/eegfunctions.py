# -*- coding: utf-8 -*-
"""
Created on Fri Jun 15 14:37:57 2018

SCRIPT:
    EEG Signal Analysis functions(see MNE and EEGLAB documentation):
        1.DATA STRUCTURES AND CONTAINERS
        2.DATA I/O AND DATASETS
        3.PREPROCESSING (FILTERING, SSP, ICA, MAXWELL FILTERING, ...)
        4.TIME- AND FREQUENCY-DOMAIN ANALYSES
        5.REALTIME
        6.VISUALIZATION
        10.SOURCE-LEVEL ANALYSIS
        7.STATISTICS
        8.MACHINE LEARNING (DECODING, ENCODING, MVPA)
        9.CONNECTIVITY



My EEG INSTRUMENTATION:
    EEG setup:
        Amplifier: Actichamp BVP
    Data type format:
        IEEE_FLOAT_32
        IEEE floating-point format, single precision, 4 bytes per value
        [uV] microvolts
        tranfered to mushu IEEE_FLOAT_32
        IEEE floating-point format, single precision, 4 bytes per value
        when loading data with wyrm library -> data converted to numpy.float32 single precision
        MNE uses float64 double precision for processing, but saves at float 32 single precision
        Precison discussion:https://github.com/mne-tools/mne-python/issues/2720
    Cap :
        ACTICAP new design UOL BVP - easycap
    Number of channels:
        32
    Number of electrodes:
        32 Active Electrodes
    Channels Acticap - sorted from 1 to 32 or 0-31:
        acticap_10_20_new_design_uol = ['Fp1', 'Fz', 'F3', 'F7', 'FT9', 'FC5', 'FC1', 'C3','T7','TP9', 'CP5', 'CP1', 'Pz', 'P3', 'P7', 'O1', 'Oz', 'O2', 'P4', 'P8', 'TP10', 'CP6','CP2', 'Cz','C4', 'T8', 'FT10', 'FC6','FC2', 'F4', 'F8','Fp2']
    Sampling frequency:
        125(resampled), 250(resampled), 500(resampled), 1000(resampled), 10000(native) Hz
        using 500
    Ground Reference Location:
        FCz -Acticap - However, new cap does not have FCz
    Reference electrode Location:
        No reference electrode - Using Active shield from Activechamp + Average Re-reference
    Electrode impedances:
        kept below 50 kohm

EEG Data Packages:
    MUSHU
    WYRM
    MNE


PACKAGE DATA STRUCTURE
MNE:
    Raw: The core data structure is simply a 2D numpy array (channels × samples) (in memory or loaded on demand) combined with an Info object (.info attribute)
    Epochs: representing continuous data as a collection of time-locked trials, stored in an array of shape (n_events, n_channels, n_times)
    Evoked:  used for storing averaged data over trials.
    Info: created when data is imported into MNE-Python and contains details such as:
        date, subject information, and other recording details
        the sampling rate
        information about the data channels (name, type, position, etc.)
        digitized points
        sensor–head coordinate transformation matrices

    DataTypes:
        float64 for processing
        float32 for saving
    Units:
        V - Volts
        s - seconds

    Source:https://martinos.org/mne/stable/manual/io.html



MUSHU:
    -Saves three kinds of data to disk: the actual EEG data, the markers, and some metadata.
    EEG data:
        is saved in binary form. Since the number- and ordering of EEG channels is ﬁxed during a recording, we can write the values for each channel sample-wise to disk.
    Markers:
        stored in text ﬁles, where each line contains the time stamp in milliseconds and the label.  The time stamps relative to the beginning of the recording(conversion from relative to absolute-formula bastian thesis)
    Metadata:
        stored as JSON ﬁles (more on JSON in Section 4.4.1), with the most crucial information being the sampling frequency, the channel names, and the order of channels in the EEG data ﬁles used in that recording.

WYRM:
    n-dimensional arrays.The dimensions of an array are sometimes called axes. For example: an array with n rows and m columns has two dimensions (axes) of length n and m respectively.
    shape of an array is a tuple indicating the length (or size) of each dimension

    STRUCTURE ATTRIBUTES of Data:
    data: n-dimensional array (e.g.(time | frequency, channel)). Like a matrix
    names: quantities or names for each dimension in the data (e.g.[ 'time' , 'frequency' ,  'channel' ].)
    axes: array of arrays (length equal to the number of dimensions of ). describes the rows and columns of the data, like headers describe the rows and columns of a table (e.g [[time labels],[Freq lables],[Ch labels]])
    units: contains the physical units of the data in axes (e.g [ 'ms' ,  'Hz' ,  '#' ]
    markers: [float(ts), str(m)] - [Absolute timestamp, Marker name]

    DataTypes:
        float32 for everything - It can have errors in processing because of single precision
    Units:
        uV - microVolts
        ms - seconds

    #NOTE:Wyrm time units in ms; MNE time units in s


@author: nm.costa
"""
from __future__ import division


__version__="3.1+dev" #e1 version working with nftclass version 2

import time

#import os
#import sys
import numpy as np
#import copy
#import scipy as sp
import math
#signal acquisition & processing
#import libmushu.driver.labstreaminglayer
import wyrm
import wyrm.processing as wyrmproc
from wyrm import io #dont remove this -needed because bad wyrm behavior
#from wyrm import plot
from wyrm.types import RingBuffer, BlockBuffer
#advanced EEG processing
import mne
import matplotlib.pyplot as plt
#import pandas as pd
from scipy.signal import savgol_filter

from scipy import stats
#from collections import namedtuple
# My functions
import neuroprime.src.utils.myfunctions as my
#import philistine_iaf as iaf

#LOGGING
import logging
my.setlogfile(modulename=__name__, setlevel=logging.WARNING, disabled=True)
logger = logging.getLogger(__name__)
logger.disabled = False
mne.set_log_level('INFO')
#DEBBUGING
import pdb



_unit_dict = my.mne_unit_dict


def config_packages():
    pass

"""2.DATA I/O and datasets"""

#ACTICHAMP - Amplifier - Same as my_functions default - if you want change the cap ch names design or the montage file used, do it where
cap_chs_design=my.cap_chs_design #channels names
montage_file=my.montage_file# channels design


def load_data(filepath,filetype, swap_ch_names=False, ch_names=cap_chs_design,in_data_unit='uV', package="mne"):
    """
    1.Load continuous data:
        1.0 Channel Locations: TODO? With the montage in MNE probably done
            EASYCAP BVP
            32 CHs
            10_20 system
            ground in the Nasion
            #NOTE: eeglab -To plot EEG scalp maps in either 2-D or 3-D format, or to estimate source locations for data components. MNE also stores in info
"""
    #Not necessary because online also gets chs directly
    raw=None
    start_marker, end_marker = None, None
    cnt=None
    if package=="mne":
        if filetype==".meta":
            cnt, event_id = my.mushu_to_mne(filepath, chanaxis=-1, ch_names=ch_names, ch_types="eeg", in_data_unit=in_data_unit, montage = montage_file)
        if filetype==".vhdr":
            cnt = mne.io.read_raw_brainvision(filepath)

    if package=="wyrm":
        #1 LOAD DATA
        if filetype==".meta":
            #--Load continuous data to find threshold
            cnt = my.load_mushu_data(filepath)
            #ADD channel list names to axes - optional - lslamp changes names to numbers
            if swap_ch_names:
                data=cnt.data
                axes = cnt.axes
                axes[-1] = np.array(ch_names)
                units=cnt.units
                names=cnt.names
                cnt.copy(data=data, axes=axes, units=units, names=names)
            #markers to cut the data
            start_marker="START"
            end_marker="END"

        if filetype==".vhdr":
            cnt = wyrm.io.load_brain_vision_data(filepath)
            #markers to cut the data
            start_marker="R128"
            end_marker="R128"
    raw=cnt
    return raw, start_marker, end_marker

def get_data(amp, package="mushu"):
    "get data from amp"
    pass


def convert_units(dat, convertion=(1e-6, "V"), timeaxis=-2, package="wyrm"):
    cdat=my.convert_units(dat, convertion=convertion, timeaxis=timeaxis, package=package)

    return cdat

def convert_data(indata, markers=None, amp_fs=None, amp_channels=None,ch_names=cap_chs_design, in_data_unit='uV', method="raw_wyrm_to_mne"):
    data = indata.copy()  #just for safety
    event_id=None
    if method=="mushu_to_wyrm":
        data = wyrm.io.convert_mushu_data(data, markers, amp_fs, amp_channels)
    if method=="raw_wyrm_to_mne": #MNE RAW CREATION TAKES ~200ms
        data, event_id = my.online_raw_wyrm2mne(data, ch_names=ch_names, ch_types="eeg",in_data_unit=in_data_unit, montage = montage_file) #
    if method=="epoch_wyrm_to_mne":
        pass

    return data, event_id



def save_data(filepath,filetype, package="mne"):
    pass

def send_data(package="wyrm"):
    pass

"""3.PREPROCESSING (FILTERING, SSP, ICA, MAXWELL FILTERING, ...)"""


def istancetype(inst, package="mne"):
    """Check data / pull arrays from inst."""
    """"
    from ..io.base import BaseRaw
    from ..epochs import BaseEpochs
    from ..evoked import Evoked
    if isinstance(inst, (BaseEpochs, BaseRaw, Evoked)):
        pass
    """

    if type(inst).__module__ == "mne.raw":
        pass
    if type(inst).__module__ == "mne.epoch":
        pass
    if type(inst).__module__ == "mne.evoked":
        pass

def select_ch_picks(ch_names_in_order=cap_chs_design, select_chs=None, ch_extract_feature=None, ch_extract_iaf=None):
    """
    1.1Choose Channels to process: TODO
            SMR: electrode over position CZ?
            Alpha:Electrode over position PZ?
    """
    #ASSERT That they are list type or none

    #SELECT CHANNELS and picks(ch indexes)
    ORDERED_CH_NAMES = ch_names_in_order
    SELECT_CHANNEL = ch_names_in_order #all_chs
    if select_chs: SELECT_CHANNEL = select_chs #only channels to process and extract features - can be without order
    CH_EXTRACT_FEATURE=[]
    if ch_extract_feature: CH_EXTRACT_FEATURE=ch_extract_feature
    CH_EXTRACT_IAF=[]
    if ch_extract_iaf: CH_EXTRACT_IAF=ch_extract_iaf



    # channels indexes = picks
    picks=[]
    order_select_channels=[]
    ch_extract_feature_picks=[]
    ch_extract_iaf_picks=[]
    for i, c in enumerate(ORDERED_CH_NAMES):
        #NOTE: using upper to find even if you make a mistake
        if c.upper() in (name.upper() for name in SELECT_CHANNEL):
            order_select_channels.append(c)
            picks.append(i) #all indexes
            if c.upper() in (name.upper() for name in CH_EXTRACT_FEATURE):
                ch_extract_feature_picks.append(i)
            if c.upper() in (name.upper() for name in CH_EXTRACT_IAF):
                ch_extract_iaf_picks.append(i)


    return order_select_channels, picks, ch_extract_feature_picks, ch_extract_iaf_picks

def select_data_chs(data, index_picks, package="wyrm"):
    if package=="wyrm":
        chanaxis=-1
        regexp_list=[]
        for i in index_picks:
            regexp_list.append(data.axes[chanaxis][i])  #obtain Ch names in data
        data = wyrmproc.select_channels(data, regexp_list, chanaxis=-1)
    if package=="mne":
        picks=mne.pick_types(data.info,meg=False, eeg=False, stim=True)
        picks=sorted(index_picks+picks.tolist())#list - add stim chs to the list if it is not included
        picks = list(set(picks)) #list - remove duplicates
        ch_names=data.info['ch_names']
        ch_names_picks = [ch_names[i] for i in picks]
        data=data.pick_channels(ch_names_picks) #but mantain the stim ch

    return data

def remove_data_chs(data, chs):
    """
    remove bad chs TODO
    """
    pass



def select_data_interval(data, start, end, method="markers", package="wyrm"):
    """
    1.2.Choose Data interval:  TODO
            (between start and end marker)
    """
    if package=="wyrm":
        #wyrmdata : time ms
        if method=="markers":
            #select data arround start and end markers
            assert hasattr(data, 'markers')
            markers = data.markers
            start_time, end_time= None, None
            for t, m in markers:
                if start and m.find(start)>-1:
                    start_time=t-10 #ms Just to not remove marker
                    break
            for t, m in sorted(markers, reverse=True):
                if end and m.find(end)>-1:
                    end_time=t+10 #ms Just to not remove marker
                    break
            if start_time and end_time:
                data = wyrmproc.select_ival(data, [start_time, end_time] )

            else:
                logger.error("Markers to select data not found - Something wrong - Data not selected")

        if method=="segment":
            #select data arround start and end time
            data = wyrmproc.select_ival(data, [start, end] )

    if package=="mne":
        if method=="markers":
            #select data arround start and end markers
            pass
        if method=="segment":
            #select data arround start and end time
            pass

    return data


def filterdesigncoeff(fs_n, n_channels, order=2, freq=60, filterband='low', filtertype="butter", method="online", package="wyrm"):
    b, a, zi = None, None, None
    if package=="wyrm":
        if filtertype=="butter":
            b, a = wyrmproc.signal.butter(order, [freq / fs_n], btype= filterband )
        if method=="online":
            """
            When filtering the data chunk-wise, we have to use lfilter with filter delay values in order to receive the same results as if we were filtering the whole data set at once.
            #NOTE: zi is calculated for all channels
            state zi corresponds to the steady state of the step response.
            use of this function is to set the initial state so that the output of the filter starts at the same value as the first element of the signal to be filtered.
            zi parameter that represents the initial conditions for the filter delays-This is useful if you want to filter n-dimensional data like multi channel EEG.
            """
            zi = wyrmproc.lfilter_zi(b, a, n_channels)

    return  b, a, zi


def filtering(data, b=None, a=None, zi=None,  method="online", package="wyrm"):
    if package=="mne":
        if method=="online":
            pass
        if method=="offline":
            pass
    if package=="wyrm":
        #works online and offline(zi=None)
        logger.debug("#NOTE PUT offline and online option because of the option of starting all 3 coefficients at once in the bigining")
        if method=="offline":
            data = wyrmproc.lfilter(data, b, a, zi=None)
        if method=="online":
            #update data and zi
            data, zi = wyrmproc.lfilter(data, b, a, zi=zi)


    return data, zi



def init_buffers(blocksize=10, ringtime=1000, method="online", package="wyrm"):
    """
    Note resample value and delay sequence are dependent

    blocksize: samples
    ringsize: miliseconds

    """
    blockbuffer, ringbuffer = None, None
    if package=="wyrm":
        if method=="online":
            blockbuffer = BlockBuffer(blocksize)
            # Circular Buffer implementation
            ringbuffer = RingBuffer(ringtime)
    return blockbuffer, ringbuffer

def apply_blockbuffer(data, blockbuffer, method="online", package="wyrm"):
    """
    During the processing we will subsample the data from 1kHz to 100Hz.
        The subsampling internally works by taking, in this case, every 10th sample. Since Mushu’s LSL amplifier
        has no configuration for a block size that would guarantee that get_data returns data in
        multiples of a 10 samples, we have to use Wyrm’s BlockBuffer, in order to avoid losing
        samples between the chunks of data. For that we have to either set a block size of 10 samples
(or an integer multiple of 10) in the amplifier or utilize Wyrm’s implementation of a block
buffer. Since most amplifiers allow for a configuration of the block size, we set the block
size of 10 samples in the ReplayAmp as well.

        We initialize the BlockBuffer with a block length of 10 samples and the RingBuffer with a length of 5000 milliseconds.
        The results of the classifications within each sequence will be stored in the sequence_result
        dictionary, where the keys are the markers and the values the sum of the LDA outputs for
        that marker.

        The BlockBuffer behaves like a queue, a first-in-first-out
data structure, that is unlimited in size. The block buffer has two methods: append and
get. append accepts a continuous Data object and appends it to its internal data storage.
get returns (and internally deletes) the largest possible block of data that is divisible
by blocksize, starting from the beginning of its internal data storage. After a get, the
BlockBuffer’s internal data has at most the length blocksize-1.

    use Wyrm’s BlockBuffer, in order to avoid losing samples between the chunks of data, because Mushu’s LSL amplifier has no configuration for a block size that would guarantee that get_data returns data in multiples of a fs/resample_value(=500/100=n*5) samples

    use the BlockBuffer to make sure that the data further down the processing line
            has a length of multiples of 10 samples. For that we simply append the new data to the
            BlockBuffer and call get for as much data as possible in the BlockBuffer that meets the length
            requirements. Any remaining data (here, at most 9 samples) will stay in the BlockBuffer
            until the next iteration of the loop.
    """
    input_data=data
    if package=="wyrm":
        if method=="online":
            #APPLY BLOCKBUFFER
            blockbuffer.append(data) #blockbuffer updated - seems that is not need to return to change
            data = blockbuffer.get()

            #LOG INFO
            try:
                logger.debug("\n>>BLOCKBUFFER INPUT DATA SHAPE : {}".format(input_data.data.shape))#format: wyrm
                logger.debug("\n>> blocksize: {}".format(blockbuffer.samples))
                logger.debug("\n>> blockbuffer_current_samples: {}".format(blockbuffer.dat.data.shape))
                logger.debug("\n>> blockbuffer_remaining_samples: {}".format(blockbuffer.dat.data.shape))
                logger.info("\n>> BLOCKBUFFER OUTPUT DATA SHAPE : {}".format(data.data.shape))#format: wyrm
            except:
                pass


    #update data and blockbuffer
    return data, blockbuffer

def apply_ringbuffer(data, ringbuffer, method="online", package="wyrm"):
    """
    Wyrm’s implementation of a ring buffer where we can append small
chunks of data in each iteration of the online loop and get the last 5000ms of the acquired
data to perform the classification on
        """
    if package=="wyrm":
        if method=="online":
            ringbuffer.append(data) #ringbuffer updated with specific sampling frequency(even after subsampling)
            data = ringbuffer.get()

            logger.info("\n>> ringbuffer: current data lenght {} ; total length {} ".format(len(data.data), ringbuffer.length))

    #update data and ringbuffer
    return data, ringbuffer


def rereference(data, ref_channels=[],amp_ref_channels=[], package="mne"):
    if package=="mne":
        """
        ref_channels= "average"  |  [] No-rereferencing | ['CH'] for rereference
        projection=False directly applies reference in data
        """
        st=time.time()
        #add amp previous refs
        if amp_ref_channels:
            data=mne.add_reference_channels(data, amp_ref_channels)
        #Set new reference
        data.set_eeg_reference(ref_channels=ref_channels, projection=False)
        et=time.time()-st
        logger.info("\n>> REREFERENCE:{}".format(et))


    return data

def subsample(data, subsample=100,  method="online", package="wyrm"):

    if package=="mne":
        if method=="online":
            pass
        if method=="offline":
            pass
    if package=="wyrm":
        #same online and offline
        data = wyrmproc.subsample(data, subsample)

    return data

def detrend(x, order=1, axis=-1):
    """Detrend the array x.
    Parameters
    ----------
    x : n-d array
        Signal to detrend.
    order : int
        Fit order. Currently must be '0' or '1'.
    axis : integer
        Axis of the array to operate on.
    Returns
    -------
    xf : array
        x detrended.
    Examples
    --------
    As in scipy.signal.detrend:
        >>> randgen = np.random.RandomState(9)
        >>> npoints = int(1e3)
        >>> noise = randgen.randn(npoints)
        >>> x = 3 + 2*np.linspace(0, 1, npoints) + noise
        >>> (detrend(x) - noise).max() < 0.01
        True
    """
    from scipy.signal import detrend
    if axis > len(x.shape):
        raise ValueError('x does not have %d axes' % axis)
    if order == 0:
        fit = 'constant'
    elif order == 1:
        fit = 'linear'
    else:
        raise ValueError('order must be 0 or 1')

    y = detrend(x, axis=axis, type=fit)

    return y

def artifact_detection():
    """
    MARK WINDOWS/SEGMENTS/EPOCHS TO REJECT
    SLOPE
    ENVELOP
    Extreme values
    Signal-Space Projection (SSP): No, TODO
    Decomposing Data Using ICA: No, TODO - - Not fisable with online feature exttraction
    Maxwell filtering
    """
    pass

def artifact_detection_continuous(raw, rej_eog=["Fp1", "Fp2"], filter_length=10, rej_eye_mov=100e-3, rej_eye_dif=60e-3, plotlog=False, method="offline", package="mne"):
    """
    REJECTING ARTIFACTS IN CONTINUOUS DATA

    Rejecting data by visual inspection
    Rejecting data channels based on channel statistics

    Rejecting EOG artifacts - Blinks and Saccades
    Signal-Space Projection (SSP): No, TODO
    Decomposing Data Using ICA: No, TODO - - Not fisable with online feature exttraction
    Maxwell filtering
    filter_length : str | int | None
        Number of taps to use for filtering.
    """
    logger.debug("#TODO:rej_eye_mov  and rej_eye_dif not implemented -probably not needed if rej_eog works ")


    #artifact rejection
    if package=="mne":
        if rej_eye_mov:
            #TODO: See if chs fp1 and fp2 in epoch <rej_eye_mov
            pass
        if rej_eye_dif:
            #TODO: See if chs fp1 and fp2 in epoch <rej_eye_dif
            pass
        if rej_eog:
            ch_name=rej_eog[0]
            if len(rej_eog)>1:
                for ch in rej_eog[1:]:
                    ch_name=str(ch_name+","+ch)
            eog_events = mne.preprocessing.find_eog_events(raw, ch_name=ch_name, event_id=998, l_freq=1, h_freq=10, filter_length=filter_length)
            n_blinks = len(eog_events)
            # Center to cover the whole blink with full duration of 0.5s:
            onset = eog_events[:, 0] / raw.info['sfreq'] - 0.25
            duration = np.repeat(0.5, n_blinks)
            raw.annotations = mne.Annotations(onset, duration, ['bad blink'] * n_blinks, orig_time=raw.info['meas_date'])
            logger.info("raw_annotations: {}".format(raw.annotations))  # to get information about what annotations we have
            if plotlog:
                raw.plot(events=eog_events)  # To see the annotated segments.

    return raw

def artifact_rejection_epoch(epoch, rej_inspection=False, rej_max_peaktopeak=None, rej_min_peaktopeak=None, test_max_rej=False, plotlog=False, method="offline", package="mne"):
    """
    Rejecting epochs by visual inspection
    Rejecting extreme values - find abnormal values - eeglab -+/-75 µV

    Rejecting abnormal trends - slope artifacts -envelop artifacts

    Rejecting improbable data

    Rejecting abnormally distributed data
    Rejecting abnormal spectra
    """
    if package=="mne":
        #1.Drop existing marked by anotations and projections
        epoch.drop_bad()
        #2.Rejecting by inspection
        if rej_inspection:
            epoch.plot(block=10) #IT seems it removes rejections
        #2.Reject extreme values
        reject=None
        flat=None
        if test_max_rej:
            #TodoTEST between max and min drop epochs reject and flat parameters
            pass
        if rej_max_peaktopeak:
            reject=dict(eeg=rej_max_peaktopeak)  #peak to peak
        if rej_min_peaktopeak:
            flat=dict(eeg=rej_min_peaktopeak) #minimum peak to peak

#        pdb.set_trace()
        epoch.drop_bad(reject=reject, flat=flat)


        if plotlog:
            #EPOCH DROP LOG
            logger.info("DROP EPOCHS LOG: {}".format(epoch.drop_log))  # only a subset
            epoch.plot_drop_log()
#    pdb.set_trace()
    return epoch

def slopeartifacts():
    pass

def envelopartifacts():
     pass

def extremeartifacts(data, max_value):
    pass

def ssp():
    pass
def ica():
    pass
def maxwellfilter():
    pass

def artifact_rejection():
    """REJECT MARKED WINDOWS/SEGMENTS/EPOCH"""
    pass

def artifact_correction():
    """3.6 Artifact detection/rejection in epochs:No"""
    pass


"""4.PROCESSING: TIME- AND FREQUENCY-DOMAIN ANALYSES"""

#TIME ANALYSIS
#---------------

def add_repetitive_events_wyrm(wyrmData, epoch_interval, eventName, start_marker=None,end_marker=None, method="all"):
    #NOTE: wyrmdata
    assert hasattr(wyrmData, 'fs')
    assert hasattr(wyrmData, 'markers')
    assert epoch_interval[0] <= epoch_interval[1]
    #convert to tuple if needed - format of markers is list of tuples
    for i,item in enumerate(wyrmData.markers):
        if not isinstance(item, tuple):
            wyrmData.markers[i]=tuple(item)
    timeaxis = -2
    epoch_time = epoch_interval[1]-epoch_interval[0] #ms
    data_t0 = wyrmData.axes[timeaxis][0]
    data_tf = wyrmData.axes[timeaxis][-1]
    data_ts = int( (1/float(wyrmData.fs))*(10**(3)))
    data_total_time = data_tf - data_t0 #ms
    data_total_samples = len(wyrmData.axes[timeaxis])
    # the expected length of each cnt in the resulted epo
    epoch_samples = int(wyrmData.fs * (epoch_interval[1] - epoch_interval[0]) / 1000.)
    number_of_epochs_from_time = int(np.rint(data_total_time / float(epoch_time)))
    number_of_epochs = int(np.rint(data_total_samples/epoch_samples))

    logger.debug("epoch_number using time:{}, epoch_number using samples: {}".format(number_of_epochs_from_time, number_of_epochs))
    new_markers=[]
    if number_of_epochs == 0:
        return [] #if cant make no epochs
    else:
        #append
        if method=="all": #ADDING FROM 0 to number_of_epochs+1
            logger.debug("#Change to 1*data_ts({}) if not getting initial event:  ".format(data_ts))
            for n in range(number_of_epochs+1):
                timestamp = (n)*epoch_time + (data_t0)
                if timestamp>data_tf: break
                markerName =eventName
                new_markers.append((timestamp, markerName))
        if method=="onset":#ADDING FROM 0 to number_of_epochs
            for n in range(number_of_epochs):
                timestamp = (n)*epoch_time + data_t0
                if timestamp>data_tf: break
                markerName =eventName
                new_markers.append((timestamp, markerName))
        if method=="offset":#ADDING FROM 1 to number_of_epochs+1
            for n in range(number_of_epochs+1):
                timestamp = (n+1)*epoch_time + data_t0
                if timestamp>data_tf: break
                markerName =eventName
                new_markers.append((timestamp, markerName))
        #sort
        allmarkers = sorted(wyrmData.markers + new_markers)
        #START and END MARKER
        if start_marker or end_marker:
            if start_marker:
                start=start_marker
            if end_marker:
                end=end_marker
            #remove markers outside start and end
            #go trough the array for and find the start and end index makers and remove the others - just to safely use epoch within experiment time
            if start_marker:
                for i, m in enumerate(allmarkers):
                        if not m[1].find(start)==-1:
                            start_index = i # 1st start marker appearance
                            break
            if end_marker:
                for i, m in enumerate(sorted(allmarkers,reverse=True)):
                        #Note: It removes post end
                        if not m[1].find(end)==-1: #find substring
                            end_index= -i-1
                            break
            if start_marker:
                allmarkers = allmarkers[start_index:]
            if end_marker:
                if end_index==-1:
                    allmarkers = allmarkers[:]
                else:
                    allmarkers = allmarkers[:end_index+1]
        wyrmData.markers = allmarkers

#    logger.info(wyrmData.markers)
    return wyrmData


def check_newsamples(dat, marker_def, ival, newsamples=None, timeaxis=-2):
    """
    we have to make sure that segment returns each epoch only once within all
iterations of the loop in order to avoid classifying the same epoch more than once. For
that we provide the segment method with the optional newsamples parameter.

information about the number of new samples, segment can calculate which epochs must
have already been returned in previous iterations and returns only the new epochs. Note,
that segment has to take into account, that the interval of interest SEG_IVAL typically extends
to poststimulus time. I.e., a segment is only returned when enough time has elapsed after a
marker in order to extract the specified interval.
    """

    assert hasattr(dat, 'fs')
    assert hasattr(dat, 'markers')
    assert ival[0] <= ival[1]
    if newsamples is not None:
        assert newsamples >= 0
        # the times of the `newsamples`
        new_sample_times = dat.axes[timeaxis][-newsamples:] if newsamples > 0 else []
    # the expected length of each cnt in the resulted epo
    expected_samples = dat.fs * (ival[1] - ival[0]) / 1000
    data = False
    classes = []
    class_names = sorted(marker_def.keys())
    masks = []
    for t, m in dat.markers:
        for class_idx, classname in enumerate(class_names):
            if m in marker_def[classname]:
                mask = (t+ival[0] <= dat.axes[timeaxis]) & (dat.axes[timeaxis] < t+ival[1])
                # this one is quite expensive, we should move this stuff
                # out of the loop, or eliminate the loop completely
                # e.g. np.digitize for the marker to timeaxis mapping
                mask = np.flatnonzero(mask)
                if len(mask) != expected_samples:
                    # result is too short or too long, ignore it
                    continue
                # check if the new cnt shares at least one timepoint
                # with the new samples. attention: we don't only have to
                # check the ival but also the marker if it is on the
                # right side of the ival!
                times = dat.axes[timeaxis].take(mask)
                if newsamples is not None:
                    if newsamples == 0:
                        continue
                    if (len(np.intersect1d(times, new_sample_times)) == 0 and
                        t < new_sample_times[0]):
                        continue
                masks.append(mask)
                classes.append(class_idx)
    if len(masks) == 0:
        data = np.array([])
    else:
        data = dat.data
    axes = dat.axes[:]
    names = dat.names[:]
    units = dat.units[:]

    return dat.copy(data=data, axes=axes, names=names, units=units)

def prep_epoch(data, ival, timeaxis=-2, newsamples=None, start_marker="START", end_marker="END", method="offline", package="wyrm_to_mne"):
    cnt = data
    ival_in_s=(ival[1]-ival[0])/1000.
    marker_def={"epo_win":"epo_"+str(ival_in_s)+"s"}
    if method=="offline":
        #ADD event markers to data
        cnt = add_repetitive_events_wyrm(cnt, ival, marker_def["epo_win"], start_marker=start_marker,end_marker=end_marker, method="all")
        if not cnt: return [], []
    if method=="online":
        cnt = add_repetitive_events_wyrm(cnt, ival, marker_def["epo_win"], method="all")#online only makes sense to put events to the onset, offset , all
        if not cnt: return [], []
#            timestamp=0
#            onlymarker = [[timestamp, marker_def["epo_win"]]]
#            cnt.markers = onlymarker


    ##CHECK NEWSAMPLES EVENTS - in wyrm
    #code from wyrm.processing.segment_data  - if it is not at least a new epoch it returns empty array - not necessary in wyrm because segment_data use it already - but there is no problem to repeat it
    cnt=check_newsamples(cnt, marker_def, ival, newsamples=newsamples)


    return cnt, marker_def

def assert_epoch_sampling(data_fs, event_segment, epoch_ival, chunksize=None, subsample=None, subsample_min=100, event_samples_min=100, epoch_samples_min=100):
    """
    objective: test if subsample, event_segment, epoch_ival don't pass  min and max range
    """
    subsample_min=subsample_min #samples/s
    subsample_max=data_fs #samples/s
    ts_min = int( (1/float(subsample_max))*(10**(3)) ) #ms
#    ts_max = int( (1/float(subsample_min))*(10**(3)) ) #ms

    event_segment_min = int(ts_min*event_samples_min) # ms
    #event_segment_max = int(ts_max*event_samples_max)

    epoch_segment = epoch_ival[1]-epoch_ival[0] #ms
    epoch_segment_min = int(ts_min*epoch_samples_min) #ms


    if event_segment<event_segment_min:
        event_segment=event_segment_min

    if epoch_segment<epoch_segment_min:
        epoch_segment=epoch_segment_min
        epoch_ival[1]=epoch_ival[0]+epoch_segment

    #Make subsample depend on smaller segment
    if event_segment<=epoch_segment:
        subsample_min = int(
                (event_samples_min/float(event_segment)) * (10**3)
                )  #samples/s
    else:
        subsample_min = int(
                (epoch_samples_min/float(epoch_segment)) * (10**3)
                )  #samples/s


    if subsample:
        if chunksize:
        #1.Subsample needs to give minimum number to epoch subsample needs to be a multiple of chunksize; at least 100 points per s
            if not subsample % chunksize == 0:
                m=1
                previous_sub=subsample
                while True:
                    subsample=int(math.floor(data_fs/chunksize))*m
                    if subsample>=previous_sub and data_fs % subsample==0:
                        break
                    if m>chunksize:
                        subsample=data_fs
                        break
                    m+=1

            if subsample<subsample_min:
                m=1
                while True:
                    subsample=int(math.floor(data_fs/chunksize))*m
                    if subsample>=subsample_min and data_fs % subsample==0:
                        break
                    if m>chunksize:
                        subsample=data_fs
                        break
                    m+=1

        if subsample<subsample_min:
            subsample=subsample_min
        if subsample>=subsample_max:
            subsample=subsample_max

    return event_segment, epoch_ival, subsample

def epoch_data(data, ival, marker_def={"epo_win":"epo_s"}, average=False, event_id=None, newsamples=None, baseline=(None, None), detrend=1, plotlog=False, rej_max_peaktopeak=None, rej_min_peaktopeak=None, proj=True, method="offline", package="mne"):
    """
        3.4 Epoching: Segmentation in Epochs:
                1s epochs

        epoch_ival=[] #ms
    """
    assert ival[0] <= ival[1]
    epo=None
    cnt=data
    #create epoch
    if package=="wyrm":
        timeaxis=-2

        #detrend and remove baseline
        if detrend==1 or not detrend:
            """if no DC offset is preferred (zeroth order detrending), either turn off baseline correction, as this may introduce a DC shift, or set baseline correction to use the entire time interval (will yield equivalent results but be slower)."""
            if baseline: baseline=ival#None, None does baseline correction og all - basically removes the DC offset - average of all epoch
        if detrend:
            #0 is a constant (DC) detrend, 1 is a linear detrend
            cnt = detrend(cnt, order=detrend, axis=timeaxis)
        #epoch
        epo = wyrmproc.segment_dat(cnt, ival, marker_def, newsamples=newsamples)
        if baseline:
            epo = wyrmproc.correct_for_baseline(epo, ival)  #DC offset
        if average:
            epo = wyrmproc.calculate_classwise_average(epo)

    if package=="mne":
        raw=data
        event_id=event_id
        logger.debug("MNE IVAL ARE in SECONDS")
        ival_s=[x * (10**(-3)) for x in ival]
        #events
        logger.debug("#WARNING initial_event=True - Only works from version >= 0.16 mne ")
        min_duration=0#1/raw['sfreq']
        events = mne.find_events(raw, initial_event=True, shortest_event=1, min_duration=min_duration)
        logger.info("\n>> Events Found: {}".format(events))
        if plotlog:
            logger.warning('Found {} events, first 2 events: {}'.format(len(events), events[:2]))
            plot_events_raw(raw, event_id)


        #pick only epo events no start or stop
        events = mne.pick_events(events, include=[102]) #102=epo events
        ##EPOCHING
        #detrend and remove baseline
        if detrend==1 or not detrend:
            """if no DC offset is preferred (zeroth order detrending), either turn off baseline correction, as this may introduce a DC shift, or set baseline correction to use the entire time interval (will yield equivalent results but be slower)."""
            if baseline: baseline=(None, None)#None, None does baseline correction og all - basically removes the DC offset?!


        #epoch
        tmin=ival_s[0] #s
        tmax=ival_s[1] #s
        epoch=mne.Epochs(raw, events, event_id=event_id, tmin=tmin,tmax=tmax, baseline=baseline, proj=proj, detrend=detrend, on_missing='warning', reject_by_annotation=True)
        epo=epoch.copy()
#        pdb.set_trace()

        #reject bad epochs
        #continuous artifacts annotation
        epo.drop_bad()  #Need to be dropped existing marked annotations
        logger.debug("#BUG if not dropped continuos artifacts")
        #epoch artifacts
        if rej_max_peaktopeak or rej_min_peaktopeak:
            epo=artifact_rejection_epoch(epo, rej_max_peaktopeak=rej_max_peaktopeak, rej_min_peaktopeak=rej_min_peaktopeak, plotlog=plotlog, package="mne")
#            pdb.set_trace()

        #average
        if average:
            epo=epo.average()
            if plotlog:
                epo.plot()
#            pdb.set_trace()

        #plotlog
        if plotlog:
            epoch.plot(block=True)
            epo.plot(block=True) #IT seems it removes rejections
#    pdb.set_trace()
    return epo


def remove_baseline(data, ival, package="mne"):
    """3.5 Remove baseline of epochs: TODO: INSIDE of epoch function"""
    if package=="wyrm":
        data = wyrmproc.correct_for_baseline(data, ival)

    return data

def epoch_average(epo, plotlog=False, package="mne"):
    evo=None
    if package=="wyrm":
        epoav = wyrmproc.calculate_classwise_average(epo)
    if package=="mne":
            evo=epo.average()
            logger.debug("#NOTE doing average you get evoked type signal")
            if plotlog:
                evo.plot()
                logger.debug(epoav.plot.__code__.co_varnames)


    return evo
#FREQUENCY ANALYSIS
#---------------


def psd(data, picks=None, n_fft=256, n_per_seg=None, n_overlap=0, fmin=.5, fmax=60, tmin=None, tmax=None, method="welch", package="mne"):
    """
    spectral densities can be estimated using a multitaper method with digital prolate spheroidal sequence (DPSS) windows, a discrete Fourier transform with Hanning windows, or a continuous wavelet transform using Morlet wavelets.
    3.7 PSD:
                3.7.1 FFT 0.5Hz resolution?
                3.7.2 10% hanning window with variance correction? - windowed with a Hamming window n_fft=n_per_seg
    """

    if package=="mne":
        sfreq=data.info['sfreq']
        if method=="welch":
            """
                n_fft : int
                    The length of FFT used, must be ``>= n_per_seg`` (default: 256).
                    The segments will be zero-padded if ``n_fft > n_per_seg``.
                    If n_per_seg is None, n_fft must be <= number of time points
                    in the data.
                n_overlap : int
                    The number of points of overlap between segments. Will be adjusted
                    to be <= n_per_seg. The default value is 0.
                n_per_seg : int | None
                    Length of each Welch segment (windowed with a Hamming window). Defaults
                    to None, which sets n_per_seg equal to n_fft.
                    If n_per_seg is None n_fft is not allowed to be > n_times. If you want zero-padding, you have to set n_per_seg to relevant length.

                win_size = n_fft / float(sfreq) - welch segment
                n_fft = = int(sfreq / fftresolution) # the FFT size (n_fft). Ideally a power of 2
                fft bin resolution : sfreq/n_fft where sfreq is the input signal's sampling rate and N is the number of FFT

            """
            logger.debug("TODO: sera que ao alterar a resolucao para ir buscar mais amostras ele esta a fazer - e.g.:")
#            pdb.set_trace()

            #resolution
#            n_times=data.data.shape
#            logger.debug("n_times: {}".format(n_times))
#            n_fft = int(sfreq / fftresolution) #samples fft
#            n_per_seg = int(n_fft/3) #samples per segment
#            found = False
#            startpower = 8
#            if n_fft<=(2**startpower):
#                n_fft=2**startpower
#                found = True
#            i=0
#            while not found:
#                if n_fft>(2**(startpower+i)) and n_fft<=(2**(startpower+i+1)):
#                    n_fft=2**(startpower+i+1)
#                    found=True
#                i+=1




#            pdb.set_trace()
            psd, freqs = mne.time_frequency.psd_welch(data, picks=picks,
                                                      fmin=fmin,fmax=fmax,
                                                      tmin=tmin,tmax=tmax,
                                                      n_fft=n_fft,
                                                      n_per_seg=n_per_seg,
                                                      n_overlap=n_overlap
                                                      )

            #true resolution
            fftresolution = sfreq/float(n_fft)
            if n_per_seg is None: n_per_seg=n_fft
    logger.debug("psd_shape: {}, freqs_shape: {}, fftresolution: {}, n_fft: {}, n_per_seg: {}".format(psd.shape, freqs.shape, fftresolution, n_fft, n_per_seg))


    return psd, freqs, fftresolution, n_fft


def psd_smooth(psd, window_length=11, polyorder=5, method="savgol"):
    psd_smooth=None
    if method=="savgol":
        #from scipy.signal import savgol_filter
        psd_smooth = savgol_filter(psd,
                               window_length=window_length,
                               polyorder=polyorder)
    return psd_smooth

def psd_noise(fmin=0, fmax=60, fresolution=1, a=0.9, method="pink"):

    freqs=None
    psd=None
    if fmin==0:
        fmin=fresolution
    if method=="pink":

        freqs= np.arange(fmin, fmax+fresolution, fresolution)
        psd= np.array([[1/float(f**a) for f in freqs.tolist()]])

    slope, intercept, r, p, se = stats.linregress(np.log(freqs),
                                                  np.log(psd))
    r2=r**2
    pdb.set_trace()
    psdtypeused="{} noise, r2 {}".format(method, r2)
    plot_psd(psd, freqs, psdtypeused=psdtypeused)

    return psd, freqs, slope, intercept, r, p, se

def psd_prep_extraction(psd, freqs, picks=None, chanaxis=0, ch_names_ordered=None, psdsmooth=True, pink_max_r2=0.9, ax=False):
    """PREPARATION OF ONE CHANNEL PSD - pick ch or average psds"""
    ch_name="unknown"
    if picks and len(picks)==1:  #Average psds picks
        psd = psd[picks[0]]  #np.array([ psd[picks[0]] ])
        if ch_names_ordered: ch_name=ch_names_ordered[picks[0]]
    else:
        psd = psd.mean(chanaxis) #shape array (L,)
        ch_name="average"


    PSD = np.array([psd])  #shape(1L,L)

    #PSD_SMOOTH
    if psdsmooth:
        psd = psd_smooth(psd)#shape array (L,)
        PSD_SMOOTH = np.array([psd]) #shape(1L,L)

    #Test pink noise
    psd_linregress={}
    noisysignal=None
    try:
        slope, intercept, r, p, se = stats.linregress(np.log(freqs),
                                                          np.log(psd))
        psd_linregress={"slope":slope, "intercept":intercept, "r":r, "p":p, "se":se}
        if pink_max_r2 and r:
            if r**2 > pink_max_r2:
                noisysignal=True
            else:
                noisysignal=False
    except:
        pass

     #Create plot fig
    if ax:
        PSD_PINK = np.array([1/(freqs)])
        logger.debug("#WARNING PSD array needs to be numpy.ndarray with format ([ [ ] ]) for concatenaion along axis=0")
        psds= np.concatenate((PSD, PSD_SMOOTH, PSD_PINK), axis=0)
        if pink_max_r2:
            r_leg = '$1/f$ fit ($R^2={:0.2}$)'.format(r**2)
        else:
            r_leg = ''
        plot_psd(psds, freqs, show_means=False, psd_legends=["EEG PSD", "Smoothed PSD",r_leg], psdtypeused="PSD_PREP_EXTRACTION")

    return psd, noisysignal, ch_name, psd_linregress


def calculate_iaf(psd, freqs, picks=None, psdsmooth=True, alpha_fmin=8, alpha_fmax=12, pink_max_r2=0.9,ax=False):
    """
    3.8 Alpha Peak detection - Identify the IAF(individual Alpha frequency)

    ***SIMPLE***
    The individual alpha frequency (IAF) peak can be defined as the frequency associated to the strongest EEG power within the extended alpha range (Klimesch, 1999).
In our paper about EEG rhythm sources in patients affected by Alzheimer and Frontotemporal dementia (Caso et al. 2012), we calculated the IAF as follows:
- Spectral estimation for each EEG channel, using an FFT based method
- Global power spectrum calculation, as average of all individual channel spectra
- Selection of the IAF as the frequency showing a power peak within the extended alpha range (7-13 Hz)

Caso F, Cursi M, Magnani G, Fanelli G, Falautano M, Comi G, Leocani L, Minicucci F. Quantitative EEG and LORETA: valuable tools in discerning FTD from AD? Neurobiol Aging. 2012 Oct;33(10):2343-56
Klimesch W. EEG alpha and theta oscillations reflect cognitive and memory performance: a review and analysis. Brain Res Brain Res Rev. 1999 Apr;29(2-3):169-95. Review.
    """
    paf = None  #peak alphs frequency
    IAF = None
    psd, noisysignal, ch_name = psd_prep_extraction(psd, freqs, picks=picks, psdsmooth=psdsmooth, pink_max_r2=pink_max_r2, ax=ax)
    #alpha_band
    alpha_band = np.logical_and(freqs >= alpha_fmin, freqs <= alpha_fmax)
    if noisysignal: #ruido pink noise
        paf = None
    else:
        paf_idx = np.argmax(psd[alpha_band])
        paf = freqs[alpha_band][paf_idx]
    #only one IAF
    IAF = paf
    if IAF:
        logger.info("IAF: " + str(IAF))
    else:
        logger.info("ERROR:Something went wrong with IAF; Using standard IAF")
        IAF = 10

    return IAF




def get_bands(IAF):
    """
    3.9 BANDS
                Delta Band: 0.2-4 hz (standard)
                Theta Band: IAF–6 Hz to IAF–3 Hz(standard: 4-8Hz)?
                Alpha Band: Lower Alpha = IAF‐2 Hz to IAF; upper Alpha = IAF to IAF+2 Hz (standard:8-12)?
                SMR BAND: individual = IAF+2Hz to IAF  + 4hz (standard 12– 15 Hz for SMR NF protocol)?
                Beta Band: 21–35 Hz (standard)

    As suggested in a recent paper (Babiloni et al 2012), referencing to the IAF, you can calculate the edges of bands of your interest, i.e. delta (IAF-8 to IAF-6 Hz), theta (IAF-6 to IAF-4 Hz), alpha 1 (IAF-4 to IAF-2 Hz), alpha 2 (IAF-2 to IAF Hz), and alpha 3 (IAF to IAF+2 Hz). For example, if power peak in the extended alpha range was observed at 10 Hz (IAF), the frequency bands of interest were as follows: 2–4 Hz (delta), 4–6 Hz (theta), 6–8 Hz (alpha 1), 8–10 Hz (alpha 2), 10–12 Hz (alpha 3).
Babiloni C, Stella G, Buffo P, Vecchio F, Onorati P, Muratori C, Miano S, Gheller F, Antonaci L, Albertini G, Rossini PM. Cortical sources of resting state EEG rhythms are abnormal in dyslexic children. Clin Neurophysiol. 2012 Dec;123(12):2384-91.

Mike Cohen:
    Brain rhythm frequency bands include delta (2 – 4 Hz),
theta (4 – 8 Hz), alpha (8 – 12 Hz), beta (15 – 30 Hz), lower gamma (30 – 80 Hz), and upper gamma
(80 – 150 Hz). These are not the only frequency bands; there are oscillations in the subdelta
and omega (up to 600 Hz) ranges, but the frequency bands that are most typically associated
with cognitive processes in the literature are between 2 Hz and 150 Hz. This grouping is not
arbitrary but, rather, results from neurobiological mechanisms of brain oscillations, including
synaptic decay and signal transmission dynamics (Buzsaki 2006; Buzsaki and Draguhn
2004; Kopell et al. 2010; Steriade 2005, 2006; Wang 2010). However, there are no precise
boundaries defining the bands. You might see theta referred to as 3 – 9 Hz or 3 – 7 Hz or 4 – 7
Hz. Furthermore, individual differences in peak frequencies have been linked to a number
of individual characteristics, including brain structure, age, working memory capacity, and
brain chemistry (more on this topic in section 35.4).


    """

    #NOTE: Posteriori from band range you can get IAF

    bands = {"delta" : {"band":(IAF - 8 , IAF - 6 )},
          "eye_blink": {"band":(3, 5)},
          "theta": {"band":(IAF - 6 , IAF - 2 )},
          "alpha": {"band":(IAF - 2 , IAF + 2 )},
          "lower_alpha": {"band":(IAF - 2 , IAF )},
          "upper_alpha": {"band":(IAF , IAF + 2 )},
          "SMR": {"band":(IAF+2, IAF+5)},
          "beta": {"band":(IAF+5, 35)},
          "gamma": {"band":(35, 100)},
          "muscle_movements": {"band":(22, 30)},
          "high_frequency_artifacts":{"band":(45, 60)}
          }

    return bands

def chs_to_extract_feature(rewardfeature="SMR"):
    """
    ch_feature: list, choose one or more channels to extract feature
    ch_iaf: None | list, choose one or more channels to extract feature

    NOTE: Add the feature to
    """

    ch_feature=None
    ch_iaf=None

    if rewardfeature=="alpha":
        ch_feature=["Pz"]  #needs to be a list or None
        ch_iaf=["Pz"]
    if rewardfeature=="upper_alpha":
        ch_feature=["Pz"]  #needs to be a list or None
        ch_iaf=["Pz"]
    if rewardfeature=="SMR":
        ch_feature=["Cz"]
        ch_iaf=["Cz"]
    if rewardfeature=="SMR_NO_INHIBIT":
        ch_feature=["Cz"]
        ch_iaf=["Cz"]
    if rewardfeature=="allbands_Cz_pipeline":
        ch_feature=["Cz"]
        ch_iaf=["Cz"]
    if rewardfeature=="allbands_Pz_pipeline":
        ch_feature=["Pz"]
        ch_iaf=["Pz"]

    #assert
    if not ch_feature: raise RuntimeError('Ch Feature not defined: see chs_to_extract_feature() function!')

    return ch_feature, ch_iaf

def get_reward_inhibit_bands(bands, rewardfeature="SMR", IAF=10):
    """
    Deffinitions of reward and inhibit bands based on feature

    NOTE: If Adding new features, you also need to add above the chs to extract the feature, chs_to_extract_feature()
    """
    inhibit_bands=None
    reward_bands=None
    if rewardfeature=="alpha":
        inhibit_bands={"theta": bands["theta"], "beta": bands["beta"]}#{"eye_blink": bands["eye_blink"], "high_frequency_artifacts": bands["high_frequency_artifacts"]}
        reward_bands={"alpha":bands["alpha"]}
    if rewardfeature=="upper_alpha":
        inhibit_bands={"theta": bands["theta"], "beta": bands["beta"]}#{"eye_blink": bands["eye_blink"], "high_frequency_artifacts": bands["high_frequency_artifacts"]}
        reward_bands={"upper_alpha":bands["upper_alpha"]}
    if rewardfeature=="SMR":
        inhibit_bands={"theta": bands["theta"], "beta": bands["beta"]}#{"eye_blink": bands["eye_blink"], "high_frequency_artifacts": bands["high_frequency_artifacts"]}
        reward_bands={"SMR":bands["SMR"]}
    if rewardfeature=="SMR_NO_INHIBIT":
        inhibit_bands={}#{"eye_blink": bands["eye_blink"], "high_frequency_artifacts": bands["high_frequency_artifacts"]}
        reward_bands={"SMR":bands["SMR"]}

    if rewardfeature=="allbands_Cz_pipeline":
        inhibit_bands={"delta":bands["delta"],"theta": bands["theta"], "beta": bands["beta"], "eye_blink": bands["eye_blink"], "high_frequency_artifacts": bands["high_frequency_artifacts"]}
        reward_bands={"alpha":bands["alpha"],"lower_alpha":bands["lower_alpha"],"upper_alpha":bands["upper_alpha"], "SMR":bands["SMR"]}
        
    if rewardfeature=="allbands_Pz_pipeline":
        inhibit_bands={"delta":bands["delta"], "theta": bands["theta"], "beta": bands["beta"], "gamma": bands["gamma"]}
        reward_bands={"alpha":bands["alpha"],"lower_alpha":bands["lower_alpha"],"upper_alpha":bands["upper_alpha"], "SMR":bands["SMR"]}

    #assert
    if not reward_bands: raise RuntimeError('Reward bands not defined: see get_reward_inhibit_bands() function!')


    return reward_bands, inhibit_bands



def calculate_ch_band_means(ch_psd, ch_name, freqs, bands, data_unit='V', psdlogarithm=True, datatype="feedback"):
    if not bands: return None
    if psdlogarithm:
        logger.debug("#TODO Should you do logarithm and then do the means, or first do the mean an then trasform to logarithm?")
        ch_psd = 10 * np.log10(ch_psd)
    for band_key in bands:
        try:
            band_value=bands.get(band_key, "not found" )
            band_range = band_value.get("band", "not found" )
            logical_band = np.logical_and(freqs >= band_range[0], freqs <= band_range[1])
            mean = ch_psd[logical_band].mean(0)
            std = ch_psd[logical_band].std(0)
            bands[band_key][datatype+"_mean"] = mean
            bands[band_key][datatype+"_std"] = std
            bands[band_key][datatype+"_ch"] = ch_name
            bands[band_key][datatype+"_units"] = data_unit

            #bands[band_key][datatype+"_ch_psd_logical_band"] = ch_psd[logical_band].tolist()


        except Exception as e:
            logger.error('\n>> Problems calculating chs band means? {} ; band_key {}, not a band?'.format(e, band_key))

    return bands

def copy_bands_datatype(bands, input_dt='feedback', output_dt='threshold'):
    """copy bands datatype values to another datatype"""
#    for band_key in bands:
#        try:
#            bands[band_key][out_key] = bands[band_key][in_key]
#        except Exception as e:
#            logger.error('\n>> Problems calculating chs band means? {} ; band_key {}, not a band?'.format(e, band_key))
    pass

def threshold(band_value, reward_level=0, inhibit_level=1, bandtype="reward", datatype="threshold"):
    """
    define threshold
    """
    mean = band_value[datatype+"_mean"]
    std = band_value[datatype+"_std"]
    if bandtype=="reward":
        return mean + reward_level*std# #mean is 50%;  -(0.38*std) assuming normal distribution it is a trheshold where the person was above 65% of the time and
    if bandtype=="inhibit":
        return mean+inhibit_level*std #assuming normal distribution (84.1% below the threshold)

    return mean

def feedback(band_value, reward_level=0, inhibit_level=0, bandtype="reward", datatype="feedback"):
    """
    define feedback
    """
    mean = band_value[datatype+"_mean"]
    std = band_value[datatype+"_std"]
    if bandtype=="reward":
        return mean+reward_level*std
    if bandtype=="inhibit":
        return mean+inhibit_level*std

    return mean

def calculate_features(bands, reward_level=0, inhibit_level=0, bandtype="reward", datatype="threshold"):
    """
    calculation for all bands of feedback and threshold
    """
    for band_key in bands:
        try:
            band_value=bands.get(band_key, None )
            if band_value:
                if datatype== "threshold":
                    bands[band_key]["threshold"]=threshold(band_value, reward_level=reward_level, inhibit_level=inhibit_level, bandtype=bandtype)
                if datatype== "feedback":
                    bands[band_key]["feedback"]=feedback(band_value, reward_level=reward_level, inhibit_level=inhibit_level, bandtype=bandtype)
                #ADD other datatype methods
        except Exception as e:
            logger.error('\n>> Problems calculating bands feedback_threshold? {} ; band_key {}, not a band?'.format(e, band_key))

    return bands

def get_band_features(ch_psd, ch_name, freqs, bands, data_unit='V', psdlogarithm=True, bandtype="reward", feature="SMR", datatype="feedback", reward_level=0, inhibit_level=0):
    """
    3.10 Thresholds
                reward band: mean of band power during rest state;
                inhibit band: mean power + 1 sd
        Feedbacks:
            Mean of band power
    """
    if not bands: return None

    #calculate ch band means
    bands = calculate_ch_band_means(ch_psd, ch_name, freqs, bands, data_unit=data_unit, psdlogarithm=psdlogarithm, datatype=datatype)
    #calculate features from means
    bands = calculate_features(bands, reward_level=reward_level, inhibit_level=inhibit_level, bandtype=bandtype, datatype=datatype)

    #update reward and inhibit bands


    return bands



def get_faa():
    """frontal alpha assimetry feature
    REFERENCE: https://www.science.mcmaster.ca/pnb/images/stories/courses/psych4d6/thesisabstracts/Internals/Becker/2015_16gauder_abstract.pdf
     alpha power between the right FP2 (R) and left FP1 (L) electrodes using (𝑅−𝐿)/(𝑅+𝐿)
      ratio of 0 indicates alpha power symmetry, a ratio less than 0 would indicate right-FAA, and a ratio greater 0 indicates left-FAA.
     1.normalize
     2.bandpass filter between 7Hz to 13Hz - (mine:8hz-12Hz)
     3.fast fourier transform
     4.artifacts detection: artifacts could be caused by shifts or movement of the headset by the participant, improper headset placement, or physical movements like eye blinks
     5.Visual display of FAA was smoothed over small time periods to make the movement of the FAA bar more intuitive
     6.threshold in both groups was calculated every 15 seconds
     7.proportion of time that the participant’s FAA ratio was within the threshold in the last 15 seconds was calculated
     7.
     Standard adaptative algorithm:
         proportion was less than 75% of the time, the threshold was
increased until this proportion was greater than 75% of the time

    Progressive adaptative algorithm:
         checking if the proportion of time that the participant’s FAA ratio was within the threshold in the last 15 seconds was greater than 75%
          If true, the threshold decreased
in size by 10%.
        If the participant failed to decrease the threshold for an entire 4 minute block, then the threshold would increase by (1/(f=0.9)^2) pink noise

    """
    pass

def get_learning_performance():
    """
    Participant learning curves
    Calculated for:
        1.understand changes in learning performance
        2.Thresholding optimization of individual learning

    pre-run performance
    post-run performance
    """
    pass


def feature_extraction():
    """
    """
    pass



"""5.REALTIME"""


"""6.VISUALIZATION"""
def plot_segment(raw, time_ival=[10, 15], n_ch_max=10):
    start, stop = raw.time_as_index(time_ival)  # 100 s to 115 s data segment
    data, times = raw[:, start:stop]
    print(data.shape)
    print(times.shape)
    #data, times = raw[2:20:3, start:stop]  # access underlying data
    n_channels = raw.info['nchan']
    order = np.arange(n_channels) #can change the order if wanted
    if n_channels>10: #plot no more than 10
        n_channels=10
    raw.plot(n_channels=n_channels, order=order, block=True)

def plot_psd_mean(psd, freqs, psdtypeused="welch"):
    logger.debug("#NOTE: psd:type np.ndarray - ([[]]); freqs: type np.array ([])")
    f, axs = plt.subplots()
    psds = 10 * np.log10(psd)  #Using log
    psds_mean = psds.mean(0)  #Mean of channels axis
    psds_std = psds.std(0)  #std of channels axis
    axs.plot(freqs, psds_mean, color='k')
    axs.fill_between(freqs, psds_mean - psds_std, psds_mean + psds_std,
                    color='k', alpha=.5)
    axs.set(title=psdtypeused+' PSD_MEAN', xlabel='Frequency',
           ylabel='Power Spectral Density (dB)')
    plt.show()

def plot_psd(psds, freqs, psd_legends=None, show_means=False, psdtypeused="welch", log_scale=True):
    logger.debug("#NOTE: psd:type np.ndarray - ([[]]) for list; but for plot: psd and freqs: type np.array ([])")
    f, axs = plt.subplots()
    if log_scale: psds = 10 * np.log10(psds)  #Using log
    psds_mean = psds.mean(0)  #Mean of channels axis
    psds_std = psds.std(0)  #std of channels axis
    pl_leg=[]
    for i, p in enumerate(psds):
        if psd_legends:
            pl, =axs.plot(freqs, p, label="PSD #{}".format(psd_legends[i]))
        else:
            pl, =axs.plot(freqs, p, label="PSD #{}".format(i))
        pl_leg.append(pl)
    axs.legend(handles=pl_leg)
    if show_means:
        axs.fill_between(freqs, psds_mean - psds_std, psds_mean + psds_std, color='k', alpha=.5)
    axs.set(title=psdtypeused+' PSD', xlabel='Frequency', ylabel='Power Spectral Density (dB)')
    plt.show()


def plot_events_raw(raw, event_id):
    events = mne.find_events(raw)
    print('Found %s events, first five:' % len(events))
    print(events[:5])
    #plot the events found
    mne.viz.plot_events(events, raw.info['sfreq'], raw.first_samp, color=None, event_id=event_id)
    n_channels = raw.info['nchan']
    order = np.arange(n_channels) #can change the order if wanted
    if n_channels>10: #plot no more than 10
        n_channels=10
    raw.plot(events=events, n_channels=n_channels, order=order, block=True)
"""

10.SOURCE-LEVEL ANALYSIS
7.STATISTICS
8.MACHINE LEARNING (DECODING, ENCODING, MVPA)
9.CONNECTIVITY
"""

if __name__=="__main__":
    psd_noise(fmin=0, fmax=60, fresolution=1, a=0.9, method="pink")
