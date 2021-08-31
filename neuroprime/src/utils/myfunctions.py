# -*- coding: utf-8 -*-
"""
Created on Thu Oct 26 11:38:03 2017

SCRIPT:


TODO:


NOTE:
    TO work with TKINTER in spyder you need to Tools > Preferences > IPython Console > Graphics > Graphics backend select TK
    PROBLEm is that when you use matplotlib to also display plot you need to change the backend to aautomatic
    https://groups.google.com/forum/#!topic/spyderlib/rFJhJZgjZTE

@author: Nuno Costa, 2017

"""
from __future__ import (absolute_import, division, print_function)
from builtins import * #all the standard builtins python 3 style - input(), to work running a Python script in interactive session



__version__="3.1+dev"
#sys
import os
import sys
import time
import multiprocessing
import queue
#gui
import Tkinter
import tkFileDialog

#data
#import struct
import numpy as np
import scipy
import math
import mne
import wyrm
from wyrm import io #BUG : this is needed to complete subpackage import in the first time
from wyrm.types import Data

#io
import pylsl
import json
import pickle
import copy
from xml.etree import ElementTree as ET

import codecs
from HTMLParser import HTMLParser

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.info('Logger started')



#import pdb

"""
--------------------------------------------------------------
COMOM Methods
--------------------------------------------------------------
"""

"""
Logging


Examples:
    import logging
    my.setlog(modulename=__name__, setlevel=logging.DEBUG, disabled=False)#set filehandler
    logger = logging.getLogger(__name__)
    logger.disabled = False
    logger.info('yeah')

    or use log() function
"""


def setlogfile(modulename=__name__, setlevel=logging.DEBUG, disabled=False):
    #Setting logger handler of modules and create file of logs
    logger = logging.getLogger(modulename)
    logger.disabled=disabled
    logger.setLevel(setlevel)
    if not disabled: # if disabled
        # add the handlers to the logger
        sethandlerfile(modulename=modulename,setlevel=setlevel)
        #not necessary for console
        #logger.addHandler(sethandlerconsole(setlevel=setlevel))
    return logger


def sethandlerfile(modulename=__name__, setlevel=logging.DEBUG, filepath=None):
    if not filepath:
        filepath = os.getcwd()
    filepath=os.path.join(filepath, "logs")
    filename = time.strftime("%d%m%Y") + '_' + time.strftime("%Hh%Mm") + '_'+modulename+'.log'
    path = os.path.join(filepath, filename)
    assure_path_exists(path)
    # create a file handler
    handler = logging.FileHandler(path)
    handler.setLevel(setlevel)
    # create a logging format
    formatter = logging.Formatter('%(asctime)s - %(name)s -  %(levelname)s - func:%(funcName)s - line:%(lineno)d - msg:%(message)s')
    handler.setFormatter(formatter)
    #add handler
    logger = logging.getLogger(modulename)
    logger.addHandler(handler) #uncomment if log file wanted





def sethandlerconsole(modulename=__name__, setlevel=logging.DEBUG):
    # create a file handler
    handler = logging.StreamHandler()
    handler.setLevel(setlevel)

    # create a logging format
    formatter = logging.Formatter('%(asctime)s - %(name)s -  %(levelname)s - func:%(funcName)s - line:%(lineno)d - msg:%(message)s')
    handler.setFormatter(formatter)

    #add handler
    logger = logging.getLogger(modulename)
    logger.addHandler(handler) #uncomment if log file wanted



def all_logs_enabler(disable=False):
    for name, logger in logging.root.manager.loggerDict.iteritems():
        logger.disabled=disable

def log(level, msg, modulename=__name__):
    #use log() or get logger in module and use it - in that way you get the correct line
    logger = logging.getLogger(modulename)
    if level =="debug":
        logger.debug("%s", msg)
    if level =="info":
        logger.info("%s", msg)
    if level =="warn":
        logger.warn("%s", msg)
    if level =="error":
        logger.error("%s", msg)
    if level =="critical":
        logger.error("%s", msg)

"""
Path Methods
"""
def assure_path_exists(path):
    """
    Create directory folders from path

    Note: windows path strings should be r'path'
    """

    #Only for dirs - for complete you have to change dir for path
    dir_p = os.path.dirname(parse_path(path)) #dirname is obrigatory - make sure it is a dir
    if not os.path.exists(dir_p):
        os.makedirs(dir_p)



def assure_path_exists_all(path):
    path = os.path.normpath(path)
    if not os.path.exists(path):
            os.makedirs(path)

def get_dir_path():
    root = Tkinter.Tk()
    #root.withdraw()
    dirname = tkFileDialog.askdirectory(parent=root,initialdir="/",title='Please select a directory')
    dirname = os.path.normpath(dirname)
    root.destroy()
    if len(dirname ) > 0:
        print ("You chose %s" % dirname)
        return dirname

def get_file_path():
    root = Tkinter.Tk()
    #root.wm_iconify()
    #root.withdraw()
    filename = tkFileDialog.askopenfilename(parent=root,initialdir="/",title='Please select a file')
    filename = os.path.normpath(filename)
    root.destroy()
    if len(filename ) > 0:
        print ("You chose %s" % filename)
        return filename


def parse_path(path):
    """
    Python only works with '/', not '\\'or '\'

    WARNING:
        in windows use r'path' because of escape literals , e.g: "."
        os.path.realpath(path).replace('\\', '/') #BUG os.path.realpath removes the last '\\' and if your sending a folder it is a problem

    """
    parsed_path = path.replace('\\', '/')
    parsed_path = parsed_path.replace("\ ", '/')
    return parsed_path

def parse_path_list(path):
    """
    Input:
        full path
    Returns:
        base dir, file(or dir) name, extension (if file)
    """

    path_abs = parse_path(path)
    s = path_abs.split('/')
    f = s[-1].split('.')
    basedir = '/'.join(s[:-1]) + '/'
    if len(f) == 1:
        name, ext = f[-1], ''
    else:
        name, ext = '.'.join(f[:-1]), f[-1]

    return basedir, name, ext


def add_to_pythonpath(folderpath):
    """
    Strictly taken, a module is a single python file, while a package is a folder containing python files, accompanied by a (can be empty) file named __init__.py, to tell python it is a package to import modules from. In both cases, modules need their .py extension, but importing them is done without (see further below).

By default, Python looks for its modules and packages in $PYTHONPATH.

To find out what is included in $PYTHONPATH, run the following code in python (3)
import sys
logger.warn(sys.path)
    """
    pass

"""
SAVE, load, read and serialize methods - IO methods
"""

def get_filetoreplay(folderdir="e1_sample", filename="EG_S007_NFT_ss01_rt02_21092018_11h15m_SMR_2", filetype=".meta"):
    import neuroprime.sampledata
    sampledatadir=os.path.abspath(neuroprime.sampledata.__file__)
    sampledatadir, filen, ext =parse_path_list(sampledatadir) #parse
    #folderdir
    folderdir=folderdir
    #filedir
    filedir=os.path.join(sampledatadir,folderdir)
    filetype=filetype
    filename=filename
    #filepath
    filepath= os.path.join(filedir,filename)+filetype
    filetoreplay=filepath

    return filetoreplay

def get_test_folder(foldername='temp_test'):
    import platform
    desktop_path =''
    if platform.system()=='Windows':
        desktop_path = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
    if platform.system()=='Darwin':
        desktop_path = os.path.join(os.path.join(os.path.expanduser('~')), 'Desktop')
    test_folder_path=os.path.join(desktop_path, foldername)
    if test_folder_path[-1] != '/':
        test_folder_path += '/' #make sure is a folder
    assure_path_exists(test_folder_path) #assures dirname path
    return test_folder_path

def gui_dialogue(info={'Observer':'jwp', 'GratingOri':45, 'ExpVersion': 1.1,
                'Group': ['Test', 'Control']},
                title='TestExperiment',
                fixed=['ExpVersion']):
    try:
        from psychopy import gui

        dictDlg = gui.DlgFromDict(dictionary=info,
                title=title, fixed=fixed)
        if dictDlg.OK:
            print(info)
            return info
        else:
            print('User Cancelled')
            sys.exit("USER CANCELLED")
    except:
        logger.error("MISSING SOMETHING FROM PSYCHOPY Package!")
        raise


