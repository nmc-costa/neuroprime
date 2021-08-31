# -*- coding: utf-8 -*-
from __future__ import division  #very important -don't forget
#signal acquisition & processing
import libmushu.driver.labstreaminglayer
import os
import numpy as np
import json
import struct
import wyrm
# My functions
import neuroprime.src.utils.myfunctions as my
#Module logger
import logging
logging_level=logging.DEBUG
logger = my.setlogfile(modulename=__name__, setlevel=logging_level, disabled=True)

class save_outlet(object):
    
    def configure(self, channel_number=32,fs=1000 ):
        """Configure the lsl device.

        This method looks for open lsl streams and picks the first `EEG`
        and `Markers` streams and opens lsl inlets for them.

        Note that lsl amplifiers cannot be configured via lsl, as the
        protocol was not designed for that. You can only connect (i.e.
        subscribe) to devices that connected (publishing) via the lsl
        protocol.

        """
        self.n_channels = channel_number
        self.channels = ['Ch %i' % i for i in range(self.n_channels)]
        self.fs = fs
        logger.debug('Configuration done.')
        
        
    def start(self, filename=None):
        # prepare files for writing
        self.write_to_file = False
        if filename is not None:
            self.write_to_file = True
            filename_marker = filename + '.marker'
            filename_eeg = filename + '.eeg'
            filename_meta = filename + '.meta'
            filename_txt = filename + '.txt'
            for filename in filename_marker, filename_eeg, filename_meta:
                if os.path.exists(filename):
                    logger.error('A file "%s" already exists, aborting.' % filename)
                    raise Exception
            self.fh_eeg = open(filename_eeg, 'wb')
            self.fh_marker = open(filename_marker, 'w')
            self.fh_meta = open(filename_meta, 'w')
            self.fh_txt = open(filename_txt, 'w')
            # write meta data
            meta = {'Channels': self.channels,
                    'Sampling Frequency': self.fs,
                    'Amp': str('outlet_amp')
                    }
            json.dump(meta, self.fh_meta, indent=4)
    

        # zero the sample counter
        self.received_samples = 0
        
    def get_data(self, in_sample,sample_stamp,in_marker,marker_stamp):
        """Get data from the amplifier.
    
        This method is supposed to get called as fast as possible (i.e
        hundreds of times per seconds) and returns the data and the
        markers.
    
        Returns
        -------
        data : 2darray
            a numpy array (time, channels) of the EEG data
        markers : list of (float, str)
            a list of markers. Each element is a tuple of timestamp and
            string. The timestamp is the time in ms relative to the
            onset of the block of data. Note that negative values are
            *allowed* as well as values bigger than the length of the
            block of data returned. That is to be interpreted as a
            marker from the last block and a marker for a future block
            respectively.
    
        """
        # get data and marker from underlying amp libmushu.driver.labstreaminglayer
        """
        Retrieve an estimated time correction offset for the given stream.
        The precision of these estimates should be below 1 ms (empirically within +/-0.2 ms).
        time_correction Returns the current time correction estimate. This is the number that 
        needs to be added to a time stamp that was remotely generated via 
        local_clock() to map it into the local clock domain of this 
        machine."""
        tc_m = 0 #no offset
        tc_s = 0 #no offset
        
        markers, m_timestamps = [in_marker], marker_stamp
        # flatten the output of the lsl markers, which has the form
        # [[m1], [m2]], and convert to string
        markers = [str(i) for sublist in markers for i in sublist]

        # 
        samples, timestamps = in_sample, sample_stamp
        samples = np.array(samples).reshape(-1, self.n_channels)

        t0 = timestamps[0] + tc_s #get first sample timestamp + time_correction 
        m_timestamps = [(i + tc_m - t0) * 1000 for i in m_timestamps]
        
        data, marker = samples , zip(m_timestamps, markers)
        
    
        # duration of all blocks in ms except the current one
        duration = 1000 * self.received_samples / self.fs
        
        """UPDATE REMOVED TCP"""
    
        # save data to files
        if self.write_to_file:
            for m in marker:
                self.fh_marker.write("%f %s\n" % (duration + m[0], m[1]))
            self.fh_eeg.write(struct.pack("f"*data.size, *data.flatten() ))
            self.fh_txt.write("SAMPLE_STAMP:{}\nSAMPLE_MUSHU:{}\nSAMPLE_PYLSL:{}\nMARKERS:{}\n\n".format(timestamps,samples,in_sample,marker) )
            #self.fh_txt.write("SAMPLE_STAMP:{}\nSAMPLE:{}\nMARKER_STAMP:{}\nDURATION:\n".format(sample_stamp,in_sample,marker_stamp,in_marker, duration) )
        self.received_samples += len(data)
        if len(data) == 0 and len(marker) > 0:
            logger.error('Received marker but no data. This is an error, the amp should block on get_data until data is available. Marker timestamps will be unreliable.')
        
        return  samples,timestamps, marker
    
    
    
    



