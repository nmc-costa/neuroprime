# NeuroPrime
A framework for real-time HCI/BCI. Specifically developed for advanced human-computer assisted self-regulation of Neurofeedback.

The software will be available as soon as it is published (in the upcoming months). Consequently, in the upcoming months, if one has an EEG, then one can try out the framework, use it for research, and contribute to its development.

Simplicity and reusability are the foundation of NeuroPrime package, as is intended to be an open source project to be used by the neuroscience community. It is also intended to be a BCI hub that evolves with a synthesis of the best packages the python community has to offer in terms of signal processing, signal presentation and signal acquisition. Therefore, it should provide an easy and simple structure to update and connect new packages within the same design.

## Basic layout
![](neuroprime_diagram.png)

## Overview

NeuroPrime toolbox by @nmc-costa.

NeuroPrime was built on Python open source language, synthesizing while using the best parts, we extensively tested, from specific BCI and EEG modules, for signal acquisition, signal processing/classification and signal presentation (diagram above). Signal Acquisition: pycorder (Brain Products, Gilching, Germany), pylsl/lab streaming layer (SCCN, 2014), and mushu (Venthur & Blankertz, 2012). Signal processing/classification: wyrm (Venthur & Blankertz, 2014) and mne (Gramfort et al., 2013). Signal presentation: pyff (Venthur et al., 2010) and psychopy (Peirce, 2007). Additionally, some other important packages, pandas for managing data, matplotlib for graphs, numpy for arrays, scipy for specific algorithms, pygatt for bluethooth connectivity with GSR and HR sensors, and also pyqtgraph for real-time graphical interfaces (Jones, Oliphant, & Peterson, 2001; Mckinney, 2010; Oliphant, 2006).

Framework for EEG Neurofeedback in python. Needed for simple experiment depoilment and future online machine learning.


Current Specific packages used in:
- Acquisition - Lab Streaming Layer - library pylsl; Actichamp app from LSL; Pycorder RDA client; Mushu for handling with read/write from LSL streams
- Processing/classification - Wyrm to make bridge with Mushu and pyff; MNE for advanced processing.
- Presentation - PYFF and some functions from Psychopy - in the future should intirely update to Psychopy.


## Status
In its current version the software is stable. 

#### Python: 
- [x] NeuroPrime environment is in Python 2.7 with compatibility for Python 3; 
    - [ ] **#TODO**: update completely to Python 3 
- [x] Pyff environment is in python 2.7, it runs independently of NeuroPrime;
- [x] For Brain Vison actichamp users, pycorder environment is in python 2.6;


#### Acquisition(read/write):
- [x] pylsl: 
    - [x] **#WORKING** 
    - [x] Actichamp LSL: RDA app **#WORKING** in windows; **#UPDATE** to [LSL viewer](https://pressrelease.brainproducts.com/lsl-viewer/)
- [x] Mushu: 
    - [x] **#WORKING** with patch for LSL to read/write data, because of **#LIMITATIONS** in original mushu package: specific data Structure LSL driver support lacks robustness (no block buffer, no timeout and error assessement)

#### Processing/classification
- [x] wyrm:
    - [x] **#WORKING**
- [x] mne:
    - [x] **#WORKING** 
    - [x] **#BUG** installing in mac os - print(end='') gives error for mne=0.18 - run `< python -c 'import mne; mne.sys_info()'>` to see if mne is working - try also restarting PC
    - [ ] **#TODO**:
        - [ ] simplify nftalgorithm 