#filename
# SAVING
def create_file_path(SAVE=False, FOLDER_DATA=None, GROUP='EG', TASK='', SUBJECT_NR=1, SESSION_NR=1, BLOCK_NR=None):
    PATH , FILENAME_DATA, FILENAME_PATH = None, None, None
    if SAVE:
        try:
            if FOLDER_DATA == None:
                FOLDER_DATA = get_dir_path()
            # TODO: CREATE Dialogue for this
            GROUP = GROUP  # EG: experimental group
            SUBJECT = 'S' + '{num:03d}'.format(num=SUBJECT_NR)  # subject fixed to 3 digits
            TASK = TASK  # task: PRET(pre-training); NFT(Neurofeedback)
            SESSION = 'ss'+ '{num:02d}'.format(num=SESSION_NR)

            #filename
            timestamp = time.strftime('%d%m%Y_%Hh%Mm', time.localtime())
            FILENAME_DATA = GROUP + '_' + SUBJECT + '_' + TASK + '_' + SESSION + '_' +timestamp
            if BLOCK_NR and BLOCK_NR>=0:
                logger.debug("#BLOCK_NR CAN ONLY be added in each run - so add later or reinit every new run this function")
                BLOCK = 'b'+ '{num:02d}'.format(num=BLOCK_NR)
                FILENAME_DATA = GROUP + '_' + SUBJECT + '_' + TASK + '_' + SESSION + '_' + BLOCK + '_'+timestamp
            #path
            PATH = os.path.normpath(os.path.join(FOLDER_DATA, GROUP, SUBJECT, TASK))
            FILENAME_PATH = os.path.normpath(os.path.join(PATH, FILENAME_DATA))
            # 'data/EG/S001/PRET/EG_S001_PRET_ss01_01122017'
            # Assure path exists - IF not, create directories
            assure_path_exists(FILENAME_PATH)
            logger.info ("DATA FILENAME: {:s} ; DATA PATH: {:s}".format(FILENAME_DATA, PATH))
        except Exception as e:
            logger.error("\n>> Error on Path: {}".format(e))
            raise RuntimeError("\n>> Error on Path: {}".format(e))


    return PATH , FILENAME_DATA, FILENAME_PATH



def save_data(fname, data):
    #data: list
    # Save Data
    with open (fname,'w') as fileOutput:
        for item in data:
            fileOutput.write("%s\n" % item)

def save_as_gui_image():
    myFormats = [
    ('Windows Bitmap','*.bmp'),
    ('Portable Network Graphics','*.png'),
    ('JPEG / JFIF','*.jpg'),
    ('CompuServer GIF','*.gif'),
    ]
    root = Tkinter.Tk()
    root.withdraw()
    fileName = tkFileDialog.asksaveasfilename(parent=root,filetypes=myFormats ,title="Save the image as...")
    root.destroy()
    if len(fileName ) > 0:
        print ("Now saving under %s" % fileName)

def load_file(fname):
    if not fname:
        fname = get_file_path()
    with open(fname, 'r') as fin:
        return fin.read()

def read_some_file():
    fname = get_file_path()
    with open(fname, 'r') as fin:
        print (fin.read())

def opening_file():
    root = Tkinter.Tk()
    #root.withdraw()
    FILE = tkFileDialog.askopenfile(parent=root,mode='rb',title='Choose a file')
    root.destroy()
    if FILE != None:
        data = FILE.read()
        FILE.close()
        print ("I got %d bytes from this file." % len(data))

#HTML Read Files Parser
# create a subclass and override the handler methods
class MyHTMLParser(HTMLParser):
    DATA = []
    def handle_starttag(self, tag, attrs):
        print ("Encountered a start tag:", tag)

    def handle_endtag(self, tag):
        print ("Encountered an end tag :", tag)

    def handle_data(self, data):
        print ("Encountered some data  :", data)
        self.DATA.append(data)

def htmlfile_data_as_array(htmlfile):
    # instantiate the parser and fed it some HTML
    parser = MyHTMLParser()
    f=codecs.open(htmlfile, 'r')
    parser.feed(f.read())
    FinalDataList = remove_new_lines(parser.DATA)
    logger.warn(FinalDataList)
    return FinalDataList

def save_htmlfile_data (fname, htmlfile):
    data = htmlfile_data_as_array(htmlfile)
    save_data(fname, data)

def parse_object_dict(obj):
    logger.debug("#BUG #SOLVED cant change original object - use copy.copy method")
    Object=copy.copy(obj) #shallow copy to change pointer
    logger.debug("#BUG #SOLVED thread lock objects cant be serialized in json or logger- normally they have __dict__ attribute - so change it to str")
    od=Object
    if hasattr(Object, "__dict__"):
        od = Object.__dict__
    for key in od.keys():
        if hasattr(od[key], "__dict__"):
            od[key]=str(od[key])
        if type(od[key]).__module__ == np.__name__:
            od[key]=np.array_str(od[key])
    return od

#Serializing and desirializing python objects
#SAVE OBJECT
def serialize_object(obj, filedir, filename, method="pickle"):
    #WARNING: NOT a good implementation - use filepath, remove extensions
    FILE = os.path.join(filedir, filename)
#    pdb.set_trace()
    #change object values from type object to str
    logger.debug("#BUG #SOLVED cant change original object - use copy.copy method")
    Object=copy.copy(obj) #shallow copy to change pointer
    obj=parse_object_dict(Object)

#    pdb.set_trace()
    #Serialize - different methods - can also use shelve package that does the same with pickle
    if method=="json":
        save_obj_json(FILE+'.txt', obj)
    elif method=="simplejson":
        logger.debug("needs pip install simplejson")
        import simplejson as json
        with open(FILE+'.txt', 'w') as f:
            json.dump(obj, f)
    if method=="pickle":
        save_obj_pickle(FILE+'.pcl',obj, protocol=pickle.HIGHEST_PROTOCOL)
    elif method=="cpickle":
        import cPickle as pickle
        with open(FILE+'.pcl', 'wb') as f:
            # Pickle the 'data' dictionary using the highest protocol available.
            pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)

#LOAD_OBJECT
def deserialize_object(filedir, filename, method="pickle"):
    #WARNING: NOT a good implementation - use filepath, remove extensions
    FILE = os.path.join(filedir, filename)
    Object=None
    if method=="json":
        Object=load_obj_json(FILE)
    elif method=="simplejson":
        import simplejson as json
        with open(FILE, 'r') as f:
            Object=json.load(f)
    if method=="pickle":
        Object=load_obj_pickle(FILE)
    elif method=="cPickle":
        Object=load_obj_cpickle(FILE)
    if method=='pandas.pkl':
        import pandas
        Object = pandas.read_pickle(FILE)

    return Object


def save_obj_pickle(fname, obj, protocol=pickle.HIGHEST_PROTOCOL):
    """
    Save python object into a file
    Set protocol=2 for Python 2 compatibility
    """
    with open(fname, 'wb') as fout:
        pickle.dump(obj, fout, protocol)

def load_obj_pickle(fname):
    """
    Read python object from a file
    """
    try:
        with open(fname, 'rb') as f:
            return pickle.load(f)
    except UnicodeDecodeError:
        # usually happens when trying to load Python 2 pickle object from Python 3
        with open(fname, 'rb') as f:
            return pickle.load(f, encoding='latin1')
    except:
        msg = 'load_obj(): Cannot load pickled object file "%s". The error was:\n%s\n%s' %\
              (fname, sys.exc_info()[0], sys.exc_info()[1])
        raise IOError(msg)

def load_obj_cpickle(fname):
    """
    Read python object from a file
    """
    import cPickle as pickle
    try:
        with open(fname, 'rb') as f:
            return pickle.load(f)
    except UnicodeDecodeError:
        # usually happens when trying to load Python 2 pickle object from Python 3
        with open(fname, 'rb') as f:
            return pickle.load(f, encoding='latin1')
    except:
        msg = 'load_obj(): Cannot load pickled object file "%s". The error was:\n%s\n%s' %\
              (fname, sys.exc_info()[0], sys.exc_info()[1])
        raise IOError(msg)

def save_obj_json(fname, obj):
    """
    Save python object into a json file
    """

    #different forms of serialize json to string
    #write
    with open(fname, 'w') as f:
        try:#python 2 version
            json.dump(obj, f)
#                dump=json.dumps(obj)#old, =
#                f.write(dump)
        except:#python 2&3 compatible version
            try:
                dump=json.dumps(obj)
                dump = unicode(dump, 'UTF-8')
                f.write(dump)
                #UPDATE compatability to python 3 - https://stackoverflow.com/questions/36003023/json-dump-failing-with-must-be-unicode-not-str-typeerror
            except:#pure str
                dump=obj.__repr__
                dump = unicode(dump, 'UTF-8')
                f.write(dump)


def load_obj_json(fname):
    """
    load python object from a json file
    """
    Obj=None
    with open(fname, 'r') as f:
        Obj=json.load(f)
    return Obj



