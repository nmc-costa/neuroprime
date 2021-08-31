This Program was kindly provided by Brain Products GmBH (written by Norbert Hauser) with minor modifications.
To use this program, you need to own the BrainVision recorder, and enable Remote Data Access (RDA). This program connects to the BrainVision Recorder and links the signal to the lab streaming layer.

# Usage
  * Start the BrainVisionRDA app. You should see a window like the following.
> > ![brainvisionrda.png](brainvisionrda.png)

  * Make sure that your BrainVision recorder is started, and that remote data access (RDA) is enabled in the settings/preferences (see manual).

  * If your BrainVision recorder is running on the same machine as this program, there is no need to change the RDA Server Address -- otherwise you need to enter the IP address of the respective machine.

  * Click the "Link" button. If all goes well you should now have a stream on your lab network that has name "BrainVision RDA" and type "EEG", and another stream called "BrainVision RDA Markers" of type "Markers" which holds even markers. Note that you cannot close the app while it is linked.

  * For subsequent uses you can save the settings in the GUI via File / Save Configuration. If the app is frequently used with different settings you might can also make a shortcut on the desktop that points to the app and appends to the Target field the snippet `-c name_of_config.cfg`
