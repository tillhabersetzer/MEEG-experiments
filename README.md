# MEEG-experiments
This repository contains different experiments for MEG and EEG. The differentitaion between MEG and EEG is based on the hardware in each lab at the Carl von Ossietzky University Oldenburg.
Depending on your hardware equipment you can ignore the division.

MEG lab:
- Elekta Neuromag® TRIUX 
- DATAPixx 3 (https://vpixx.com/products/datapixx3/)
- Costum made Triggerbox with RME Fireface UCX Soundcard (https://www.rme-audio.de/de_fireface-ucx.html)
- SoundMexPro Software (https://www.soundmexpro.de/home)

EEG lab:
- Bittium NeurOne™ Tesla EEG System (https://www.bittium.com/medical/bittium-neurone)
- Costum made Triggerbox with RME Fireface UCX Soundcard
- Brain Products TriggerBox Plus (https://www.brainproducts.com/solutions/triggerbox/)
- SoundMexPro Software (https://www.soundmexpro.de/home)

## Double Tone Auditory Oddball

Auditory Oddball experiment with a sequence of double tones. The double tones are on oboe- or clarinet-based sound with a fundamental frequency of either 100 Hz or 300 Hz.
The folder for each modality either EEG or MEG contains:
- experiment script (different versions with different hardware configurations)
- stimuli folder (contains wav-files)
- a script to check stimuli
- results folder (for experiment config files and results of experiment)
- psychopy_environment (.yml file to reproduce the environment for the experiments)

Cause there is no winner in terms which hardware to use, each experiment has been programmed with different hard configurations. 

Inspiration:
Hölle, D., Meekes, J. & Bleichner, M.G. Mobile ear-EEG to study auditory attention in everyday life. Behav Res 53, 2025–2036 (2021). https://doi.org/10.3758/s13428-021-01538-0

### EEG

- Oddball_eeg_triggerbox.py:
  This script uses a RME Fireface soundcard in combination with a costum-made Triggerbox to synchronize both audio channels and the trigger channel on the soundcard. The software for the playback is called SoundMexPro and
  requires a license.
  - RME Fireface Analogout 1/2 for audio left / right
  - SPDIF for audio trigger standard / target via costum-made Triggerbox
  - Button presses recorded via keyboard. Additionaly, SoundMexPro is used to send a trigger pulse (SPDIF)

- Oddball_brainproducts_triggerbox.py
  This script uses a RME Fireface soundcard in combination with a brain products triggerbox. The software for the playback is called SoundMexPro and requires a license.
  - RME Fireface Analogout 1/2 for audio left / right
  - Brain Products TriggerBox Plus for standard / target triggers
  - Button presses recorded via keyboard. Additionaly, Brain Products TriggerBox Plus is used to send a trigger pulse 

### MEG

In order to use the ButtonListener of the DATAPixx device the ButtonIDs must be known. They can be identified with "get_buttonIDs.py" which generates a file "buttonIDs.josn". This files contains the button colors and their corresponding ID. Using the ButtonListener and a Doutschedule for the trigger guarantees an immediate trigger pulse after a button press. 

Verions:
- Oddball_datapixx_v1.py:
  - AnalogOut 1/2 for audio left / right (DacSchedule for all 4 channels)
  - AnalogOut 3/4 for trigger standard / target
  - Dout 1 for button presses (DoutSchedule)
  
- Oddball_datapixx_v2.py:
  In comparison to version 1 all trigger are digital. DOUT schedules only control the first 16 DOUT channels (channels 0-15), leaving the upper 8 bits (channels 16-23) programmable with register writes.
  - AnalogOut 1/2 for audio left / right (DacSchedule for 2 channels)
  - Dout 16/17 for standard / target trigger (via RegisterWrites)
  - Dout 1 for Dout 1 for button presses (DoutSchedule)
  
- Oddball_soundmexpro.py:
  This script uses a RME Fireface soundcard in combination with a costum-made Triggerbox to synchronize both audio channels and the trigger channel on the soundcard. The software for the Playback is called SoundMexPro and
  requires a license.
  - RME Fireface Analogout 1/2 for audio left / right
  - SPDIF for audio trigger standard / target via costum-made Triggerbox
  - Dout 1 for button presses (DoutSchedule)
  
## Simple Auditory Evoked Fields

Within this auditory experiment click stimuli are played back. There is no visual display, response or task involved. It is designed as a passive listening task. 
The script offers the possibility to adjust the gain for each audio channel by scaling it with a factor (software). Surely, it is also possible to use amplifier hardware to change the gain for each channel.

### MEG

The experiment exists in two versions. Both of them are using a VPixx Technologies DATAPixx 3 device in different ways.

#### Versions:
##### AEF_exp_v1.py: 
Version 1
- AnalogOut 1/2/3 for audio left/right/trigger (DAC schedule with 3 channels)
  
##### AEF_exp_v2.py:
Version 2
- AnalogOut 1/2 for audio left/right (DAC schedule with 2 channels)
- Dout 1 for event trigger (Dout schedule with 1 channel)

##### Other files included
- calibration.py: Script for acoustic calibration of experiment
- click.wav: Audio file with click stimulus

### code
Analysis Code based on FieldTrip (https://www.fieldtriptoolbox.org/).
During the analysis Auditory Evoked Fields (AEFs) are computed and fitted with a two dipole model.

#### Included Scripts

##### main_settings.m
This script contains basic settings e.g. filepaths for data and fiedltrip. It is executed within the other scripts.

##### check_trigger.m
Checks trigger sequences in the recorded files.

##### headmodel.m
Computation of a headmodel (single shell headmodel Guido Nolte) for MEG. It performs coregistration between mri and MEG device and saves several processed mris (resliced, segmented, defaced).

##### volumetric_sourcemodel.m
Computation of a grid based volumetric sourcemodel. The sourcemodel can be restricted with an anatomical Atlas (e.g. only STG regions). The source model is also inverse warped onto a subject-specific anatomical mri.

##### compute_erfs.m
Computation of Auditory Evoked Fields.

##### plot_erf.m
Visualization of Auditory Evoked Fields.

###### compute_dipolfit.m
Computation of a two dipole fit based on AEFs. First, the dipolfits are computed with a symmetry constraint which is released in a second step for a nonlinear optimization.

##### plot_dipolfit.m
Visualization of the fitted dipoles, in space and in time.