class save_in_subprocess(object):
    """
    Simple subprocess save class

    data
    fileout: fout=open(filename, 'wb')

    sources:
        #https://stackoverflow.com/questions/2629680/deciding-among-subprocess-multiprocessing-and-thread-in-python
        #https://pymotw.com/2/multiprocessing/basics.html
        #https://stackoverflow.com/questions/32053618/how-to-to-terminate-process-using-pythons-multiprocessing

    TODO:

    WARNING:
        On windows you need to run the code in cmd line - IDEs don't work
    """

    def __init__(self, data, filepath, process_name="SAVE_SUBPROCESS", method='pcl'):
        print("data:", data)
        self.data=data
        self.process_name=process_name
        self.filepath=filepath
        self.method=method



    def save(self):
        #Main
        #start child process
        self.wk = multiprocessing.Process(name=self.process_name, target=self.worker, args=(self.data, self.filepath, self.method))
        self.wk.daemon=True #To exit the main process even if the child process p didn't finished - less constrictions between processes? Any errors and hangs (or an infinite loop) in a daemon process will not affect the main process, and it will only be terminated once the main process exits.
        self.wk.start() #start process



    def worker(self, data, filepath, method):
        #WARNING#NOTE only works with filepath not fileout
        print("data:", data)
        print("method:", method)
        print("filepath:", filepath)
        p = multiprocessing.current_process()
        print ('Starting:', p.name, p.pid)
        print('\n>> Saving raw data ...')
        if method=="pcl":
            save_obj_pickle(filepath, data, protocol=2)
        print('RAW Saved to %s\n' % filepath)


    def on_quit(self):
        ##QUIT
        #Child process still alive because of worker loop
        if self.p.is_alive():
            self.p.terminate() #force termination
            self.p.join() #wait to terminate
            print("Process ALive: ",self.p.is_alive())
        print('That took {} seconds'.format(time.time() - self.starttime))

"""
List Methods
"""
def remove_item(LIST, item):
    #Strip of ""
    #LIST = map(lambda s: s.strip(), LIST)
    # List comprehension
    LIST = [x for x in LIST if x != item]
    return LIST

def remove_new_lines(LIST):
    #Strip of "\n"
    LIST = map(lambda s: s.strip(), LIST)
    # List comprehension remove item
    LIST = remove_item(LIST, '')
    return LIST


"""
Dict Methods
"""
def dictfinditem(obj, key):
    if key in obj: return obj[key]
    for k, v in obj.items():
        if isinstance(v,dict):
            item = dictfinditem(v, key)
            if item is not None:
                return item
    return False

def replace_nan_w_previous_value(current_dict, past_dict):
    logger.debug("#TODO: Also check nan list")
    result = current_dict
    for k in current_dict:
        if isinstance(current_dict[k], dict):
            result[k] = replace_nan_w_previous_value(current_dict[k], past_dict[k])
        else:
            if isinstance(current_dict[k], str):
                if current_dict[k].isdigit():
                    if math.isnan(float(current_dict[k])):
                        result[k] = past_dict[k]
            else:
                if not isinstance(current_dict[k], list):
                    if math.isnan(current_dict[k]):
                        result[k] = past_dict[k]

    return result

def check_dict_nan(current_dict):
    result=current_dict
    for k in current_dict:
        if isinstance(current_dict[k], dict):
            result[k] = replace_nan_w_previous_value(current_dict[k])
        else:
            if isinstance(current_dict[k], str):
                if current_dict[k].isdigit():
                    if math.isnan(float(current_dict[k])):
                        return True
            else:
                if not isinstance(current_dict[k], list):
                    if math.isnan(current_dict[k]):
                        return True

    return False
"""
String Methods
"""
#Find Index in String
def allindices(string, sub, listindex=[], offset=0):
    i = string.find(sub, offset)
    while i >= 0:
        listindex.append(i)
        i = string.find(sub, i + 1)
    return listindex

"""
for Loop methods
"""
def my_range(start, end, step):
    while abs(start) <= abs(end):
        yield start
        start += step


"""
--------------------------------------------------------------
DATA ANALYSIS
--------------------------------------------------------------
"""

def peakdet(v, delta, x = None, nrpeaks=None):
    """
    Converted from MATLAB script at http://billauer.co.il/peakdet.html

    Returns two arrays

    function [maxtab, mintab]=peakdet(v, delta, x)
    %PEAKDET Detect peaks in a vector
    %        [MAXTAB, MINTAB] = PEAKDET(V, DELTA) finds the local
    %        maxima and minima ("peaks") in the vector V.
    %        MAXTAB and MINTAB consists of two columns. Column 1
    %        contains indices in V, and column 2 the found values.
    %
    %        With [MAXTAB, MINTAB] = PEAKDET(V, DELTA, X) the indices
    %        in MAXTAB and MINTAB are replaced with the corresponding
    %        X-values.
    %
    %        A point is considered a maximum peak if it has the maximal
    %        value, and was preceded (to the left) by a value lower by
    %        DELTA.

    % Eli Billauer, 3.4.05 (Explicitly not copyrighted).
    % This function is released to the public domain; Any use is allowed.

    """
    import sys
    from numpy import NaN, Inf, arange, isscalar, asarray, array
    maxtab = []
    mintab = []

    if x is None:
        x = arange(len(v))

    v = asarray(v)

    if len(v) != len(x):
        sys.exit('Input vectors v and x must have same length')

    if not isscalar(delta):
        sys.exit('Input argument delta must be a scalar')

    if delta <= 0:
        sys.exit('Input argument delta must be positive')

    mn, mx = Inf, -Inf
    mnpos, mxpos = NaN, NaN

    lookformax = True

    for i in arange(len(v)):
        this = v[i]
        if this > mx:
            mx = this
            mxpos = x[i]
        if this < mn:
            mn = this
            mnpos = x[i]

        if lookformax:
            if this < mx-delta:
                maxtab.append((mxpos, mx))
                mn = this
                mnpos = x[i]
                lookformax = False
        else:
            if this > mn+delta:
                mintab.append((mnpos, mn))
                mx = this
                mxpos = x[i]
                lookformax = True
    #order peaks
    def myfn(item):
        return item[1]
    maxtab=sorted(maxtab, key=myfn, reverse=True)#descending peak order
    mintab=sorted(maxtab, key=myfn, reverse=False)#ascending peak order
    if nrpeaks:
        maxtab = [maxtab[i] for i in range(nrpeaks)]
        mintab = [mintab[i] for i in range(nrpeaks)]

    return array(maxtab), array(mintab)


"""
--------------------------------------------------------------
UNCOMOM Methods - Specific Modules
--------------------------------------------------------------
"""

"""
Check Monitor Functions
"""

def returnMonitorSize():
    root = Tkinter.Tk()
    root.withdraw()
    width, height = root.winfo_screenwidth(), root.winfo_screenheight()
    return [width, height]
    """Check monitor Size in python
    https://stackoverflow.com/questions/3129322/how-do-i-get-monitor-resolution-in-python/17475065
    any os
    import Tkinter #tkinter python 3 syntax; Tkinter python 2 syntax
    root = Tkinter.Tk()
    root.withdraw()
    width, height = root.winfo_screenwidth(), root.winfo_screenheight()

    windows os
    from win32api import GetSystemMetrics
    print ("Width =", GetSystemMetrics(0)
    print ("Height =", GetSystemMetrics(1)
    or
    import ctypes
    user32 = ctypes.windll.user32
    screensize = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
    or
    import wx
    app = wx.App(False) # the wx.App object must be created first.
    logger.warn(wx.GetDisplaySize())  # returns a tuple
    """


'''"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
 Timer class
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""'''

class Timer(object):
    """
    Timer class

    if autoreset=True, timer is reset after any member function call
    """
    def __init__(self, autoreset=False):
        self.autoreset = autoreset
        self.reset()

    def sec(self):
        read = time.time() - self.ref
        if self.autoreset: self.reset()
        return read

    def msec(self):
        return self.sec() * 1000.0

    def reset(self):
        self.ref = time.time()

    def sleep_atleast(self, sec):
        """
        Sleep up to sec seconds
        It's more convenient if autoreset=True
        """
        timer_sec = self.sec()
        if timer_sec < sec:
            time.sleep(sec - timer_sec)
            if self.autoreset: self.reset()



"""
Lab Streaming Layer functions
"""

def sniff_and_close_stream(streamname):
    # IT Just closes stream inlet data - it doe not close outlet stream
    inlet = None
    myStreamName = streamname
    streams = pylsl.resolve_stream()
    stream_names = [si.name() for si in streams]
    logger.warn(stream_names)
    if len(streams) > 1:
        logger.warn('Number of streams is > 0, picking up:', streamname)
    if myStreamName in stream_names and inlet is None:
        logger.warn(streamname, " Stream, still exists. Closing it...")
        stream_index = stream_names.index(myStreamName)
        stream = streams[stream_index]
        inlet = pylsl.StreamInlet(stream)
        inlet.close_stream()
    else:
        logger.warn("WARNING: No stream with the name: ", streamname)

def checkstreamstype(streamtype='EEG'):
    # IT Just closes stream inlet data - it doe not close outlet stream
    """
    contResolver = pylsl.ContinuousResolver()
    inlet = None
    n=0
    while n <= 1:
        n += 1
        streams = contResolver.results()
        stream_names = [si.name() for si in streams]
        stream_types = [si.type() for si in streams]
        #print("Streams : {}".format(stream_names))
        time.sleep(1)
    """
    inlet = None
    streams = pylsl.resolve_streams(wait_time=3.0)
    stream_names = [si.name() for si in streams]
    stream_types = [si.type() for si in streams]
    logger.warn("names: {}".format(stream_names))
    logger.warn("types: {}".format(stream_types))
    if streamtype in stream_types:
        logger.warn('Number of {} streams is {}'.format(streamtype, len(streams)))
        inlet=True
    else:

        logger.warn("WARNING: No stream of type {} ".format(streamtype))
        inlet=None

    return inlet


