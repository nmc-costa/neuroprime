# -*- coding: utf-8 -*-

"""Example program to demonstrate how to read a multi-channel time-series
from LSL in a chunk-by-chunk manner (which is more efficient)."""

from pylsl import StreamInlet, resolve_stream


"""EEG"""
# first resolve an EEG stream on the lab network
print("looking for an EEG stream...")
streams = resolve_stream('type', 'EEG')

# create a new inlet to read from the stream
inlet = StreamInlet(streams[0])

"""MARKERS"""
# first resolve a marker stream on the lab network
print("looking for a marker stream...")
streamsMARKER = resolve_stream('type', 'Markers')
    
# create a new inlet to read from the stream
inletMARKER = StreamInlet(streamsMARKER[0])

while True:
    # get a new sample (you can also omit the timestamp part if you're not
    # interested in it)
    chunk, timestamps = inlet.pull_chunk()
    if timestamps:
        print('**********************INLET_DATA*******************')
        print('SAMPLE_STAMP:'+str(timestamps))
        print('SAMPLE:'+str(chunk))
        
    marker,timestampM = inletMARKER.pull_sample()
    if timestampM:
        print('MARKER_STAMP:'+str(timestamps))
        print('MARKER:'+str(chunk))
        print(timestampM, marker)