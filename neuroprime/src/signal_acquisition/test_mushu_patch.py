# -*- coding: utf-8 -*-
"""
Created on Fri May 03 17:02:39 2019

@author: nm.costa
"""
from __future__ import (absolute_import, division, print_function)
from builtins import * #all the standard builtins python 3 style



#signal acquisition
#import mushu_patch_v3 as patch
import neuroprime.src.signal_acquisition.mushu_patch as patch #test current bci version

import pylsl
import time
import timeit
import numpy
import os
# My functions
import neuroprime.src.utils.myfunctions as my

import logging
logging.basicConfig(level=logging.INFO)






def loop_get_data(amp, stop_counter=100):
    pid_os=os.getpid()
    #loop
    counter=0
    previous_time=timeit.default_timer()
    previous_time_lsl=pylsl.local_clock()
    elapsed_time_a=[]
    elapsed_time_a_lsl=[]
    received_samples_a=[]
    print ('Starting LOOP')
    sys.stdout.flush() #flush the results buffer and print emideatly to screen
    while counter<stop_counter:
        print ('Getting data...')
        sys.stdout.flush() #flush the results buffer and print emideatly to screen
        data, markers=amp.get_data()
        #Time after geting data
        current_time = timeit.default_timer()
        current_time_lsl = pylsl.local_clock()
        elapsed_time=current_time-previous_time
        elapsed_time_lsl=current_time_lsl-previous_time_lsl
        previous_time = current_time
        previous_time_lsl = current_time_lsl

        print(">> PROCESS OS:{} ".format(pid_os))

        print(">> local time:{} s".format(current_time))
        print(">> local time LSL:{} s".format(current_time_lsl))
        print(">> elapsed time:{} s".format(elapsed_time))
        print(">> elapsed time LSL:{} s".format(elapsed_time_lsl))
        if markers:
            for m in markers:
                print(">> markers: {},{}".format(m[0],m[1]))
        print(">> received samples: {}".format(len(data)))
        elapsed_time_a.append(elapsed_time)
        elapsed_time_a_lsl.append(elapsed_time_lsl)
        received_samples_a.append(len(data))
        counter+=1

        sys.stdout.flush() #flush the results buffer and print emideatly to screen
        time.sleep(0.01)#to fast block to the minimum of blocksize - is not relevant to be faster -probably add this in get_data with block_size





    #plot data
    import matplotlib.pyplot as plt
    import numpy as np
    plt.close('all')

    #Buffer amp
    plt.figure(2)
    y = np.array(amp.amp.samples_buffer)#format: samples X channels
    print("y amp2 buffer shape", y.shape)
    y=y[:, 1]
    y2=y[0:20]
    x = np.arange(len(y))
    plt.plot(x, y,'.', color = 'r', label='buffer')

    #log time
    elapsed_time_a=numpy.array(elapsed_time_a)
    elapsed_time_a_lsl=numpy.array(elapsed_time_a_lsl)
    received_samples_a= numpy.array(received_samples_a)
    try:
        print(">> PROCESS OS:{} ".format(pid_os))
        print(">> Average elapsed Time, timeit.default_timer():{} s; pylsl.local_clock:{} s".format(elapsed_time_a.mean(), elapsed_time_a_lsl.mean() ))
        print(">> Average received samples: {}".format(received_samples_a.mean()))
        print(">> samples_buffer: {}".format(len(amp.amp.samples_buffer)))
        print(">> received_samples_buffer: {}".format(amp.amp.received_samples_buffer[-1]))
        print(">> markers_buffer: {}".format(amp.amp.markers_buffer_tc[-1]))
    except Exception as e:
        print("ERROR: {}".format(e))
        pass
    sys.stdout.flush() #flush the results buffer and print emideatly to screen

    return amp

def hrv_worker(run):
    p = multiprocessing.current_process()
    print ('Starting:', p.name, p.pid)
    #Init amp
    hrv = patch.libmushu.get_amp('lslamp')
    #config amp
    hrv.configure(stream_type='HRV', stream_server='lsl', lsl_amp_name='HRV', lsl_marker_name="PyffMarkerStream")
    amp=hrv
    while True:
        if run.value:
            amp.start()
            amp=loop_get_data(amp)#update amp
            #stop() amp to close files
            amp.stop()
            run.value=not run.value