def return_marker_inlet(myStreamName, streamtype='Markers'):
    inlet = None
    FLAG = 0  #float("inf")
    streams = pylsl.resolve_stream('type', streamtype)
    logger.warn(streams)
    stream_names = [si.name() for si in streams]
    logger.warn(stream_names)
    if len(streams) > 1:
        logger.warn('Number of Marker streams is > 0, picking the pyff Marker.')
    if myStreamName in stream_names and inlet is None:
        logger.warn("Pyff marker Exists in the Stream")
        stream_index = stream_names.index(myStreamName)
        stream = streams[stream_index]
        inlet = pylsl.StreamInlet(stream)

    else:
        logger.error("WARNING: marker not in the Stream:"+myStreamName)
        inlet= None

    if inlet is not None:
        n=0
        while n <= FLAG:
            n += 1
            sample, timestamp  = inlet.pull_sample()
            if sample:
                logger.warn("got %s at time %s" % (sample[0], timestamp))
    return inlet

def return_stream_inlet(myStreamName, streamtype=None, FLAG=None, wait_time=5.0, max_buflen=360, max_chunklen=0, recover=True, processing_flags=0):
    """
    contResolver = pylsl.ContinuousResolver()
    inlet = None
    n=0
    while n <= 3:
        n += 1
        streams = contResolver.results()
        stream_names = [si.name() for si in streams]
        #print("Streams : {}".format(stream_names))
        time.sleep(1)
    """
    inlet = None
    stream = None
    streams = pylsl.resolve_streams(wait_time=wait_time)
    stream_names = [si.name() for si in streams]
    logger.warn("\n>> Streams : {}".format(stream_names))
    if len(streams) > 1:
        logger.debug('\n>> Number of streams is > 1')
    #more than one stream with the same name?
    stream_index_l = [ i for i, v in enumerate(stream_names) if myStreamName.upper() == v.upper()]
    #WARNING:IF there is more than one stream with the same name
    if len(stream_index_l)>1:
        logger.error("\n>> more than one stream with the same name, close them: {}".format(stream_names))
        raise AssertionError("\n>> more than one stream with the same name, close them: {}".format(stream_names))
        #Getting the last one is can be a mistake
        #stream_index = stream_index_l[-1] #getting last pyffmarker, hopefully it is the right one
        #stream = streams[stream_index]
    elif len(stream_index_l)==1:
        logger.warn("\n>> GREAT - Only 1 {} stream!".format(myStreamName))
        stream_index = stream_index_l[0]
        stream = streams[stream_index]
    else:
        logger.error("\n>> WARNING: No Stream Named: "+myStreamName)
        stream=None


    if stream:
        inlet = pylsl.StreamInlet(stream, max_buflen=max_buflen, max_chunklen=max_chunklen, recover=recover, processing_flags=processing_flags)
        if streamtype:#assert type
            true_streamtype = str(stream.type())
            if true_streamtype.upper() == streamtype.upper():
                logger.debug("\n>> CORRECT streamtype: input_streamtype:{}; actual_streamtype:{}".format(streamtype,true_streamtype))
            else:
                logger.error("\n>> ERROR: WRONG streamtype: input_streamtype:{}; actual_streamtype:{}".format(streamtype,true_streamtype))
                inlet= None

    if inlet and FLAG:
        n=0
        while n <= FLAG:
            n += 1
            sample, timestamp  = inlet.pull_sample()
            if sample:
                logger.warn("\n>> got %s at time %s" % (sample[0], timestamp))


    return inlet

def streams_in_network(FLAG=10):
    contResolver = pylsl.ContinuousResolver()
    n=0
    while n <= FLAG:
        n += 1
        streams = contResolver.results()
        stream_names = [si.name() for si in streams]
        print(stream_names)
        time.sleep(1)
    return stream_names



def test_lsl_inlet_offset(lsl_inlet, max_offset=0.05, timeout=5):
    logger.warning('\n>> Testing INLET PERFORMANCE....')
    watchdog = Timer()
    watchdog.reset()
    restart_connection=False
    lsl_time_offset=None
    stream_valid=False
    tslist = []
    while watchdog.sec() < timeout:
        # retrieve chunk in [frame][ch]
        if len(tslist) == 0:
            chunk, tslist = lsl_inlet.pull_chunk()  # [frames][channels]
        if len(tslist) > 0:
            lsl_clock = pylsl.local_clock()
            break
        time.sleep(0.0005)
    else:
        logger.error('\n>> ERROR : Timeout of {}s occurred while acquiring data. Stream driver bug?'.format(timeout))
        restart_connection=True
    if len(tslist)>0:
        logger.info('\n>> Sample Chunk length = %s' % str(len(chunk)))
        logger.info('\n>> LSL timestamp = %s' % lsl_clock)
        logger.info('\n>> Server timestamp = %s' % tslist[-1])
        lsl_time_offset = lsl_clock - tslist[-1]
        logger.info('\n>> Offset = %.3f ' % (lsl_time_offset))
        if lsl_time_offset > max_offset:#above 100ms
            logger.error('\n>> The server timestamps have high offset to LSL timestamps. Probably a bug in the acquisition server.')
            #restart_configure=True
            stream_valid=False #Stay here while not good the offset
        else:
            logger.info('\n>> (LSL time synchronized)')
            stream_valid=True

    return lsl_time_offset, stream_valid, restart_connection

"""Functions adapted from https://github.com/dbdq/neurodecode by Kyuhwa Lee Package with some updates"""
def search_lsl(ignore_markers=False):
    import time

    # look for LSL servers
    amp_list = []
    amp_list_backup = []
    while True:
        streamInfos = pylsl.resolve_streams()
        if len(streamInfos) > 0:
            for index, si in enumerate(streamInfos):
                # LSL XML parser has a bug which crashes so do not use for now
                #desc = pylsl.StreamInlet(si).info().desc()
                #amp_serial = desc.child('acquisition').child_value('serial_number').strip()
                amp_serial = 'N/A' # serial number not supported yet
                amp_name = si.name()
                if 'Markers' in amp_name:
                    amp_list_backup.append((index, amp_name, amp_serial))
                else:
                    amp_list.append((index, amp_name, amp_serial))
            break
        logger.info('No server available yet on the network...')
        time.sleep(1)

    if ignore_markers is False:
        amp_list += amp_list_backup



    logger.info('-- List of servers --')
    for i, (index, amp_name, amp_serial) in enumerate(amp_list):
        if amp_serial == '':
            amp_ser = 'N/A'
        else:
            amp_ser = amp_serial
        logger.info('%d: %s (Serial %s)' % (i, amp_name, amp_ser))

    if len(amp_list) == 1:
        index = 0
    else:
        index = input('Amp index? Hit enter without index to select the first server.\n>> ')
        if index.strip() == '':
            index = 0
        else:
            index = int(index.strip())
    amp_index, amp_name, amp_serial = amp_list[index]
    si = streamInfos[amp_index]
    assert amp_name == si.name()
    # LSL XML parser has a bug which crashes so do not use for now
    #assert amp_serial == pylsl.StreamInlet(si).info().desc().child('acquisition').child_value('serial_number').strip()
    amp_inlet = pylsl.StreamInlet(si)
    logger.info('Selected %s (Serial: %s Inlet: %s)' % (amp_name, amp_serial, amp_inlet ))

    return amp_name, amp_serial, amp_inlet

def choose_lsl(streamtype='Markers', wait_time=1.0):
    # look for LSL servers
    amp_list = []
    amp_list_backup = []
    streamInfos = pylsl.resolve_streams(wait_time=wait_time)
    if len(streamInfos) == 0:
        logger.warning('No lsl server avilable yet on the network...')
        amp_name, amp_serial, amp_inlet = None, None, None
        return amp_name, amp_serial, amp_inlet
    else:
        for index, si in enumerate(streamInfos):
            # LSL XML parser has a bug which crashes so do not use for now
            #desc = pylsl.StreamInlet(si).info().desc()
            #amp_serial = desc.child('acquisition').child_value('serial_number').strip()
            amp_serial = 'N/A' # serial number not supported yet
            amp_name = si.name()
            if 'Markers' in amp_name:
                amp_list_backup.append((index, amp_name, amp_serial))
            else:
                amp_list.append((index, amp_name, amp_serial))

        amp_list += amp_list_backup


        logger.info('-- List of servers --')
        for i, (index, amp_name, amp_serial) in enumerate(amp_list):
            if amp_serial == '':
                amp_ser = 'N/A'
            else:
                amp_ser = amp_serial
            logger.info('%d: %s (Serial %s)' % (i, amp_name, amp_ser))

        if len(amp_list) == 1:
            index = 0
            amp_index, amp_name, amp_serial = amp_list[index]
            amp_inlet = return_stream_inlet(amp_name, streamtype=streamtype, FLAG=None, wait_time=1.0)
            if amp_inlet:
                return amp_name, amp_serial, amp_inlet
            else:
                amp_name, amp_serial, amp_inlet = None, None, None
                return amp_name, amp_serial, amp_inlet
        else:
            index = input('Stream index? Hit enter without index to select the first server.\n>> ')
            if index.strip() == '':
                index = 0
            else:
                index = int(index.strip())
        amp_index, amp_name, amp_serial = amp_list[index]
        si = streamInfos[amp_index]
        assert amp_name == si.name()
        # LSL XML parser has a bug which crashes so do not use for now
        #assert amp_serial == pylsl.StreamInlet(si).info().desc().child('acquisition').child_value('serial_number').strip()
        amp_inlet = pylsl.StreamInlet(si)
        logger.info('Selected %s (Serial: %s Inlet: %s)' % (amp_name, amp_serial, amp_inlet ))

        return amp_name, amp_serial, amp_inlet



