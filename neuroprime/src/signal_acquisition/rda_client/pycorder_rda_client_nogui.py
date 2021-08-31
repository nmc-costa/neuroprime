# -*- coding: utf-8 -*-
'''
Remote Data Access (RDA) Client Module

PyCorder ActiChamp Recorder

BASE CODE: Pycorder
author: Norbert Hauser
date: $Date: 2013-06-05 12:04:17 +0200 (Mi, 05 Jun 2013) $
version: 1.0

UPDATE
@author: nm.costa
@date:  2019-04-30
@version: 1.2
Working using inside the _client_thread() loop the _client_message() interperter - DON't know if changes the performance of the thread - Possible Solution - create a loop in the main script that watchs the header like in the simple_rda.py
'''




from PyQt4 import Qt
from socket import socket,AF_INET, SOCK_STREAM #from python standard library
from select import select #
from struct import unpack #from python standard library
from binascii import unhexlify #from python standard library
import copy
import Queue #from python standard library
import time
import threading
import numpy as np
import datetime
from lxml import objectify
#PYCORDER SPECIFIC
from pycorder_modbase_nogui import ModuleBase, EEG_DataBlock,EEG_Marker, ErrorSeverity, ModuleEvent, EventType, RecordingMode, ImpedanceIndex  # pycorder specific
import frmRdaClientOnline # pycorder specific
# impedance value invalid (electrode disconnected)
#CHAMP_IMP_INVALID = 2147483647  # INT_MAX
CHAMP_IMP_INVALID = 999900  # INT_MAX
GUI_QT =False #this uses pyqt4 and pyqwt

import logging
logger=logging.getLogger(__name__)
logger.setLevel(logging.WARNING)


# RDA message GUID
_MSG_GUID = "8E45584396C9864CAF4A98BBF6C91450"

