# -*- coding: utf-8 -*-
"""
Adaptation by nmc-costa of https://github.com/dbdq/neurodecode stream player by Kyuhwa Lee, 2015

Stream Player
Stream signals from a recorded file on LSL network.
For Windows users, make sure to use the provided time resolution
tweak tool to set to 500us time resolution of the OS.
"""
from __future__ import (absolute_import, division, print_function)
import sys
if sys.version_info >= (3, 0): from builtins import * #not usable in python 2 because of pylsl



import time

import pylsl
import mne
import os
import wyrm
import wyrm.io
# My functions
import neuroprime.src.utils.myfunctions as my
#Module logger
import logging
logging_level=logging.DEBUG
logger = logging.getLogger(__name__)
logger.info('Logger started.')

import timeit
#NOTE
"""2.7 timeit.py:

if sys.platform == "win32":
    # On Windows, the best timer is time.clock()
    default_timer = time.clock
else:
    # On most other platforms the best timer is time.time()
    default_timer = time.time

In Python3.4 this has become

default_timer = time.perf_counter
I'd go with timeit.default_timer().
"""


def load_raw(filepath, server_data_unit='uV'):
    """INPORT/LOAD DATA
    """

    filenamepath, filetype =os.path.splitext(filepath)
    raw=None
    #MNE units is Volts
    if filetype==".fif":
        raw = mne.io.read_raw_fif(filepath, preload=True,verbose='ERROR') #V

    if filetype==".vhdr":
        raw = mne.io.read_raw_brainvision(filepath, preload=True) #uV->V

    if filetype==".meta":
        raw, event_id = my.mushu_to_mne(filepath, in_data_unit=server_data_unit) #mushu data . uV -> V

    #convert to server units
    data = raw._data
    factor=my.mne_unit_dict.get(server_data_unit, None)
    if not factor: raise RuntimeError("Add factor {} to mne_unit_dict!".format(server_data_unit))
    data=data*(1/factor)
    raw._data = data


    return raw

def stream_player(server_name, filepath, chunk_size,  server_data_unit='uV', auto_restart=False, high_resolution=False, verbose='timestamp', trigger_file=None, trigger_ch_name=None):
    """
    Params
    ======

    server_name: LSL server name.
    fif_file: fif file to replay.
    chunk_size: number of samples to send at once (usually 16-32 is good enough).
    auto_restart: play from beginning again after reaching the end.
    high_resolution: use perf_counter() instead of sleep() for higher time resolution
                     but uses much more cpu due to polling.
    trigger_file: used to convert event numbers into event strings for readability.
    verbose:
        'timestamp': show timestamp each time data is pushed out
        'events': show non-zero events whenever pushed out
    """
    #load raw
    raw=load_raw(filepath, server_data_unit=server_data_unit)
    if not raw: raise
    #choose picks
    event_ch = None
    if trigger_ch_name:
        try:
            event_ch = raw.ch_names.index(trigger_ch_name)
        except ValueError:
            pass
    else:
        raw.pick_types(eeg=True, meg=False, stim=False)


    sfreq = raw.info['sfreq']  # sampling frequency
    n_channels = len(raw.ch_names)  # number of channels

    if raw is not None:
        logger.info('Successfully loaded %s\n' % filepath)
        logger.info('Server name: %s' % server_name)
        logger.info('Sampling frequency %.1f Hz' % sfreq)
        logger.info('Number of channels : %d' % n_channels)
        logger.info('Chunk size : %d' % chunk_size)
        for i, ch in enumerate(raw.ch_names):
            logger.info('%d %s' % (i, ch))
        logger.info('Trigger channel : %s' % event_ch)
    else:
        raise RuntimeError('Error while loading %s' % filepath)

    # set server information
    sinfo = pylsl.StreamInfo(server_name, channel_count=n_channels, channel_format='float32',\
        nominal_srate=sfreq, type='EEG', source_id=server_name)
    desc = sinfo.desc()
    channel_desc = desc.append_child("channels")
    for ch in raw.ch_names:
        channel_desc.append_child('channel').append_child_value('label', str(ch))\
            .append_child_value('type','EEG').append_child_value('unit',server_data_unit)
    desc.append_child('amplifier').append_child('settings').append_child_value('is_slave', 'false')
    desc.append_child('acquisition').append_child_value('manufacturer', 'PyNFT').append_child_value('serial_number', 'N/A')
    outlet = pylsl.StreamOutlet(sinfo, chunk_size=chunk_size)

    if sys.version_info >= (3, 0):
        input('Press Enter to start streaming.')
    else:
        raw_input('Press Enter to start streaming.')#Python 2 implementation -put input()
    logger.info('\n>> Streaming started')

    idx_chunk = 0
    t_chunk = chunk_size / sfreq
    finished = False
#    t_start = timeit.default_timer() #chooses the best default timer depending on os and python version
    if high_resolution:
        t_start = time.perf_counter() #faster timer only in python3 - time.perf_counter()
    else:
        t_start = timeit.default_timer()

    # start streaming
    while True:
        idx_current = idx_chunk * chunk_size
        chunk = raw._data[:, idx_current:idx_current + chunk_size]
        data = chunk.transpose().tolist()
        if idx_current >= raw._data.shape[1] - chunk_size:
            finished = True
        if high_resolution:
            # if a resolution over 2 KHz is needed
            t_sleep_until = t_start + idx_chunk * t_chunk #Next chunk
            while time.perf_counter() < t_sleep_until:
                pass
        else:
            # time.sleep() can have 500 us resolution using the tweak tool provided.
#            t_wait = t_start + idx_chunk * t_chunk - timeit.default_timer()
#            if t_wait > 0.001:
#                time.sleep(t_wait)
            t_sleep_until = t_start + idx_chunk * t_chunk
            while timeit.default_timer() < t_sleep_until:
                pass

        outlet.push_chunk(data)
        if verbose == 'timestamp':
            logger.info('[%8.3fs] sent %d samples' % (timeit.default_timer(), len(data)))
        elif verbose == 'events' and event_ch is not None:
            event_values = set(chunk[event_ch]) - set([0])
            if len(event_values) > 0:
                if trigger_file is None:
                    logger.info('Events: %s' % event_values)
                else:
                    pass
        idx_chunk += 1

        if finished:
            if auto_restart is False:
                input('Reached the end of data. Press Enter to restart or Ctrl+C to stop.')
            else:
                logger.info('Reached the end of data. Restarting.')
            idx_chunk = 0
            finished = False
#            t_start = timeit.default_timer() #chooses the best default timer depending on os and python version
            if high_resolution:
                t_start = time.perf_counter()
            else:
                t_start = timeit.default_timer()




# sample code
if __name__ == '__main__':
    server_name = 'BrainVision RDA'#'Actichamp-0'
    server_data_unit='uV'
    chunk_size = 50  # chunk samples ; for a fs=1000Hz , 10 Samples are sent at a 10ms interval
    #filetoreplay
    folderdir='e2_sample'#folder inside "sampledata"
    filename='EG_S001_REST_ss01_b01_08102019_14h13m_rest_1'#
    filetype=".meta"#".vhdr"#".meta"
    filetoreplay= my.get_filetoreplay(folderdir=folderdir, filename=filename, filetype=filetype) #filepath "sampledata"
    #stream
    stream_player(server_name, filetoreplay, chunk_size, server_data_unit=server_data_unit, auto_restart=True)
