# -*- coding: utf-8 -*-
# Copyright (C) 2019 Nuno Costa
# License: BSD (3-clause)
"""neuroprime update with pylsl functions"""

__version__ = '1.0+dev'

import time
import os
import logging

#logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
#console_handler = logging.StreamHandler()
#logger.addHandler(console_handler) #use it to send to console directly
filelogger=False
if filelogger:
    filename = time.strftime("%d%m%Y") + '_' + time.strftime("%Hh%Mm") + '_'+__name__+'.log'
    #make dir
    filepath =os.path.join('logs',filename)
    dir_p = os.path.dirname(os.path.normpath(filepath))
    if not os.path.exists(dir_p): os.makedirs(dir_p)
    file_handler = logging.FileHandler(filename)
    #create a filelogging format
    formatter = logging.Formatter('%(asctime)s - %(name)s -  %(levelname)s - func:%(funcName)s - line:%(lineno)d - msg:%(message)s')
    file_handler.setFormatter(formatter)
    #add handler
    logger.addHandler(file_handler) #uncomment if log file wanted