class RDAMessageType:
    ''' RDA Message Types, negative values are for internal use only
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

class RDAMessage():
    ''' RDA Message Header
    '''
    def __init__(self):
        self.GUID = unhexlify(_MSG_GUID)
        self.Type = 0
        self.Size = 0
        self.Data = ""

class RDA_Client(ModuleBase):
    ''' Receive EEG data over network via TCP/IP
    '''

    def __init__(self, *args, **keys):
        ''' Initialize module
        '''
        ModuleBase.__init__(self, name="RDA Client", **keys)

        self.dataavailable = False
        self.data = EEG_DataBlock(0, 0)
        self.lastBlockNumber = -1
        self.impedanceStartPending = False

        # XML parameter version
        # 1: initial version
        self.xmlVersion = 1

        # create online configuration pane
        if GUI_QT:
            self.online_cfg = _OnlineCfgPane(self)
            self.connect(self.online_cfg, Qt.SIGNAL("modeChanged(int,QString)"), self._online_mode_changed)
        else:
            pass



#
        # define message header structures
        self.GUID = unhexlify(_MSG_GUID)
        self.hdr = "<16sLL"     # generic header: GUID, nSize, nType

        # set client socket defaul values
        self._thClientLock = threading.Lock()
        self.HOST = 'localhost'
        self.PORT = 51244           #: 32-Bit data port
        self.ADDR = (self.HOST, self.PORT)
        self.serverDataValid = False
        self.client_thread_running = False
        self.client_thread = None

        # define data buffer
        self.resetBuffers()
        self.stream_buffer = [] #UPDATE buffer to save all the data - like a Queue - use it to call get_data

    def resetBuffers(self):
        # string buffer for samples
        self.data_buffer = []
        # buffer sizes
        self.data_count = 0
        # calculate block size in samples for a 50ms block
        self.block_size = max(self.data.sample_rate * 0.05, 5)

    def setDefault(self):
        ''' Set module default values
        '''
        self.online_cfg.setIpList([])


    def _online_mode_changed(self, mode, serverIP):
        ''' SIGNAL conect/disconnect button clicked
        @param mode: 0=disconnect, 1=connect requested
        '''
        if mode == 0: # disonnect
            self.disconnectClient()
        else:   # connect
            if len(serverIP) == 0:
                self.online_cfg.updateUI(0)
                return
            self.HOST = serverIP
            self.ADDR = (self.HOST, self.PORT)
            self.connectClient()


    def connectClient(self):
        ''' Create client socket and start client connection thread
        '''
        self.clientsock = socket(AF_INET, SOCK_STREAM)

        self.client_thread_state = 1    # start thread in wait mode
        self.client_thread_running = True
        self.client_thread = threading.Thread(target=self._client_thread)
        self.client_thread.start()

        if GUI_QT:
            self.online_cfg.updateUI(1)
            self.connect(self, Qt.SIGNAL('clientMsg(PyQt_PyObject)'), self._client_message)
            self.connect(self, 'clientMsg(PyQt_PyObject)', self._client_message)
        else:
            self.header_msg= None #reset header




    def disconnectClient(self):
        ''' Stop client thread and close the socket
        '''
        # stop acquisition
        self.stopClient()
        # close socket
        if self.client_thread != None:
            self.client_thread_running = False
            self.client_thread.join(5.0)
            self.client_thread = None
            self.clientsock.close()
            self.clientsock = None
            if GUI_QT:
                self.online_cfg.updateUI(0)
                pass
        if GUI_QT:
            self.disconnect(self, Qt.SIGNAL('clientMsg(PyQt_PyObject)'), self._client_message)
            pass
        else:
            #disconnet througth the thread
            pass



    def stopClient(self):
        ''' Stop client data acquisition
        '''
        if not self.isRunning():
            return
        # stop it
        ModuleBase.stop(self)



    def get_online_configuration(self):
        ''' Get the online configuration pane
        '''
        return self.online_cfg


    def terminate(self):
        ''' Shut down client socket
        '''
        if self.client_thread_running:
            self.client_thread_running = False
            self.client_thread.join(5.0)
            self.client_thread = None
            self.clientsock.close()
            self.clientsock = None

    def stop(self, force=False):
        ''' Stop data acquisition and disconnect client
        '''
        self.disconnectClient()





    def _client_thread(self):
        ''' Client socket connection thread
        '''
        # Messages types which to send directly to input queue
        sendToQueue = [RDAMessageType.DATA16,
                       RDAMessageType.DATA32,
                       ]
        readheader = True
        requested = 24
        received = 0
        msg = RDAMessage()

        while self.client_thread_running:
            # idle mode
            if self.client_thread_state == 0:
                time.sleep(0.2)

            # wait for RDA server
            elif self.client_thread_state == 1:
                # wait for server socket available
                try:
                    self.clientsock.settimeout(10.0)
                    self.clientsock.connect(self.ADDR)
                    self.clientsock.setblocking(0)
                    msg.Type = RDAMessageType.CONNECTED
                    if GUI_QT:
                        self.emit(Qt.SIGNAL('clientMsg(PyQt_PyObject)'), msg)   # connected
                        pass
                    else:
                        logger.debug("connected")
                        self._client_message(msg)
                    self.client_thread_state = 2
                    readheader = True
                    requested = 24
                    msg = RDAMessage()
                except:
                    time.sleep(0.2)

            # connection to server established
            elif self.client_thread_state == 2:
                # look for data
                rd, wr, err = select([self.clientsock],[],[self.clientsock], 0.05)
                if len(err) > 0:
                    # socket error
                    msg.Type = RDAMessageType.DISCONNECTED
                    if GUI_QT:
                        self.emit(Qt.SIGNAL('clientMsg(PyQt_PyObject)'), msg)   # disconnected
                        pass
                    else:
                        logger.debug("!disconnected!")
                        self._client_message(msg)
                    self.client_thread_state = 0
                elif len(rd) > 0:
                    # data received
                    len(msg.Data)
                    data = self.clientsock.recv(requested - len(msg.Data))
                    if len(data) == 0:
                        # connection error
                        msg.Type = RDAMessageType.DISCONNECTED
                        if GUI_QT:
                            self.emit(Qt.SIGNAL('clientMsg(PyQt_PyObject)'), msg)   # disconnected
                            pass
                        else:
                            logger.debug("!connection error!")
                            self._client_message(msg)
                        self.client_thread_state = 0
                    else:
                        # collect data
                        msg.Data += data
                        if requested == len(msg.Data):
                            if readheader:
                                # header received
                                msg.GUID, msg.Size, msg.Type = unpack(self.hdr, msg.Data)

                                # prepare to read data or next header
                                if msg.Size > 24:
                                    readheader = False
                                    requested = msg.Size - 24
                                    msg.Data = ""
                                else:
                                    readheader = True
                                    requested = 24
                                    # Header only, no data
                                    if GUI_QT:
                                        self.emit(Qt.SIGNAL('clientMsg(PyQt_PyObject)'), msg)
                                        pass
                                    else:
                                        logger.debug("!header received!")
                                        self._client_message(msg)
                                    msg = RDAMessage()
                            else:
                                # data part received
                                if msg.Type in sendToQueue:
                                    self._transmit_data(msg)
                                else:
                                    if GUI_QT:
                                        self.emit(Qt.SIGNAL('clientMsg(PyQt_PyObject)'), msg)
                                    else:
                                        logger.debug("!data part received!")
                                        self._client_message(msg)

                                # prepare to read next header
                                readheader = True
                                requested = 24
                                msg = RDAMessage()




    def _client_message(self, message):
        ''' Evaluate client messages
        '''
        logger.debug('****************Evaluate client messages*****************')
        # validate message GUID
        if message.GUID != self.GUID:
            self.disconnectClient()
            self.send_event(ModuleEvent(self._object_name,
                                        EventType.ERROR,
                                        "Invalid data type (GUID)",
                                        severity=ErrorSeverity.NOTIFY))
            return

        if message.Type == RDAMessageType.DISCONNECTED:
            self.disconnectClient()
            logger.debug("DISCONNECTED:{}".format(RDAMessageType.DISCONNECTED))
            return

        if message.Type == RDAMessageType.CONNECTED:
            if GUI_QT:
                self.online_cfg.updateUI(2)
                pass
            logger.debug("CONNECTED:{}".format(RDAMessageType.CONNECTED))
            return

        if message.Type == RDAMessageType.KEEP_ALIVE:
            logger.debug("KEEP_ALIVE:{}".format(RDAMessageType.KEEP_ALIVE))
            return

        if message.Type == RDAMessageType.NEWSTATE:
            logger.debug("NEWSTATE:{}".format(RDAMessageType.NEWSTATE))
            state, = unpack('<i', message.Data[:4])
            return

        if (message.Type == RDAMessageType.STOP) or (message.Type == RDAMessageType.IMP_STOP):
            logger.debug("STOP")
            self._thLock.acquire()
            self.serverDataValid = False
            self._thLock.release()
            self.stopClient()
            return

        if message.Type == RDAMessageType.START:
            logger.debug("START:{}".format(RDAMessageType.START))
            # Extract channel configuration
            (self.channelCount, self.samplingInterval) = unpack('<Ld', message.Data[:12])#UPDATE self.

            # Extract resolutions
            self.resolutions = np.fromstring(message.Data[12:],
                                             dtype=np.float64,
                                             count=self.channelCount)

            # Extract channel names
            self.channelNames = self.splitString(message.Data[12 + 8 * self.channelCount:])

            # Create and setup data configuration object
            self.data = EEG_DataBlock(self.channelCount, 0)
            for idx, ch in np.ndenumerate(self.data.channel_properties):
                ch.name = self.channelNames[idx[0]].decode("cp1252")
                ch.lowpass = 0.0
                ch.highpass = 0.0
                ch.notchfilter = False
                ch.isReference = False
            self.data.sample_rate = 1e6 / self.samplingInterval
            self.data.recording_mode = RecordingMode.NORMAL

            # start acuisition
            logger.debug("!!!!START ACQUISITION!!!")
            self.start() #process_start
            self._thLock.acquire()
            self.serverDataValid = True
            self._thLock.release()
            return



        if message.Type == RDAMessageType.IMP_START:
            # start impedance measurement
            self.data.recording_mode = RecordingMode.IMPEDANCE
            self.impedanceStartPending = True
            return

        if message.Type == RDAMessageType.IMP_DATA:
            # we need a delay impedance start
            # because we have to extract the channel structure from the first impedance data package
            # already started?
            if self.isRunning():
                self._transmit_data(message) # just put the message to the data queue
                return

            if self.impedanceStartPending:
                # extract numerical data
                channels, = unpack('<L', message.Data[:4])
                raw = message.Data[4:]
                # extract impedance values
                self.data = EEG_DataBlock(channels, 0)
                self.data.recording_mode = RecordingMode.IMPEDANCE
                self.data.block_time = datetime.datetime.now()

                # define which channels contains which impedance values
                self.data.eeg_channels[:,:] = 0
                self.data.eeg_channels[:,ImpedanceIndex.DATA] = 1

                # setup channel names
                for ch in range(channels):
                    posx, posy, impedance = unpack('<ffi', raw[:12])
                    raw = raw[12:]
                    name, raw = self.parseUnicodeZ(raw)
                    self.data.channel_properties[ch].name = name

                # start impedance measurement
                self.impedanceStartPending = False
                self.start()
                self._thLock.acquire()
                self.serverDataValid = True
                self._thLock.release()
                return


    def process_start(self):
        ''' Start acquisition
        '''
        # reset variables
        self.data.sample_counter = 0
        self.update_receivers(self.data)
        self.lastBlockNumber = -1
        self.resetBuffers()
        self.data.markers = []

        # set start time on first call
        self.start_time = datetime.datetime.now()

        # send status info
        if self.data.recording_mode == RecordingMode.IMPEDANCE:
            info = "Start impedance check"
        else:
            info = "Start recording with %.0fHz and %d channels"%(self.data.sample_rate,
                                                                  len(self.data.channel_properties))
        self.send_event(ModuleEvent(self._object_name, EventType.LOGMESSAGE, info))
        # send recording mode
        self.send_event(ModuleEvent(self._object_name,
                                    EventType.STATUS,
                                    info = self.data.recording_mode,
                                    status_field="Mode"))
        logger.debug(info)


    def process_stop(self):
        ''' Stop acquisition
        '''
        # reset a pending impedance start
        self.impedanceStartPending = False

        # send status info
        if self.data.recording_mode == RecordingMode.IMPEDANCE:
            info = "Stop impedance check"
        else:
            info = "Stop recording"
        self.send_event(ModuleEvent(self._object_name, EventType.LOGMESSAGE, info))
        # send recording mode
        self.send_event(ModuleEvent(self._object_name,
                                    EventType.STATUS,
                                    info = -1,                  # stop
                                    status_field="Mode"))
        logger.debug(info)


    def process_update(self, params):
        ''' Propagate channel update to all connected receivers
        '''
        # send current status as event
        self.send_event(ModuleEvent(self._object_name,
                                    EventType.STATUS,
                                    info = "%.0f Hz"%(self.data.sample_rate),
                                    status_field = "Rate"))
        self.send_event(ModuleEvent(self._object_name,
                                    EventType.STATUS,
                                    info = "%d ch"%(len(self.data.channel_properties)),
                                    status_field="Channels"))
        return copy.copy(self.data)


    def process_input(self, serverData):

        self.dataavailable = False
        if not self.serverDataValid:
            return
        logger.debug("process_input")


        # process 32bit server data
        if (self.data.recording_mode != RecordingMode.IMPEDANCE) and \
           (serverData.Type == RDAMessageType.DATA32):
            # extract numerical data
            block, points, markerCount = unpack('<LLL', serverData.Data[:12])
            channels = self.data.eeg_channels.shape[0]

            # extract markers
            if self.data_count == 0:
                self.data.markers = []
            index = 12 + 4 * points * channels
            for m in range(markerCount):
                markersize, = unpack('<L', serverData.Data[index:index+4])

                ma = EEG_Marker()
                ma.position, ma.points, ma.channel = unpack('<lLl', serverData.Data[index+4:index+16])
                typedesc = self.splitString(serverData.Data[index+16:index + markersize])
                ma.type = typedesc[0].decode("utf-8")
                ma.description = typedesc[1].decode("utf-8")
                # position is realative to data block, make it absolute
                ma.position = self.data.sample_counter + self.data_count + ma.position
                # add marker to data block
                self.data.markers.append(ma)
                index = index + markersize

            # buffer data until required block size is reached
            self.data_buffer.append(serverData.Data[12:12+(points*channels*np.float32(0).itemsize)])
            self.data_count += points

            if self.data_count >= self.block_size:
                # concatenate data buffer
                data = "".join(self.data_buffer)

                # extract channel data
                eeg = np.fromstring(data,
                                    dtype = np.float32,
                                    count = self.data_count * channels)
                self.data.eeg_channels = np.transpose(np.reshape(eeg, (self.data_count, -1))) * self.resolutions[:,np.newaxis]

                # create sample counter channel
                self.data.sample_channel = np.arange(self.data.sample_counter,
                                                     self.data.sample_counter + self.data_count,
                                                     dtype = np.uint64).reshape(1,-1)
                self.data.sample_counter += self.data_count
                # create dummy trigger channel
                self.data.trigger_channel = np.zeros((1, self.data_count),
                                                     dtype = np.uint32)
                # calculate date and time for the first sample of this block in s
                sampletime = self.data.sample_channel[0][0] / self.data.sample_rate
                self.data.block_time = self.start_time + datetime.timedelta(seconds=sampletime)

                # reset buffers - reset data count
                self.resetBuffers()
                #update
                t_eeg = self.data.eeg_channels.transpose() #[channels][samples]
                t_eeg = t_eeg.tolist()
                self.stream_buffer.extend(t_eeg)

                # mark data as available
                self.dataavailable = True

            # check for missing blocks
            if self.lastBlockNumber >= 0:
                if block != self.lastBlockNumber + 1:
                    missing = block - self.lastBlockNumber - 1
                    self.send_event(ModuleEvent(self._object_name,
                                                EventType.ERROR,
                                                "Missing samples: %d Block(s)"%(missing),
                                                severity=ErrorSeverity.NOTIFY))
            self.lastBlockNumber = block


        # process impedance data
        if (self.data.recording_mode == RecordingMode.IMPEDANCE) and \
           (serverData.Type == RDAMessageType.IMP_DATA):
            # extract numerical data
            channels, = unpack('<L', serverData.Data[:4])
            raw = serverData.Data[4:]
            # extract impedance values
            self.data = EEG_DataBlock(channels, 0)
            self.data.recording_mode = RecordingMode.IMPEDANCE
            self.data.block_time = datetime.datetime.now()
            for ch in range(channels):
                posx, posy, impedance = unpack('<ffi', raw[:12])
                raw = raw[12:]
                name, raw = self.parseUnicodeZ(raw)
                self.data.channel_properties[ch].name = name
                # put the impedance values into the eeg data array
                if impedance < 0:
                    self.data.eeg_channels[ch, ImpedanceIndex.DATA] = CHAMP_IMP_INVALID
                else:
                    self.data.eeg_channels[ch, ImpedanceIndex.DATA] = impedance * 1000
            if channels > 0:
                self.dataavailable = True

        #It would be useful for sync if implemented in modbase
        marker_tick=False
        if marker_tick:
            # Create and insert markers
            # search 1s sample counter ticks
            tickmap = (self.data.sample_channel[0] % self.data.sample_rate) == 0
            ticks = np.nonzero(tickmap)[0]
            # add 1s tick markers
            for tick in ticks:
                self.data.markers.append(EEG_Marker(type="1s Tick",
                                                    description="1s",
                                                    position=self.data.sample_channel[0][tick],
                                                    channel=0))

        logger.debug("process_input: {}".format(self.data))

    def process_output(self):
        if not self.dataavailable:
            return None
        self.dataavailable = False
        return copy.copy(self.data)

    def parseUnicodeZ(self, uRaw):
        ''' Parse zero terminated unicode string
        @param uRaw: unicode raw data
        @return: string, remaining part of uRaw
        '''
        zpos = -1
        for i in range(0,len(uRaw),2):
            v, = unpack('<H', uRaw[i:i+2])
            if v == 0:
                zpos = i
                break
        if zpos > 0:
            uString = uRaw[:zpos].decode("utf-16")
            remainder = uRaw[zpos+2:]
        else:
            uString = u""
            remainder = uRaw
        return uString, remainder


    def splitString(self, raw):
        ''' Helper function for splitting a raw array of
            zero terminated strings (C) into an array of python strings
        '''
        stringlist = []
        s = ""
        for i in range(len(raw)):
            if raw[i] != '\x00':
                s = s + raw[i]
            else:
                stringlist.append(s)
                s = ""
        return stringlist

    def getXML(self):
        ''' Get module properties for XML configuration file
        @return: objectify XML element
        '''
        E = objectify.E
        ipList = E.IP_list()
        for ip in self.online_cfg.getIpList():
            ipList.append(E.item(ip))

        cfg = E.RDA_Client(ipList,
                           version=str(self.xmlVersion),
                           module="RDA",
                           instance=str(self._instance))
        return cfg


    def setXML(self, xml):
        ''' Set module properties from XML configuration file
        @param xml: complete objectify XML configuration tree,
        module will search for matching values
        '''
        # search module configuration data
        configs = xml.xpath("//RDA_Client[@module='RDA' and @instance='%i']"%(self._instance) )
        if len(configs) == 0:
            # configuration data not found, set default values
            self.setDefault()
            return

        # we should have only one instance from this type
        cfg = configs[0]

        # check version, has to be lower or equal than current version
        version = cfg.get("version")
        if (version == None) or (int(version) > self.xmlVersion):
            self.send_event(ModuleEvent(self._object_name,
                                        EventType.ERROR,
                                        "XML Configuration: wrong version"))
            return
        version = int(version)

        # get the values
        try:
            iplist = []
            for ip in cfg.IP_list.iterchildren():
                iplist.append(ip.pyval)
            self.online_cfg.setIpList(iplist)
        except Exception as e:
            self.send_exception(e, severity=ErrorSeverity.NOTIFY)





'''
------------------------------------------------------------
RDA CLIENT MODULE GUI_QT GUI
------------------------------------------------------------
'''


class _OnlineCfgPane(Qt.QFrame, frmRdaClientOnline.Ui_frmRdaClientOnline):
    ''' RDA client online configuration pane
    '''
    def __init__(self, amp, *args):
        apply(Qt.QFrame.__init__, (self,) + args)
        self.setupUi(self)
        self.amp = amp

        # set default values
        self.updateUI(0)

        # actions
        self.connect(self.pushButtonConnect, Qt.SIGNAL("clicked(bool)"), self._button_toggle)
        self.connect(self.pushButtonAdd, Qt.SIGNAL("clicked()"), self._button_add)
        self.connect(self.pushButtonRemove, Qt.SIGNAL("clicked()"), self._button_remove)

    def _button_add(self):
        ''' Add current IP to combobox list
        '''
        # item already in list?
        item = self.comboBoxServerIP.currentText()
        index = self.comboBoxServerIP.findText(item)
        if index < 0:
            self.comboBoxServerIP.addItem(item)

    def _button_remove(self):
        ''' Remove current IP from combobox list
        '''
        # search current item
        item = self.comboBoxServerIP.currentText()
        index = self.comboBoxServerIP.findText(item)
        # remove item
        if index >= 0:
            self.comboBoxServerIP.removeItem(index)

    def _button_toggle(self, checked):
        mode = 0 # disconnect
        if self.pushButtonConnect.isChecked():
            mode = 1 # connect
        self.emit(Qt.SIGNAL('modeChanged(int,QString)'), mode, self.comboBoxServerIP.currentText())

    def getIpList(self):
        ''' Get combobox list entries
        @return: IPs as list
        '''
        list = []
        for idx in range(self.comboBoxServerIP.count()):
            list.append(str(self.comboBoxServerIP.itemText(idx)))
        return list

    def setIpList(self, list):
        ''' Setup combobox list entries
        @param list: IP entries
        '''
        self.comboBoxServerIP.clear()
        for ip in list:
            self.comboBoxServerIP.addItem(ip)
        if self.comboBoxServerIP.count():
            self.comboBoxServerIP.setCurrentIndex(0)
        else:
            self.comboBoxServerIP.setEditText("localhost")

    def updateUI(self, mode):
        ''' Update user interface
        '''
        if (mode == 1) or (mode == 2):
            self.pushButtonConnect.setChecked(True)
            self.pushButtonConnect.setText("Disconnect")
            self.labelMessage.setText("waiting")
            self.comboBoxServerIP.setEnabled(False)
            self.pushButtonAdd.setEnabled(False)
            self.pushButtonRemove.setEnabled(False)
        else:
            self.pushButtonConnect.setChecked(False)
            self.pushButtonConnect.setText("Connect")
            self.labelMessage.setText("disconnected")
            self.comboBoxServerIP.setEnabled(True)
            self.pushButtonAdd.setEnabled(True)
            self.pushButtonRemove.setEnabled(True)
        if mode == 2:
            self.labelMessage.setText("connected")