#### Presentation:
   Pyff:
       #WORKING using package instructions and specific dependencies
       shown below (compatible with python 2.7)

   Psychopy:
       Full implementation still in development (\#Not working)
       #TODO create coder decorator for windows


Installing & Dependedcies
=========================

1- Easy install python with Anaconda or miniconda 2- CHECK update and
upgrades: - pip normally needs to install additional pakcages(like
argparse): pip install --upgrade pip On Windows the recommended command
is: python -m pip install --upgrade pip pip install argparse msgpack pip
install ipykernel - For windows install GIT to update packages from
github: <https://git-scm.com/download/win> compiler for python: For
windows Microsoft visual C++ compiler is needed:
<http://aka.ms/vcpython27> Or alternatively use visual studio compiler:
<https://stackoverflow.com/questions/29909330/microsoft-visual-c-compiler-for-python-3-4>

3- ACQUISTION
:   Install your amplifier drivers.

    Pylsl:
    :   It installs pylsl.py and the lsl libs necessary for the os

    MUSHU - Virtual amplifier (1.already creates methods for
    labstreaminglayer synchronization;2.configure, start and stop
    amplifier method; 3.io methods: get\_data; save\_data )

    > \#TODO:
    > :   Mushu has a good virtual amp structure, but possibly gona
    >     simplify so you dont need to install, only pylsl
    >     (replay,receive,record) and mne(fif data struct): Also, the
    >     package is not maintained for some years Robustness: Remove
    >     deprecated Mushu package and Derive simple class from patch OR
    >     update libmushu and add the patch as a new driver
    >
    > \#BUG: LSL Data saving has problems - probably:
    > :   block function (using pylsl timeout forever); - LSL (default )
    >     saving (specific data structure); loading (wyrm load can )
    >     Transforming (from mushu to mne data format can have problems)
    >
    > \#DONE: Patch
    > :   :added support for BVP pycorder rda acquistion :added support
    >     for Pycnbi package acquistion :added amp.configure()
    >     connection timeouts :added amp.start() validation timeouts
    >     :added specific block size when asking for data
    >     amp.get\_data() (\#Performance still needs checking) :added
    >     amp.get\_data() timeout and error manegement :added data
    >     buffers to store data in amp object till you amp.start()
    >     again. Now you have the possibility of using privious
    >     get\_data samples, or save only in the end. :removed support
    >     for tcp/udp markers (it was just to see if the performance
    >     changed, but it wont change, so you can enable them again)
    >
4- PRESENTATION - PYFF or PSYCHOPY:
:   PYFF
    :   1- Create virtual environment with conda yml file or with the
        requirements\_pyffEV.txt (\$ pip install -r
        requirements\_pyffEV.txt). WARNING: Pyff Start batch calls the
        name of the environment pyffEVwin, however, because pyff can
        have the same environment as phdEV, you can use the same
        environment

        Note:Pyff has no setup.py, you start pyff with the main function
        FeedbackController.py - therefore you have to add pyff to your
        project folder path to work with it

    PSYCHOPY
    :   1- YOU can install psychopy in environment or standalone see
        psychopy online documentation (TODO: Still not completely
        integrated, only using some functions)

        \#TODO:
        :   You can start pyff and the bci with the same environment. So
            create a GUI batch with start buttons for each call(1.Start
            Presentation(Pyff); 2.Start Acquisition(Pycorder); 3.Start
            experiment(phdproject bci experiment)). Psychopy is more
            powerfull, but not has simple. The GUI in psychopy can be a
            good addition. Use GUI to fast create python protocols and
            save them. Add online functionality (use a decorator) by
            hierarquichal class structure(make the psychopy code the
            parent) with pylsl marker stream and online feedback. Note:
            Probably you need to commit to an independent thread or
            process to use the presentation in parallel with the
            acquisition

5- PROCESSING:
:   WYRM and MNE -Some procesing capabilities on wyrm, but MNE is more
    advanced and has support, however wyrm is needed because is the
    central api(functions for pyff connection and mushu data handling):

    \#TODO:
    :   WYRM is necessary to glue pyff and mushu in an online setting
        with some important buffers and filters. For now needs to be
        used. Try to remove necessity of wyrm during processing, only
        use pyff connection

6- ADD phdproject as an editable module to your environment
:   1-add \_\_init\_\_.py to folders that contain scripts you want to
    use as package 2-create setup.py
    (<https://stackoverflow.com/questions/6323860/sibling-package-imports/50193944#50193944>)
    - already created 3-pip install -e phdproject\_master Or use python
    setup.py develop Note: it is highly recommended to use pip install .
    (install) and pip install -e . (developer install) to install
    packages, as invoking setup.py directly will do the wrong things for
    many dependencies, such as pull prereleases and incompatible package
    versions, or make the package hard to uninstall with pip.
    (<https://stackoverflow.com/questions/19048732/python-setup-py-develop-vs-install>)
    4-if using pycnbi package, you should pip install -e path/to/pycnbi

Get the latest code
===================

Sepecific Dependencies
======================

Go to the folder requirements and see for each environment what is
needed.

There is also conda environment .yml files for easy installing.

\#NOTE: When using conda be carefull when install certain packages with
pip, sometimes they don't work, you need to install them again using
conda install (e.g.futures)

Installation Specific to OS
===========================

-   Mac OS Installation:
    :   install/update \$ xcode-select --install (command line developer
        tools) \$ brew update && brew upgrade

        Python issues: \#BUG ICLOUD ALTERS PATHS. - DONT USE OPTIMIZE
        MAC SPACE
        (e.g.:/Users/nm.costa/Desktop/testdata/CG/S030/NFT/.CG\_S030\_NFT\_ss01\_rt03\_04102018\_14h32m\_SMR\_3.eeg.icloud)

        \#BUG pygame GUI issues:
        :   Can't work in fullscreen mode

-   Windows OS Installation:
    :   1- PYTHON: Microsoft visual C++ compiler is needed:
        :   <http://aka.ms/vcpython27>

        2- PARALEL PORT: you need to install inpout32.dll to use parallel port:
        :   go to <http://www.highrez.co.uk/Downloads/InpOut32/>

        3- USING BATCH WITH ANACONDA Environments:
        :   -   To work with cmd batch you need to add persistent path enviromental variables:
                :   .Anaconda2; .Anaconda2Scripts; .Anaconda2Librarybin

        4- For Windows users, increase timer resolution (tool located in
        the src folder)

        > The default timer resolution in some Windows versions is 16
        > ms, which can limit the precision of timings. It is strongly
        > recommended to run the following tool and set the resolution
        > to 1 ms or lower:
        > [<https://vvvv.org/contribution/windows-system-timer-tool>]

Contributing
============

Mailing list
============

Licensing
=========