def lsl_channel_list(inlet):
    """
    Reads XML description of LSL header and returns channel list

    Input:
        pylsl.StreamInlet object
    Returns:
        ch_list: [ name1, name2, ... ]
    """
    #UPDATE NUNO COSTa
    if not inlet.__class__ is pylsl.StreamInlet:
        raise TypeError('lsl_channel_list(): wrong input type %s' % inlet.__class__)
    root = ET.fromstring(inlet.info().as_xml())
    desc = root.find('desc')
    ch_list = []
    for ch in desc.find('channels').getchildren():
        ch_name = ch.find('label').text
        ch_list.append(ch_name)

    ''' This code may throw access violation error due to bug in pylsl.XMLElement
    # for some reason type(inlet) returns 'instance' type in Python 2.
    ch = inlet.info().desc().child('channels').first_child()
    ch_list = []
    for k in range(inlet.info().channel_count()):
        ch_name = ch.child_value('label')
        ch_list.append(ch_name)
        ch = ch.next_sibling()
    '''
    return ch_list


def formatxml(xml):
    xml = ET.fromstring(xml)
    return xml

def parseXmlToJson(xml):
    """
    usage:
        xml    = ET.fromstring(xml)
        parsed = parseXmlToJson(xml)

    #TODO: need update to add repeated child.tag

    """
    response = {}

    for child in list(xml):

        if len(list(child)) > 0:
#            if dictfinditem(response, child.tag):
#                n_name=child.tag
#                idx= n_name.find('_')
#                if idx:
#                    nr=int(n_name[idx+1])+1
#                    n_name=n_name[:idx+1]+str(nr)
#                else:
#                    n_name=n_name+'_1'#init
#                child.tag = n_name
            response[child.tag] = parseXmlToJson(child)
        else:
            response[child.tag] = child.text or ''

    # one-liner equivalent
    # response[child.tag] = parseXmlToJson(child) if len(list(child)) > 0 else child.text or ''

    return response


"""
ACTICHAMP - Amplifier
"""

import neuroprime.src.utils.montages.montage as mtage #NOTE with absolute_import can't do relative imports, like import montages
cap_chs_design=mtage.cap_chs_design #channels names
montage_file=mtage.montage_file# channels design

"""
Wyrm , Mushu functions
"""


def load_mushu_data(meta):#    Addaptation of wyrm.io.load_mushu_data()
    """
    Load saved EEG data in 'addapted' Mushu's format.

    This method loads saved data in 'addapted' Mushu's format and returns a
    continuous ``Data`` object.

    Parameters
    ----------
    meta : str
        Path to `.meta` file. A Mushu recording consists of three
        different files: `.dat`, `.marker`, and `.meta`.

    Returns
    -------
    dat : Data
        Continuous Data object

    Examples
    --------

    >>> dat = load_mushu_data('testrecording.meta')

    """
    # reverse and replace and reverse again to replace only the last
    # (occurrence of .meta)
    datafile = meta[::-1].replace('atem.', 'tad.', 1)[::-1]
    markerfile = meta[::-1].replace('atem.', 'rekram.', 1)[::-1]
    assert os.path.exists(meta) and os.path.exists(datafile) and os.path.exists(markerfile)
    # load meta data
    with open(meta, 'r') as fh:
        metadata = json.load(fh)
    fs = metadata['Sampling Frequency']
    channels = np.array(metadata['Channels'])
    # load eeg data
    data = np.fromfile(datafile, np.float32)
    data = data.reshape((-1, len(channels)))
    # load markers
    markers = []
    with open(markerfile, 'r') as fh:
        for line in fh:
            ts, m = line.split(' ', 1)
            markers.append([float(ts), str(m).strip()])
    # construct Data
    duration = len(data) * 1000 / fs
    axes = [np.linspace(0, duration, len(data), endpoint=False), channels]
    names = ['time', 'channels']
    units = ['ms', '#']
    dat = wyrm.types.Data(data=data, axes=axes, names=names, units=units)
    dat.fs = fs
    dat.markers = markers
    return dat

def read_file_from_mushu(filepath=None):
    meta=filepath
    if not filepath:
        meta = get_file_path()
    print (meta)
    data = load_mushu_data(meta)
    logger.warn(data)
    return data


def convert_units(dat, convertion=(1e-6, "V"), timeaxis=-2, package="wyrm"):
    cdat=None
    if package=="wyrm":
        data=dat.data*convertion[0]
        axes=dat.axes
        units=dat.units
        units[timeaxis]=convertion[1]
        names=dat.names
        cdat=dat.copy(data=data, axes=axes, units=units, names=names)

    return cdat

"""
MNE Functions
"""
# IO
# MUSHU to MNE

mne_unit_dict = {'V': 1,  # V stands for Volt
              u'µV': 1e-6,
              'uV': 1e-6,
              'nV': 1e-9,
              'C': 1,  # C stands for celsius
              u'µS': 1e-6,  # S stands for Siemens
              u'uS': 1e-6,
              u'ARU': 1,  # ARU is the unity for the breathing data
              'S': 1,
              'N': 1}  # Newton

def parse_file_montage(ch_names, montage_file):
    """Files with extensions
        '.elc', '.txt', '.csd', '.elp', '.hpts', '.sfp', '.loc' ('.locs' and
        '.eloc') or .bvef are supported.
    """
    logger.debug("\n>> MONTAGE_FILE: {}".format(montage_file))
    filedir, filename, ext = parse_path_list(montage_file)
    montage_mne = mne.channels.read_montage(filename,ch_names=ch_names, path=filedir, unit='cm')
    return montage_mne

montage_mne = parse_file_montage(cap_chs_design, montage_file)

def config_mne(fname=None, log_level="INFO"):
    #SET LOGGING PREFERENCE
    mne.set_config('MNE_LOGGING_LEVEL', log_level, set_env=True) #OR mne.set_log_level('INFO')
    mne.get_config_path()
    #SET LOG FILE
    mne.set_log_file(fname=fname, output_format='%(message)s', overwrite=None)
    #SET DEFAULT STIM CHANNEL FOR EVENTS - MNE DEFAULT is 'STI 014'
    mne.set_config('MNE_STIM_CHANNEL', 'STI101', set_env=True)


def mushu2fif(filepath, outdir=None, overwrite=False, precision='single'):
    mne.set_log_level('ERROR')

    #load mushu data to mne
    raw, event_id = mushu_to_mne(filepath, data_unit='uV')

    # dir
    fdir, fnametype=os.path.split(filepath)
    fname, ftype =os.path.splitext(fnametype)
    if outdir is None:
        outdir = fdir + '/fif/'
    elif outdir[-1] != '/':
        outdir += '/'
    assure_path_exists(outdir)
    #save
    outfile=outdir + fname
    outfilepath=outfile+ '.fif'
    raw.save(outfilepath, verbose=False, overwrite=overwrite, fmt=precision)
    outfilepath=outfile+ '_event_id.mat'
    scipy.io.savemat(outfilepath, event_id, oned_as='row')
    logger.info('Saved to %s' % outfile)


def mne2mat(raw, event_id, eeg_filepath, events_filepath, event_id_filepath):
    'converts raw mne EEG data into MAT format;'
    'events are stored in an extra file in EEGLab mat format.'

    'pick only eeg channels if you dont need'
    picks = mne.pick_types(raw.info, meg=False,eeg=True, stim=False)
    data, time = raw[picks,:]
    print ('saving eeg to', eeg_filepath)
    scipy.io.savemat(eeg_filepath, dict(data=data), oned_as='row')
    events = mne.find_events(raw, stim_channel='STI', shortest_event=0)

    # EEGLab event structure: type, latency, urevent
    # Event latencies are stored in units of data sample points relative to (0)
    # the beginning of the continuous data matrix (EEG.data).
    eeglab_events = [[event[2], event[0], 0] for event in events]
    eeglab_events = np.asarray(eeglab_events, dtype=int)

    print ('saving events to', events_filepath)
    scipy.io.savemat(events_filepath, dict(data=eeglab_events), oned_as='row')

    print ('saving event_id', event_id_filepath)
    scipy.io.savemat(event_id_filepath, event_id, oned_as='row')

def mushu_to_mne(filepath, chanaxis=-1, in_data_unit='uV', ch_names=cap_chs_design, ch_types="eeg", montage=montage_mne):
    #type of data
    raw_wyrm = load_mushu_data(filepath) #format: raw_wyrm.data samples x channels
    raw, event_id = raw_wyrm_to_mne(raw_wyrm,chanaxis=chanaxis, epoch=False, in_data_unit=in_data_unit, ch_names=ch_names, ch_types=ch_types, montage=montage)
    return raw, event_id



