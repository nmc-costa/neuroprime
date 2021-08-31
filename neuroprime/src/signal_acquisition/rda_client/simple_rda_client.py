"""
Simple Python RDA client for the RDA tcpip interface of the BrainVision Recorder
It reads all the information from the recorded EEG,
prints EEG and marker information to the console and calculates and
prints the average power every second

Base code: https://www.brainproducts.com/downloads.php?kid=2&tab=5
26-04-2010

@author: nm.costa
"""
from __future__ import (absolute_import, division, print_function)
from builtins import * #all the standard builtins python 3 style

# needs socket and struct library
from socket import socket, AF_INET, SOCK_STREAM
from struct import unpack
import pylsl
import time
import numpy
class RDAMessageType:
    ''' RDA Message Types, negative values are for internal use only of RDA CLIENT
    The positive values were defined on the RDA server
    '''
    CONNECTED = -1      #: Connected to server
    DISCONNECTED = -2   #: Disconnected from server
    START = 1           #: Setup / Start info
    DATA16 = 2          #: Block of 16-bit data
    STOP = 3            #: Data acquisition has been stopped
    DATA32 = 4          #: Block of 32-bit floating point data
    NEWSTATE = 5        #: Recorder state has been changed
    IMP_START = 6       #: Impedance measurement start
    IMP_DATA = 7        #: Impedance measurement data
    IMP_STOP = 8        #: Impedance measurement stop
    INFO = 9            #: Recorder info Header, sent after connection and when setup is changed
    KEEP_ALIVE = 10000  #: Sent periodically to check whether the connection is still alive

# Marker class for storing marker information
class Marker:
    def __init__(self):
        self.position = 0
        self.points = 0
        self.channel = -1
        self.type = ""
        self.description = ""

# Helper function for receiving whole message
def RecvData(socket, requestedSize):
    returnStream = ''
    while len(returnStream) < requestedSize:
        databytes = socket.recv(requestedSize - len(returnStream))
        if databytes == '':
            raise RuntimeError, "connection broken"
        returnStream += databytes

    return returnStream


# Helper function for splitting a raw array of
# zero terminated strings (C) into an array of python strings
def SplitString(raw):
    stringlist = []
    s = ""
    for i in range(len(raw)):
        if raw[i] != '\x00':
            s = s + raw[i]
        else:
            stringlist.append(s)
            s = ""

    return stringlist


# Helper function for extracting eeg properties from a raw data array
# read from tcpip socket
def GetProperties(rawdata):

    # Extract numerical data
    (channelCount, samplingInterval) = unpack('<Ld', rawdata[:12])

    # Extract resolutions
    resolutions = []
    for c in range(channelCount):
        index = 12 + c * 8
        restuple = unpack('<d', rawdata[index:index+8])
        resolutions.append(restuple[0])

    # Extract channel names
    channelNames = SplitString(rawdata[12 + 8 * channelCount:])

    return (channelCount, samplingInterval, resolutions, channelNames)

# Helper function for extracting eeg and marker data from a raw data array
# read from tcpip socket
def GetData(rawdata, channelCount):

    # Extract numerical data
    (block, points, markerCount) = unpack('<LLL', rawdata[:12])

    # Extract eeg data as array of floats
    data = []
    for i in range(points * channelCount):
        index = 12 + 4 * i
        value = unpack('<f', rawdata[index:index+4])
        data.append(value[0])

    # Extract markers
    markers = []
    index = 12 + 4 * points * channelCount
    for m in range(markerCount):
        markersize = unpack('<L', rawdata[index:index+4])

        ma = Marker()
        (ma.position, ma.points, ma.channel) = unpack('<LLl', rawdata[index+4:index+16])
        typedesc = SplitString(rawdata[index+16:index+markersize[0]])
        ma.type = typedesc[0]
        ma.description = typedesc[1]

        markers.append(ma)
        index = index + markersize[0]

    return (block, points, markerCount, data, markers)



##############################################################################################
#
# Main RDA routine
#
##############################################################################################

