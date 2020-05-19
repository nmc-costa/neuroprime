# NeuroPrime
A framework for real-time HCI/BCI. Specifically developed for advanced human-computer assisted self-regulation of Neurofeedback.

The software will be available as soon as it is published (in the upcoming months).

Simplicity and reusability are the foundation of NeuroPrime package, as is intended to be an open source project to be used by the neuroscience community. It is also intended to be a BCI hub that evolves with a synthesis of the best packages the python community has to offer in terms of signal processing, signal presentation and signal acquisition. Therefore, it should provide an easy and simple structure to update and connect new packages within the same design.

## Basic layout
![](neuroprime_diagram.png)

Neuroprime was built on Python open source language, synthesizing while using the best parts, we extensively tested, from specific BCI and EEG modules, for signal acquisition, signal processing/classification and signal presentation (diagram above). Signal Acquisition: pycorder (Brain Products, Gilching, Germany), pylsl/lab streaming layer (SCCN, 2014), and mushu (Venthur & Blankertz, 2012). Signal processing/classification: wyrm (Venthur & Blankertz, 2014) and mne (Gramfort et al., 2013). Signal presentation: pyff (Venthur et al., 2010) and psychopy (Peirce, 2007). Additionally, some other important packages, pandas for managing data, matplotlib for graphs, numpy for arrays, scipy for specific algorithms, pygatt for bluethooth connectivity with GSR and HR sensors, and also pyqtgraph for real-time graphical interfaces (Jones, Oliphant, & Peterson, 2001; Mckinney, 2010; Oliphant, 2006). 