def raw_wyrm_to_mne(wyrmdata, chanaxis=-1,timeaxis=-2, epoch=False, in_data_unit='uV', ch_names=cap_chs_design, ch_types="eeg",check_ch_names=True, montage=montage_mne, stim_ch='STI 014', event_id_start=100, event_id_end=101, event_id_epo=102, convert_markers=True, add_event_option=1):
    """
    After loading mushu to wyrm format, convert to mne format

    wyrmdata: object holding data(eeg data samples x channels), axes,fs,markers,

    montage: montage file | mne montage;

    """
    #units
    factor=mne_unit_dict.get(in_data_unit, None)
    if not factor: raise RuntimeError("Add factor {} to mne_unit_dict!".format(in_data_unit))
    wyrmdata=convert_units(wyrmdata, convertion=(factor, 'V') ) #mne standard is votls
    #transpose
    data = wyrmdata.data.T #format to channels x samples
    ##wyrm data informations
    sfreq=wyrmdata.fs
    t0=wyrmdata.axes[timeaxis][0]  #first sample time =0
    tmax=wyrmdata.axes[timeaxis][-1] #last sample time =samples * ts
    if not wyrmdata.markers:#empty -bug
        wyrmdata.markers=[[t0,'START_BUG_MISSING_MARKER'],[tmax,'END_BUG_MISSING_MARKER']]
    t0_markers = wyrmdata.markers[0][0] #first timestamp
    tmax_markers=wyrmdata.markers[-1][0] #end timestamp
    try:
        assert (t0_markers>=t0 and t0_markers<=tmax) and (tmax_markers>=t0 and tmax_markers<=tmax)
    except Exception as e:
        logger.warning("\n>> #WARNING Strange Marker behavior, removing makers: {}! t0_markers={}, t0_samples={};tmax_markers={}, tmax_samples={}; ".format(e,t0_markers, t0, tmax_markers, tmax))
        #remove markers outside of sample range
        wyrmdata = wyrm.processing.clear_markers(wyrmdata)

    total_sample_number = wyrmdata.data.shape[0]
    assert total_sample_number == data.shape[1]
    logger.debug("#LIMITATION !!MNE EVENT MAX UNPRECISION: {} ms".format((1/sfreq)*1000.))
    ch_number=wyrmdata.data.shape[1]
    assert ch_number == data.shape[0] == len(wyrmdata.axes[chanaxis])



    #ADD EVENTS (transfer to code id)
    colum_1=[] # sample number
    colum_2=[] # timestamp - in thhis case I used timestamp
    logger.debug("MNE RAW SECOND COLUMN - timestamp - but normally is the onset and offset of events: output = ‘onset’ or ‘step’ - value of the stim channel immediately before the event/step output = ‘offset’ - value of the stim channel after the event offset")
    colum_3=[] # value=event_id int value
    for m in wyrmdata.markers:
        timestamp = m[0]
        name=m[1]
        sample_number = int(round((timestamp-t0)*sfreq/1000.))
        if sample_number == total_sample_number:  #if it round up to value above 0...total_sample_number-1
            sample_number= total_sample_number-1
        colum_1.append(sample_number)
        colum_2.append(int(round(timestamp)))
        #CONVERT MARKERS - LIMIT NUMBER of words to 3and add _
        r_item=name
        if convert_markers:
            us_item=name.split('_')#underscore
            cv_item=[]
            for it in us_item:
                #only two spaces and 3 words
                cs_it=it.replace(' ', '_',2)#replace the first 2 spaces
                s_it=cs_it.split(' ')#split by space and use first
                cs_it=s_it[0]#chosing only the first
                cv_item.append(cs_it)
            r_item='_'.join(cv_item)#joint again
        colum_3.append(r_item)

    #Create ID for each new marker
    result = list(set(colum_3)) #remove duplicates

    event_id={}
    start_likert=1
    end_likert=1
    for i, x in enumerate(result):
        event_id[x] = 10+i+1 #Create events based on new inputs
        if not x.upper().find("start".upper())==-1:
            event_id[x] = event_id_start
            if not x.upper().find("likert".upper())==-1:
                if start_likert<10:
                    event_id[x] = 10*event_id_start+(start_likert) #100**
                if start_likert>=10 and start_likert<100:#add more if conditions if you have above 100 questions
                    event_id[x] = 100*event_id_start+(start_likert)
                start_likert+=1
        if not x.upper().find("end".upper())==-1:
            event_id[x] = event_id_end
            if not x.upper().find("likert".upper())==-1:
                if end_likert<10:
                    event_id[x] = 10*event_id_end+(end_likert) #101**
                if end_likert>=10 and end_likert<100:#add more if conditions if you have above 100 questions
                    event_id[x] = 100*event_id_end+(end_likert)
                end_likert+=1
        if not x.upper().find("epo".upper())==-1: event_id[x] = event_id_epo
        if not x.upper().find("keypress".upper())==-1:
            s=x.split('_')
            event_id[x] = int(s[-1])+1 #BUG using the numbers from keypress +1 because zero can't be code
        if not x.upper().find("point".upper())==-1:
            s=x.split('_')
            event_id[x] = int(s[-1])+1000 #1000**

    #convert to int:
    int_colum_3 = [event_id[m] for m in colum_3]
    matrix = list(zip(colum_1, colum_2, int_colum_3))#Python3 update
    events = np.array(matrix)
    logger.debug("MNE RAW EVENTS: {}".format(events))

    #check ch_names
    chanaxis=-1
    server_ch_names=wyrmdata.axes[-1].tolist()
    if check_ch_names and ch_names and (not set(server_ch_names).issubset( ch_names)): 
        logger.error(">>ERROR: Check Ch names montage: \n>> server_ch_names: {} \n>> input cap ch_names: {}".format(server_ch_names, ch_names))
        if len(server_ch_names) != len(ch_names):
            raise AssertionError(">>ERROR: Check Ch names montage: \n>> server_ch_names: {} \n>> input cap ch_names: {}".format(server_ch_names, ch_names))
        else:
            logger.warning("\n>> I assume you now what your doing, they have the same lenght! therefore server_ch_names==ch_names")
            server_ch_names=ch_names
    if not ch_names or (len(server_ch_names) != len(ch_names)):
        ch_names=server_ch_names

    #check montage
    if montage and isinstance(montage, str): montage = parse_file_montage(ch_names, montage)

    #add event CH to data and update
    if add_event_option==1:#Faster
        # ADD stim channel
        if not stim_ch: stim_ch ='STI 014' # use default 'STI 014' if None
        stim_data = np.zeros((1, total_sample_number))
        data = np.concatenate((data, stim_data), axis=0) #data format :channels x samples
        ch_names = ch_names +[stim_ch]
        ch_types= [ch_types] * ch_number + ['stim'] #update ch_types
        ##create raw array
        info = mne.create_info(ch_names=ch_names, sfreq=sfreq, ch_types=ch_types, montage=montage)
        raw = mne.io.RawArray(data, info)
    if add_event_option==2:
        ##create raw array
        info = mne.create_info(ch_names=ch_names, sfreq=sfreq, ch_types=ch_types, montage=montage)
        raw = mne.io.RawArray(data, info)
        # ADD stim channel
        if not stim_ch: stim_ch ='STI 014' #use default 'STI 014' if None
        info = mne.create_info([stim_ch], raw.info['sfreq'], ['stim'])
        stim_data = np.zeros((1, len(raw.times)))
        stim_raw = mne.io.RawArray(stim_data, info)
        raw.add_channels([stim_raw], force_update_info=True)#could this be changing something
    # Add events
    raw.add_events(events, stim_channel=stim_ch) #if None default

#        # Extract data from the first 5 channels, from 1 s to 3 s.
#        sfreq = raw.info['sfreq']
#        data, times = raw[:5, int(sfreq * 1):int(sfreq * 3)]
#        _ = plt.plot(times, data.T)
#        _ = plt.title('Sample channels')


    return raw, event_id