if __name__ == "__main__":
    #TEST FOLDER for files
    test_folder_path=my.get_test_folder(foldername='temp_test')


    #TEST save in multiprocessing (Something wrong in saving )
    TEST_0=True
    if TEST_0:
        data = {'signals': 'lool'}
        #file
        timestamp = time.strftime('%d%m%Y_%Hh%Mm', time.localtime())
        datadir=test_folder_path
        method="pcl"
        filepath=os.path.join(datadir,'e2_test_save_in_subprocess' +'_'+timestamp+'.'+method)
        subsave=my.save_in_subprocess(data, filepath, method=method)
        subsave.save()



    #test 1- Test lsl client performance (Actichamp App and Brainvision RDA App)
        #ACTICHAMP APP: sampleRate =1000hz counter=3000 elapsed time average= :0.0161090831667 s =16 ms; Average received samples(chunk size) = 16.113
        #Brainvision RDA App: sampleRate =1000hz counter=3000; elapsed time average= 0.0433990042 s = 43ms ; Average received samples(chunk size) = 43.413
    TEST_1 = False
    if TEST_1:
        #file
        timestamp = time.strftime('%d%m%Y_%Hh%Mm', time.localtime())
        datadir=test_folder_path
        filename=os.path.join(datadir,'e2_mushu_test_4_rdalsl' +'_'+timestamp)  #None -No Saving

        lsl_amp_name='BrainVision RDA'##'Actichamp-0' or 'BrainVision RDA'
        lsl_marker_name='BrainVision RDA Markers'#'ActiChamp-0-Markers' or'BrainVision RDA Markers'

        eeg = patch.libmushu.get_amp('lslamp')
        eeg.configure(stream_type='EEG', stream_server='lsl', lsl_amp_name=lsl_amp_name, lsl_marker_name=lsl_marker_name, lsl_save_buffers=True)

        #check for
        while True:
            try:
                eeg.start(filename)
                eeg=loop_get_data(eeg, stop_counter=float("inf"))
                eeg.stop()
                break
            except Exception as e:
                eeg.stop()#save and reset previous
                op=input('??? Exception Ocurred: {} ??? \n>> Do you want to restart task: enter 1 \n>> If Not, close the program: enter 2\n>>'.format(e))
                op=str(op)
                if op=='1':
                    continue
                else:
                    raise RuntimeError("User choose option {} , close the program!".format(op))





    #test 3.5.1- multiprocessing loop
        #hrv - 0.114s - 100 samples
        #warning: only works with amp object initiated inside the child process
        #warning: passing amp object as an arg to the child process, or directly to the worker function does not work
    TEST_35_1 =False
    if TEST_35_1:
        import multiprocessing
        import logging
        import sys

        multiprocessing.log_to_stderr()
        logger = multiprocessing.get_logger()
        logger.setLevel(logging.DEBUG)

        #Sharing state between processes¶ - Method: shared memory map Value
        run = multiprocessing.Value('b', False) #start False
        print("run.value", run.value)

        starttime = time.time()

        p = multiprocessing.Process(name="loop_get_data", target=hrv_worker, args=(run,))
        p.daemon=True #To exit the main process even if the child process p didn't finished

        p.start() #start process

        time.sleep(5)
        run.value= True #Start True

        #join to block main process until timeout
        #p.join(10) #block until process finished (works even for daemon)
        #block main process till the finish of the loop
        while True:
            if not run.value: break

        if p.is_alive():
            p.terminate() #force termination
            p.join() #wait to terminate
            print("Process ALive: ",p.is_alive())
        print('That took {} seconds'.format(time.time() - starttime))



    #TEST 3.5.2 - Test times using multiprocessing
        #EEG - 0.019s average - 100 samples
        #HRV - 0.114s average - 100 samples
    TEST_35_2 = False
    if TEST_35_2:
        ##INIT EEG - INIT & CONFIG AMP object
        eeg = patch.libmushu.get_amp('lslamp')
        eeg.configure(stream_type='EEG', stream_server='lsl', lsl_amp_name='Actichamp', lsl_marker_name="PyffMarkerStream")
        ##INIT HR - INIT & CONFIG AMP object
        import multiprocessing
        import logging
        multiprocessing.log_to_stderr()
        logger = multiprocessing.get_logger()
        logger.setLevel(logging.DEBUG)
        #Sharing state between processes¶ - Method: shared memory map Value
        run = multiprocessing.Value('b', False) #start False
        print("run.value", run.value)
        #child process
        p = multiprocessing.Process(name="loop_get_data", target=hrv_worker, args=(run,))
        p.daemon=True #To exit the main process even if the child process p didn't finished - less constrictions between processes?
        p.start() #start process

        ##GET DATA LOOP
        starttime = time.time()
        #HRV
        run.value= True #Start child loop
        #EEG
        eeg=loop_get_data(eeg) #start main process loop
        #block main process till child finish the child loop
        while True:
            if not run.value: break
        print('That took {} seconds'.format(time.time() - starttime))

        ##QUIT
        #Child process still alive because of worker loop
        if p.is_alive():
            p.terminate() #force termination
            p.join() #wait to terminate
            print("Process ALive: ",p.is_alive())


    #test 3.5.3 - Test each amp in main process to compare
    TEST_35_3 = False
    if TEST_35_3:
        #file
        timestamp = time.strftime('%d%m%Y_%Hh%Mm', time.localtime())
        datadir=test_folder_path#'/Users/nm.costa/Desktop/temp_test'#'C:/Users/admin.DDIAS4/Desktop/temp_test'


        lsl_amp_name='BrainVision RDA'#'Actichamp'
        lsl_marker_name='BrainVision RDA Markers'#"PyffMarkerStream"

        #eeg - 0.019s average - 100 samples
        eeg = patch.libmushu.get_amp('lslamp')
        eeg.configure(stream_type='EEG', stream_server='lsl', lsl_amp_name=lsl_amp_name, lsl_marker_name=lsl_marker_name)
        filename=os.path.join(datadir,'EEG_test_353_files' +'_'+timestamp)
        eeg.start(filename)
        eeg=loop_get_data(eeg)
        eeg.stop()
        #input('Pause for Inspection: click enter to continue...') #does not work in spyder - to work running a Python script in interactive way - external system file
        #hrv - 0.114s average - 100 samples
        test_hrv=False
        if test_hrv:
            hrv = patch.libmushu.get_amp('lslamp')
            hrv.configure(stream_type='HRV', stream_server='lsl', lsl_amp_name='HRV', lsl_marker_name="PyffMarkerStream")
            hrv.start()
            loop_get_data(hrv)
            hrv.stop()


    #test 3.5.4 - Test amp subprocess class from initbciclass()
    TEST_35_4 = False
    if TEST_35_4:
        # My classes
        from neuroprime.src.initbciclass import get_amp_subprocess


        #file
        timestamp = time.strftime('%d%m%Y_%Hh%Mm', time.localtime())
        datadir=test_folder_path#'C:/Users/admin.DDIAS4/Desktop/temp_test'
        filename=os.path.join(datadir,'test_354_files' +'_'+timestamp)

        #init amp
        hrv=get_amp_subprocess(filepath=filename, process_name='HR')
        hrv.configure(stream_type='HR', stream_server='lsl', lsl_amp_name='HR', lsl_marker_name="PyffMarkerStream")


        #loop and get_data
        hrv.start()

        #stop loop
        hrv.stop()


        #quit subproces amp
        hrv.quit()





    #test 3.5.5 - Test 2 amp subprocess class from initbciclass()
        #WARNING: MARKER PROBLEMS
    TEST_35_5 = False
    if TEST_35_5:
        # My classes
        from neuroprime.src.initbciclass import get_amp_subprocess


        #file
        timestamp = time.strftime('%d%m%Y_%Hh%Mm', time.localtime())
        datadir=test_folder_path#'C:/Users/nbugz/Desktop/temp_test'#'/Users/nm.costa/Desktop/temp_test'#'C:/Users/admin.DDIAS4/Desktop/temp_test'
        filename=os.path.join(datadir,'test_355_files' +'_'+timestamp)

        #init amp
        gsr=get_amp_subprocess(filepath=None,  process_name='GSR')#get_amp_subprocess(filepath=None, save_task=False, process_name='GSR')
        gsr.configure(stream_type='GSR', stream_server='lsl', lsl_amp_name='GSR', lsl_marker_name="PyffMarkerStream")


        hr=get_amp_subprocess(filepath=filename, save_task=False, process_name='HR')
        hr.configure(stream_type='HR', stream_server='lsl', lsl_amp_name='HR', lsl_marker_name="PyffMarkerStream")
    #
    #
    #    #loop and get_data
        gsr.start()
        hr.start()

        #stop loop
        gsr.stop()
        hr.stop()


        #quit subproces amp
        gsr.quit()
        hr.quit()





