SIGNAL PRESENTATION TUTORIAL
^^^^^^^^^^^^^^^^^^^^^^^^^^^^
1.1 Start Pyff version 2012.6  
------------------------
1.2.Start new python shell in the appropriate environment
    terminal:
        $ source activate pyffEV
        $ cd '..yourpathphdproject/maincode/modules/pyff' 
        $ python FeedbackController.py --protocol=json --additional-feedback-path="path to feedbacks folder"  # because wyrm needs to comunicate in JSON format
    
    OR
    
    Bash script start_pyff: 
        1.Update paths of bash scripts
        2.Start bash scripts

    WARNING: Preferebly use the batch - because it adds the necessary feedbacks folder
        
        
1.3. ADD more feedbacks to Feedbacks folder feedbackapps by adding a new .py to the folder and update de feedback.list. 

1.4. To check if new plugins are installed go to pyff->src->lib->PluginController.py, or use the GUI to verify.
    

2. Use Psychopy instead of Pyff (TODO)
-----------------------------------
2.1 Install standalone version, or add to the requirements_phdEV.txt the necessary modules(see page online) (TODO: PSYCHOPY still needs development)
    2.1.2 Easy way(TODO): 
        1.Create in builder the tasks;
        2.Export python code;
        3.Add an outlet stream with pylsl for presentation markers
        4.add an inlet stream in virtual actichamp configuration
        5.update main code to use psychopy presentation instead of pyff (like when to start and stop presentation,etc)
    2.1.3 hard way1(TODO):
        Mix psychopy with pyff in a class.
        How it works: Instead of using pygame for presentation of feedbacks - use psychopy tools:
        1.create something similar to PygameFeedback.py class((TODO: Already done but with some errors on mac os - psychopyfeedback.py -> in bcitests>presentation>psychopy_tests folder)
    2.1.3 hard way2(TODO):
        Create psychopy classes similar to pyff hirarchical classes structure:
        1.Feedback class
        2.Mainloop class
            * :func:`on_init`
            * :func:`on_play`
            * :func:`on_pause`
            * :func:`on_stop`
            * :func:`on_quit`
            * :func:`init`
            * :func:`pre_mainloop`
            * :func:`post_mainloop`
            * :func:`tick`
            * :func:`pause_tick`
            * :func:`play_tick`




SIGNAL ACQUISITION TUTORIAL
^^^^^^^^^^^^^^^^^^^^^^^^^^^^
1. Start Stream of Data from amplifier
------------------------
1.1 In windows use Actichamp LSL APP located in modules folder (NOTE: Create a shortcut to start the app)
    
        
NOTE:
Lower chunk size to minimum fs=1000 chunksize=10ms:
My hardware supports different block/chunk sizes. Which one is best for use with LSL? 
The chunk size trades off latency vs. network overhead, so we suggest to allow the user to override the value if desired. A good range for the default value is between 5-30 milliseconds of data (resulting in an average latency that is between 2.5-15 ms and an update rate between 200-30 Hz). Shorter chunks make sense in very low-latency control settings, though note that chunks that comprise only a few bytes of data waste some network bandwidth due to the fixed Ethernet packet overhead. Longer chunks can also be used (any duration is permitted, e.g. for sporadic data logging activities), although the longer the chunks are the harder it becomes to perform sample-accurate real-time time-synchronization (specifically, removing the jitter in the chunk time stamps): the longest chunks that can be synchronized in real time would be around 100ms in typical settings.

1.2 Other OS only work through a lan networt with a windows PC because actichamp only has drivers for windows

2. Add montage to the code (go to montage folder and add in montage.py)
------------------------
Change montage according to server chs info


SIGNAL PROCESSING AND CLASSIFICATION TUTORIAL - START EXPERIMENT
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
1.1 Start Wyrm and mushu
------------------------
$ activate phdEV
$ cd '..yourpath/phdproject/maincode/src/)' 
$ python bci.py

Or 

start_bci.bat


What it will do the bci.py:
    0. GUI Dialogue 
    1.Initialize, configure and start: 
        S.Presentation, Pyff communication object; 
        S.Acquisition, an amplifier instance for Actichamp Stream
    2.Signal processing and classification
    


    



    
    