def online_raw_wyrm2mne(wyrmdata, chanaxis=-1,timeaxis=-2, epoch=False, in_data_unit='uV', ch_names=cap_chs_design, ch_types="eeg",check_ch_names=True, montage=montage_mne, stim_ch='STI 014', event_id_start=100, event_id_end=101, event_id_epo=102, convert_markers=True):
    """
    After loading mushu to wyrm format, convert to mne format

    ONLINE faster method

    wyrmdata: object holding data(eeg data samples x channels), axes,fs,markers,

    montage: montage file | mne montage;

    """

    #units
    factor=mne_unit_dict.get(in_data_unit, None)
    if not factor: raise RuntimeError("Add factor {} to mne_unit_dict!".format(in_data_unit))
    wyrmdata=convert_units(wyrmdata, convertion=(factor, 'V') ) #mne standard is votls
    #transpose
    data = wyrmdata.data.T #format to channels x samples

    ##wyrm data informations
    sfreq=wyrmdata.fs
    t0=wyrmdata.axes[timeaxis][0]  #first sample time =0
    tmax=wyrmdata.axes[timeaxis][-1] #last sample time =samples * ts
    if not wyrmdata.markers:#empty -bug
        wyrmdata.markers=[[t0,'START_BUG_MISSING_MARKER'],[tmax,'END_BUG_MISSING_MARKER']]
    t0_markers = wyrmdata.markers[0][0] #first timestamp
    tmax_markers=wyrmdata.markers[-1][0] #end timestamp
    try:
        assert (t0_markers>=t0 and t0_markers<=tmax) and (tmax_markers>=t0 and tmax_markers<=tmax)
    except Exception as e:
        logger.warning("\n>> #WARNING Strange Marker behavior, removing makers: {}! t0_markers={}, t0_samples={};tmax_markers={}, tmax_samples={}; ".format(e,t0_markers, t0, tmax_markers, tmax))
        #remove markers outside of sample range
        wyrmdata = wyrm.processing.clear_markers(wyrmdata)

    total_sample_number = wyrmdata.data.shape[0]
    assert total_sample_number == data.shape[1]
    logger.debug("#LIMITATION !!MNE EVENT MAX UNPRECISION: {} ms".format((1/sfreq)*1000.))
    ch_number=wyrmdata.data.shape[1]
    assert ch_number == data.shape[0] == len(wyrmdata.axes[chanaxis])



    #ADD EVENTS (transfer to code id)
    colum_1=[] # sample number
    colum_2=[] # timestamp - in thhis case I used timestamp
    colum_3=[] # value=event_id int value

    #faster numpy
    np_m=np.array(wyrmdata.markers)
    c1 = np.around((np_m[:,0].astype(np.float)-t0)*sfreq/1000.).astype(np.int) #int(round((timestamp-t0)*sfreq/1000.))
    colum_1=c1.tolist()
    if colum_1[-1]>=total_sample_number: colum_1[-1]= total_sample_number-1 #just to make sure it is below the total_sample number
    c2=np.around(np_m[:,0].astype(np.float)).astype(np.int)
    colum_2=c2.tolist()
    c3=np_m[:,1]
    colum_3=c3.tolist()

    #Create ID for each new marker (using continue and only the events of NFT)
    result = list(set(colum_3)) #remove duplicates
    event_id={}
    for i, x in enumerate(result):
        event_id[x] = 10+i+1 #Create events based on new inputs #add numbers always
        if not x.upper().find("epo".upper())==-1:
            event_id[x] = event_id_epo
            continue
        if not x.upper().find("keypress".upper())==-1:
            s=x.split('_')
            event_id[x] = int(s[-1])+1 #BUG using the numbers from keypress +1 because zero can't be code
            continue
        if not x.upper().find("point".upper())==-1:
            s=x.split('_')
            event_id[x] = int(s[-1])+1000 #1000**
            continue
        if not x.upper().find("start".upper())==-1:
            event_id[x] = event_id_start
            continue
        if not x.upper().find("end".upper())==-1:
            event_id[x] = event_id_end
            continue




    #convert to int:
    int_colum_3 = [event_id[m] for m in colum_3]
    matrix = list(zip(colum_1, colum_2, int_colum_3))#Python3 update
    events = np.array(matrix)
    logger.debug("MNE RAW EVENTS: {}".format(events))



    #check ch_names
    chanaxis=-1
    server_ch_names=wyrmdata.axes[-1].tolist()
    if check_ch_names and ch_names and (not set(server_ch_names).issubset( ch_names)): 
        logger.error(">>ERROR: Check Ch names montage: \n>> server_ch_names: {} \n>> input cap ch_names: {}".format(server_ch_names, ch_names))
        if len(server_ch_names) != len(ch_names):
            raise AssertionError(">>ERROR: Check Ch names montage: \n>> server_ch_names: {} \n>> input cap ch_names: {}".format(server_ch_names, ch_names))
        else:
            logger.warning("\n>> I assume you now what your doing, they have the same lenght! therefore server_ch_names==ch_names")
            server_ch_names=ch_names
    if not ch_names or (len(server_ch_names) != len(ch_names)):
        ch_names=server_ch_names

    #check montage
    if montage and isinstance(montage, str): montage = parse_file_montage(ch_names, montage)

    #add event CH to data and update
    # ADD stim channel
    if not stim_ch: stim_ch ='STI 014' # use default 'STI 014' if None
    stim_data = np.zeros((1, total_sample_number))
    data = np.concatenate((data, stim_data), axis=0) #data format :channels x samples
    ch_names = ch_names +[stim_ch]
    ch_types= [ch_types] * ch_number + ['stim'] #update ch_types

    ##create raw array
    info = mne.create_info(ch_names=ch_names, sfreq=sfreq, ch_types=ch_types, montage=montage)
    #SLOW almost 100ms
    raw = mne.io.RawArray(data, info)

    # Add events
    raw.add_events(events, stim_channel=stim_ch) #if None default





    return raw, event_id


def epoch_wyrm_to_mne(wyrmdata, chanaxis=-1, epoch=False, ch_names=cap_chs_design, ch_types="eeg", montage = montage_mne):
    pass



def find_event_channel(raw, ch_names=None):
    """
    Adaptation of https://github.com/dbdq/neurodecode stream player by Kyuhwa Lee
    Find event channel using heuristics for pcl files.

    Disclaimer: Not guaranteed to work.

    Input:
        raw: mne.io.RawArray-like object or numpy array (n_channels x n_samples)

    Output:
        channel index or None if not found.
    """

    if type(raw) == np.ndarray:
        if ch_names is not None:
            for ch_name in ch_names:
                if 'TRIGGER' in ch_name or 'STI ' in ch_name:
                    return ch_names.index(ch_name)

        # data range between 0 and 255 and all integers?
        for ch in range(raw.shape[0]):
            if (raw[ch].astype(int) == raw[ch]).all()\
                    and max(raw[ch]) < 256 and min(raw[ch]) == 0:
                return ch
    else:
#        signals = raw._data
        for ch_name in raw.ch_names:
            if 'TRIGGER' in ch_name or 'STI ' in ch_name:
                return raw.ch_names.index(ch_name)

    return None

def event_timestamps_to_indices(sigfile, eventfile, offset=0):
    """
    Convert LSL timestamps to sample indices for separetely recorded events.

    Parameters:
    sigfile: raw signal file (Python Pickle) recorded with stream_recorder.py.
    eventfile: event file where events are indexed with LSL timestamps.
    offset: if the LSL server's timestamp is shifted, correct with offset value in seconds.

    Returns:
    events list, which can be used as an input to mne.io.RawArray.add_events().
    """

    raw = load_obj_pickle(sigfile)
    ts = raw['timestamps'].reshape(-1)
    ts_min = min(ts)
    ts_max = max(ts)
    events = []

    with open(eventfile) as f:
        for l in f:
            data = l.strip().split('\t')
            event_ts = float(data[0]) + offset
            event_value = int(data[2])
            # find the first index not smaller than ts
            next_index = np.searchsorted(ts, event_ts)
            if next_index >= len(ts):
                logger.warning('Event %d at time %.3f is out of time range (%.3f - %.3f).' % (event_value, event_ts, ts_min, ts_max))
            else:
                events.append([next_index, 0, event_value])
    return events

