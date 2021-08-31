#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Thu Dec 14 19:54:32 2017

@author: nm.costa
"""

import time, pylsl
contResolver = pylsl.ContinuousResolver()
inlet = None
while True:
    streams = contResolver.results()
    stream_names = [si.name() for si in streams]
    print(stream_names)
    time.sleep(0.5)