def main(stop_counter=100):
    # Create a tcpip socket
    con = socket(AF_INET, SOCK_STREAM)
    # Connect to recorder host via 32Bit RDA-port
    # adapt to your host, if recorder is not running on local machine
    HOST ="localhost"
    # change port to 51234 to connect to 16Bit RDA-port
    PORT = 51244           #: 32-Bit data
    if PORT == 51244: DATA_TYPE ="32bit"
    if PORT == 51234: DATA_TYPE ="16bit"
    con.connect((HOST, PORT))


    # Flag for main loop
    finish = False

    # data buffer for calculation, empty in beginning
    data1s = []

    # block counter to check overflows of tcpip buffer
    lastBlock = -1

    #### Main Loop ####
    counter = 0
    previous_time=time.time()
    previous_time_lsl=pylsl.local_clock()
    elapsed_time_a=[]
    elapsed_time_a_lsl=[]
    while not finish and counter<stop_counter:
        print(counter)

        # Get message header as raw array of chars
        requested = 24  #message requested size
        rawhdr = RecvData(con, requested)


        # Split array into usefull information id1 to id4 are constants
        (id1, id2, id3, id4, msgsize, msgtype) = unpack('<llllLL', rawhdr)

        # Get data part of message, which is of variable size
        rawdata = RecvData(con, msgsize - requested)

        # Perform action dependend on the message type
        if msgtype == RDAMessageType.INFO:
            print("Header")
            (channelCount, samplingInterval, resolutions, channelNames) = GetProperties(rawdata)
            print("Info")
            print("Number of channels: " + str(channelCount))
            print("Sampling interval: " + str(samplingInterval))
            print("Resolutions: " + str(resolutions))
            print("Channel Names: " + str(channelNames))
            print("len(channelNames): "+ str(len(channelNames)))

        elif msgtype == RDAMessageType.START:
            # Start message, extract eeg properties and display them
            (channelCount, samplingInterval, resolutions, channelNames) = GetProperties(rawdata)
            # reset block counter
            lastBlock = -1

            print("Start")
            print("Number of channels: " + str(channelCount))
            print("Sampling interval: " + str(samplingInterval))
            print("Resolutions: " + str(resolutions))
            print("Channel Names: " + str(channelNames))
            print("Sample Rate: " + str(1e6/samplingInterval))
            return



        elif (DATA_TYPE == "32bit" and msgtype == RDAMessageType.DATA32) or (DATA_TYPE == "16bit" and msgtype == RDAMessageType.DATA16):
            #time performance
            counter+=1
            current_time = time.time()
            current_time_lsl = pylsl.local_clock()
            elapsed_time=current_time-previous_time
            elapsed_time_lsl=current_time_lsl-previous_time_lsl
            previous_time = current_time
            previous_time_lsl = current_time_lsl
            print("local time:{}".format(current_time))
            print("local time LSL:{}".format(current_time_lsl))
            print("elapsed time:{}".format(elapsed_time))
            print("elapsed time LSL:{}".format(elapsed_time_lsl))
            elapsed_time_a.append(elapsed_time)
            elapsed_time_a_lsl.append(elapsed_time_lsl)

            # Data message, extract data and markers
            (block, points, markerCount, data, markers) = GetData(rawdata, channelCount)

            # Check for overflow
            if lastBlock != -1 and block > lastBlock + 1:
                print ("*** Overflow with " + str(block - lastBlock) + " datablocks ***")
            lastBlock = block

            # Print markers, if there are some in actual block
            if markerCount > 0:
                for m in range(markerCount):
                    print ("Marker " + markers[m].description + " of type " + markers[m].type)

            # Put data at the end of actual buffer
            data1s.extend(data)

            # If more than 1s of data is collected, calculate average power, print it and reset data buffer
            if len(data1s) > channelCount * 1000000 / samplingInterval:
                index = int(len(data1s) - channelCount * 1000000 / samplingInterval)
                data1s = data1s[index:]

                avg = 0
                # Do not forget to respect the resolution !!!
                for i in range(len(data1s)):
                    avg = avg + data1s[i]*data1s[i]*resolutions[i % channelCount]*resolutions[i % channelCount]

                avg = avg / len(data1s)
                print ("Average power: " + str(avg))

                data1s = []



        elif msgtype == RDAMessageType.STOP:
            # Stop message, terminate program
            print ("Stop")
            finish = True





    elapsed_time_a=numpy.array(elapsed_time_a)
    elapsed_time_a_lsl=numpy.array(elapsed_time_a_lsl)
    print("Average elapsed, time.time():{} ; pylsl.local_clock:{}".format(elapsed_time_a.mean(), elapsed_time_a_lsl.mean() ))
    # Close tcpip connection
    con.close()
    return elapsed_time_a, elapsed_time_a_lsl


if __name__ == "__main__":
    main()