def pcl2mne(filepath, interactive=False, outdir=None, external_event=None, offset=0, overwrite=False, precision='single'):
    raw=None
    data = load_obj_pickle(filepath)
    if type(data['signals']) == list:
        signals_raw = np.array(data['signals'][0]).T  # to channels x samples
    else:
        signals_raw = data['signals'].T  # to channels x samples
    sample_rate = data['sample_rate']

    if 'ch_names' not in data:
        ch_names = ['CH%d' % (x + 1) for x in range(signals_raw.shape[0])]
    else:
        ch_names = data['ch_names']

    # search for event channel
    trig_ch_guess = find_event_channel(signals_raw, ch_names)
    if 'TRIGGER' in ch_names:
        trig_ch = ch_names.index('TRIGGER')
    elif 'STI ' in ch_names:
        trig_ch = ch_names.index('STI ')
    else:
        trig_ch = trig_ch_guess

    # exception
    if trig_ch is not None and trig_ch_guess is None:
        logger.warning('Inferred event channel is None.')
        if interactive:
            logger.warning('If you are sure everything is alright, press Enter.')
            input()

    # fix wrong event channel
    elif trig_ch_guess != trig_ch:
        logger.warning('Specified event channel (%d) != inferred event channel (%d).' % (trig_ch, trig_ch_guess))
        if interactive: input('Press Enter to fix. Event channel will be set to %d.' % trig_ch_guess)
        ch_names.insert(trig_ch_guess, ch_names.pop(trig_ch))
        trig_ch = trig_ch_guess
        logger.info('New channel list:')
        for c in ch_names:
            logger.info('%s' % c)
        logger.info('Event channel is now set to %d' % trig_ch)

     # move trigger channel to index 0
    if trig_ch is None:
        # assuming no event channel exists, add a event channel to index 0 for consistency.
        logger.warning('No event channel was not found. Adding a blank event channel to index 0.')
        eventch = np.zeros([1, signals_raw.shape[1]])
        signals = np.concatenate((eventch, signals_raw), axis=0)
        num_eeg_channels = signals_raw.shape[0] # data['channels'] is not reliable any more
        trig_ch = 0
        ch_names = ['TRIGGER'] + ['CH%d' % (x + 1) for x in range(num_eeg_channels)]
    elif trig_ch == 0:
        signals = signals_raw
        num_eeg_channels = data['channels'] - 1
    else:
        # move event channel to 0
        logger.info('Moving event channel %d to 0.' % trig_ch)
        signals = np.concatenate((signals_raw[[trig_ch]], signals_raw[:trig_ch], signals_raw[trig_ch + 1:]), axis=0)
        assert signals_raw.shape == signals.shape
        num_eeg_channels = data['channels'] - 1
        ch_names.pop(trig_ch)
        trig_ch = 0
        ch_names.insert(trig_ch, 'TRIGGER')
        logger.info('New channel list:')
        for c in ch_names:
            logger.info('%s' % c)

    ch_info = ['stim'] + ['eeg'] * num_eeg_channels
    info = mne.create_info(ch_names, sample_rate, ch_info)

    # create Raw object
    raw = mne.io.RawArray(signals, info)
    raw._times = data['timestamps'] # seems to have no effect

    if external_event is not None:
        raw._data[0] = 0  # erase current events
        events_index = event_timestamps_to_indices(filepath, external_event, offset)
        if len(events_index) == 0:
            logger.warning('No events were found in the event file')
        else:
            logger.info('Found %d events' % len(events_index))
        raw.add_events(events_index, stim_channel='TRIGGER')

    return raw

def pcl2fif(filepath, interactive=False, outdir=None, external_event=None, offset=0, overwrite=False, precision='single'):
    pass#todo

"""
Psychopy Functions
"""

def addPsychopyPath(PSYCHOPY_FOLDER, PSYCHOPY_VERSION_EGG):
    # PSYCHOPY add Path (change [PSYCHOPY_FOLDER, folder_package, PSYCHOPY_VERSION_EGG])
    folder_package = os.path.join("Lib", "site-packages")
    psychopy_path_1 = os.path.join(PSYCHOPY_FOLDER, folder_package)
    psychopy_path_2 = os.path.join(psychopy_path_1, PSYCHOPY_VERSION_EGG)
    if os.path.isdir(psychopy_path_1) and os.path.isdir(psychopy_path_2):
        if any(psychopy_path_1 in pathlist for pathlist in sys.path):
            logger.warn("path already exists: " + psychopy_path_1)
        else:
            sys.path.append(psychopy_path_1)  # temporary in session
        if any(psychopy_path_2 in pathlist for pathlist in sys.path):
            logger.warn("path already exists: " + psychopy_path_2)
        else:
            sys.path.append(psychopy_path_2)
    else:
        sys.exit("ERROR: paths wrong!")

class Sound(object):
    """
    A windows-only low-latency replacement for psychopy.sound.
    It can only play wav files. Timing is unrel ble if sound.play() is called before previous sound ends. Usage::
        beep = ppc.Sound('beep.wav')
        beep.play()

        # or generated beep:
        beep = ppc.Sound()
        beep.beep(1000, 0.2)  # 1000 Hz for 0.2 seconds
    """
    def __init__(self, filename=''):
        """ :filename: a .wav file"""
        self.sound = filename
        self._winsound = __import__('winsound')

    def play(self):
        """ plays the sound file with low latency"""
        self._winsound.PlaySound(self.sound,  self._winsound.SND_FILENAME | self._winsound.SND_ASYNC)

    def beep(self, frequency, duration):
        """ plays a beep with low latency"""
        self._winsound.Beep(frequency, duration / float(1000))


def timer(script, setup='', timeScale=False, runs=False):
    """
    Times code snippets and returns average duration in seconds.

    :script: a string to be timed
    :setup: a comma-separated string specifying methods and variables to be imported from __main__
    :timeScale: the unit for seconds. 10**-9 = nanoseconds. If False, the scale is automagically determined as s, ms, us or ns
    :runs: how many times to run the script. If False, the number of runs is automagically determine from 3 testruns, trying to keep the total test duration around a second but at least 10 runs and at most 10**6 runs.
    """
    if setup:
        setup = 'from __main__ import ' + setup

    import timeit
    timeit.timeit(number=10**7)  # get the computer's attention/ressources. First run is slower.

    # optional: determine appropriate number of runs from 3 test runs
    if not runs:
        result = timeit.timeit(script, setup=setup, number=3)
        runs = int(3 / result) if result > 0 else 10 ** 6
        if runs > 10 ** 6: runs = 10 ** 6  # a million at most
        if runs < 10: runs = 10  # ten at least

    # Actually do the timing
    baseline = timeit.timeit(setup=setup, number=runs)  # the time it takes to run an empty script
    result = timeit.timeit(script, setup=setup, number=runs)  # Run the test!
    mean = (result - baseline) / runs  # in seconds

    # Optional: determine appropriate timeScale for reporting
    if not timeScale:
        timeScale = 1 if mean > 1 else 10**-3 if mean > 10**-3 else 10**-6 if mean > 10**-6 else 10**-9
    unit = 's' if timeScale == 1 else 'ms' if timeScale == 10**-3 else 'us' if timeScale == 10**-6 else 'ns' if timeScale == 10**-9 else '*' + str(timeScale)

    # print (results
    print ('\n\'', script, '\'')
    print ('AVERAGE:', round(mean / timeScale, 3), unit, 'from', runs, 'runs')


def deg2cm(angle, distance):
    """
    Returns the size of a stimulus in cm given:
        :distance: ... to monitor in cm
        :angle: ... that stimulus extends as seen from the eye

    Use this function to verify whether your stimuli are the expected size.
    (there's an equivalent in psychopy.tools.monitorunittools.deg2cm)
    """
    import math
    return math.tan(math.radians(angle)) * distance  # trigonometry


class csvWriter(object):
    def __init__(self, saveFilePrefix='', saveFolder=''):
        """
        Creates a csv file and appends single rows to it using the csvWriter.write() function.
        Use this function to save trials. Writing is very fast. Around a microsecond.

        :saveFilePrefix: a string to prefix the file with
        :saveFolder: (string/False) if False, uses same directory as the py file

        So you'd do this::
                # In the beginning of your script
                writer = ppc.csvWriter('subject 1', 'dataFolder')

                # In the trial-loop
                trial = {'condition': 'fun', 'answer': 'left', 'rt': 0.224}  # your trial
                writer.write(trial)
        """
        import csv, time

        # Create folder if it doesn't exist
        if saveFolder:
            import os
            saveFolder += '/'  # - Update Nuno Costa
            if not os.path.isdir(saveFolder):
                os.makedirs(saveFolder)

        # Generate self.saveFile and self.writer
        self.saveFile = saveFolder + str(saveFilePrefix) + ' (' + time.strftime('%Y-%m-%d %H-%M-%S', time.localtime()) +').csv'  # Filename for csv. E.g. "myFolder/subj1_cond2 (2013-12-28 09-53-04).csv"
        self.writer = csv.writer(open(self.saveFile, 'wb'), delimiter=';').writerow  # The writer function to csv. It appends a single row to file
        self.headerWritten = False

    def write(self, trial):
        """:trial: a dictionary"""
        if not self.headerWritten:
            self.headerWritten = True
            self.writer(trial.keys())
        self.writer(trial.values())

def getActualFrameRate(frames=1000):
    """
    Measures the actual framerate of your monitor. It's not always as clean as
    you'd think. Prints various useful information.
        :frames: number of frames to do test on.
    """
    from psychopy import visual, core

    # Set stimuli up
    durations = []
    clock = core.Clock()
    win = visual.Window(color='pink')

    # Show a brief instruction / warning
    visual.TextStim(win, text='Now wait and \ndon\'t do anything', color='black').draw()
    win.flip()
    core.wait(1.5)

    # blank screen and synchronize clock to vertical blanks
    win.flip()
    clock.reset()

    # Run the test!
    for i in range(frames):
        win.flip()
        durations += [clock.getTime()]
        clock.reset()

    win.close()

    # print (summary
    import numpy as np
    print ('average frame duration was', round(np.average(durations) * 1000, 3), 'ms (SD', round(np.std(durations), 5), ') ms')
    print ('corresponding to a framerate of', round(1 / np.average(durations), 3), 'Hz')
    print ('60 frames on your monitor takes', round(np.average(durations) * 60 * 1000, 3), 'ms')
    print ('shortest duration was ', round(min(durations) * 1000, 3), 'ms and longest duration was ', round(max(durations) * 1000, 3), 'ms')


def dkl2rgb(dkl):
    """ takes a DKL color as input and returns the corresponding RGB color """
    from numpy import array
    from psychopy.misc import dkl2rgb
    return dkl2rgb(array(dkl))












