# -*- coding: utf-8 -*-
"""
Created on Mon Nov 27 20:00:21 2023

@author: Till Habersetzer
         Carl von Ossietzky University Oldenburg
         till.habersetzer@uol.de
         
Rapid double tone auditory Oddball paradigm (~ 5min 30sec)
-------------------------------------------------------------------------------
- Two different double tones used: an oboe-based sound with a fundamental 
  frequency of 100 Hz and a clarinet-based sound with a fundamental frequency 
  of 300 Hz.The first tone had a duration of 700 ms (including 5-ms rise and fall time) 
  and was followed after a silent period of 100 ms by the second tone with 
  identical pitch but a duration of 500 ms (including 5-ms rise and fall time).
- One of the double tones served as target, the other as standard.
- Each run consisted of 160 trials (double tones), 112 standards (70%) and 48 
  targets (30%)
- The first four trials were always standards
- The order of the remaining trials was randomized with no more than two 
  targets in succession.
- Only targets required a response by the participant.
- inter-trial interval (offset of previous double tone to onset of next double tone) 
  randomly varied between 500 ms and 900 ms (minimal standard random number generator as implemented in Presentation)
  resulting in an average of nine targets per minute
  (0.7+0.1+0.5)+0.75 = 2.05 s per tone
  60/2.05 * 0.3 = 30*0.3 = 9 targets per minute
  
Check out:
Hölle, D., Meekes, J. & Bleichner, M.G. Mobile ear-EEG to study auditory 
attention in everyday life. Behav Res 53, 2025–2036 (2021).
https://doi.org/10.3758/s13428-021-01538-0
https://rdcu.be/dlAje

v2 -- version 2: Analog Audio, Digital trigger for Button Presses and Audio Events 
  
Hardware / Software details
-------------------------------------------------------------------------------
- Python + PsychoPy
Audio
-----
- DATAPixx AnalogOut 1 (left)
- DATAPixx AnalogOut 2 (right)

Trigger
-------
All triggers are digital (buttons + audio events - see Specifics)
- DOUT schedules only control the first 16 DOUT channels (channels 0-15)
- Upper 8 bits (channels 16-23) programmable with register writes
- DATAPixxDout 16 (Standard)
- DATAPixxDout 17 (Target)

Button Presses
--------------
- Recorded with VPixx ResponsePixx / MRI response box via ButtonListener. 
- Button presses automatically send a digital trigger due to ButtonScheduler.
  (Requires Datapixx device and corresponding software package for python) 
        
Wiring
------
In use: 
- 2 analog channels 
  - 2 BNCs for audio to headphone amplifier
- 2 digital channels
  - 2 BNCs for audio triggers
    - Standard: BNC (Dout17) to MEG Trigger Interface (STI001) 
    - Target: BNC (Dout18) to MEG Trigger Interface (STI002)
- Connect VPixx Dout 1 (Dout Value is set to 1) to STI003 in MEG Trigger Interface
  (sum channel STI101: 4)
  
Specifics
---------
It is not possible to use multiple DoutSchedules at the same time. This is a 
hardware limitation of the DATAPixx device. Therefore, the ButtonSchedule, 
generating a trigger when a button is pressed, is blocking other DoutSchedules 
for the entirety of the experiment.
Therefore, riggers for the audio signals cant be send through the digital ports 
via DoutSchedule.
In order to make it work the DoutSchedules for buttons and audio triggers have 
to be used one at a time in an interleaved fashion.
As a workaround, the audiotriggers are send as an analog signal with the digital
to analog converter. Unfortunately, the DATAPixx3 offers only 4 channels.
Two of the analog channels are blocked for the audio (left/rigth) and the other 
two for the triggers. 
Each analog channel must be connected individually to the corresponding channel
in the MEG Stimulus Trigger Interface.
Due to that it is possible to only encode to different triggers, one for the
standard and one for a deviant. That is why, both tones within a double tone 
trial have the same trigger value. 

BUT it is still possible to avoid using analog triggers and using up to 8 bits 
for digital triggers.
As a workaround the following solution is recommended: 
DOUT schedules only control the first 16 DOUT channels (channels 0-15), leaving 
the upper 8 bits (channels 16-23) programmable with register writes.
Actually, it is possible to run the schedule for sending triggers corresponding 
to button presses (on channels 0-15), and potentially send a separate trigger 
at the same time as the sound by using DPxSetDoutValue (from one of the 
channels 16-23).
"""

#%% Import packages
#------------------------------------------------------------------------------

from pypixxlib import _libdpx as dp
from pypixxlib import responsepixx as rp
import soundfile as sf
import datetime
import numpy as np
import os.path as op
import os
import matplotlib.pyplot as plt
import json
import sys

from psychopy import core, visual
from psychopy.gui import DlgFromDict
from psychopy.hardware import keyboard

#%% Settings
#------------------------------------------------------------------------------

# Plot Audio signals
plot_signals = False
# Show window in fullscreen mode
fullscrMode = False
# Show information for current trial
trialinfo = True

# Experiment info gui
#--------------------
expInfo = {'sub':'01', 'run':'1','Target tone': ['clarinet','oboe']}
expInfo['date'] = str(datetime.datetime.now())
expInfo['Plot signals'] = str(plot_signals)
expInfo['Fullscreen Mode'] = str(fullscrMode)
expInfo['Show trial info'] = str(trialinfo)

# present a dialogue to change params
dlg = DlgFromDict(expInfo, 
                  title='Double Tone Auditory Oddball',
                  fixed=['date','Plot signals','Fullscreen Mode','Show trial info'], 
                  order = ['date','sub','run','Target tone','Plot signals','Fullscreen Mode','Show trial info'],
                  )
if dlg.OK:
    print(expInfo)
else:
    print('User Cancelled')
    core.quit()  # the user hit cancel so exit

# Get subject
subject = 'sub-' + str(expInfo['sub'])
# Get run 
run = 'run-' + str(expInfo['run'])
# Get target
target = str(expInfo['Target tone'])

print('\nSubject: ' + str(subject))
print('Run: ' + str(run))

# select run for labelling of saved cfg-file
run = 1
# select target tones
target = 'clarinet'
# target = 'oboe'

NumTrials = 160
NumStandards = int(NumTrials * 0.7)
NumTargets = int(NumTrials * 0.3)
GapSize = 0.1 # 100 ms
jitter_interval = [0.5, 0.9] # sec
TrigLen = 0.1 # 100 ms

# Trigger Values
#---------------
event_values = {
    'button': 1, # EventValue for DoutSchedule (means first Dout pin)
    'standard': 2**16, # bitmask: '10000000000000000' channel 16 (0,1,...15,16)
    'target':2**17, # bitmask: '100000000000000000' channel 17 
    }

# Set up DinValues
#-----------------
button_mapping = {
    'blue': 3, # needs to be known, depends on wiring (run get_buttonIDs.py)
    }
buttonSubset = [button_mapping['blue']]
buttonDevice = 'mri 10 button'
recordPushes = True
recordReleases = False

# Channel mapping for AnalogOut
#------------------------------
# 4 anlalog channels in use: 0,1,2,3
# 0,1: audio left / right
channel = [1,2]

kb = keyboard.Keyboard()
kb.clearEvents() # clear events

#%% Setup window and initialize components
#------------------------------------------------------------------------------
    
# Setup the Window 
win = visual.Window(
    fullscr=fullscrMode, 
    screen = 2,
    winType='pyglet', 
    monitor='testMonitor',
    color=[0,0,0], # default grey
    colorSpace='rgb',
    units='height',
    checkTiming=False 
    )

# Show fixation cross
# Initialize components for Routine "Stimulus"
textStimulusCross = visual.TextStim(win=win, name='textStimulusCross',
    text='+',
    font='Open Sans',
    pos=(0, 0), 
    height=0.15, 
    wrapWidth=None, 
    ori=0.0, 
    color='white', 
    colorSpace='rgb', 
    opacity=None, 
    languageStyle='LTR',
    depth=-1.0)

# stimulus is automatically drawn every frame
textStimulusCross.autoDraw = True

# Initialize components for Routine "Stimulus"
textStimulusTrial = visual.TextStim(win=win, name='textStimulusTrial',
    text='',
    font='Open Sans',
    pos=(0, -0.1), 
    height=0.03, 
    wrapWidth=None,
    ori=0.0, 
    color='white', 
    colorSpace='rgb', 
    opacity=None, 
    languageStyle='LTR',
    depth=-1.0)

textStimulusTrial.autoDraw = True

win.flip()

#%% Welcome Message
#------------------------------------------------------------------------------
    
print('\nDouble Tone Auditory Oddball Experiment')
print('---------------------------------------')
print('\nPress "Escape" for emergency stop during experiment.')
print('Press "SPACE" to start experiment.')

not_pressed = True

while not_pressed:
    keys = kb.getKeys(['space','escape'])
    # Emergency stop
    if 'escape' in keys:
        print('\n!!!Experiment stopped!!!')
        sys.exit()
    elif 'space' in keys:
        not_pressed = False
        pass
     
    core.wait(0.01)

#%% Build double tones and triggers
#------------------------------------------------------------------------------

if target == 'clarinet':
    sig_target1, fs = sf.read(op.join('stimuli','clarinet_new.wav'))
    sig_target2, fs = sf.read(op.join('stimuli','clarinet_new_short.wav'))
    
    sig_standard1, fs = sf.read(op.join('stimuli','oboe_new.wav'))
    sig_standard2, fs = sf.read(op.join('stimuli','oboe_new_short.wav'))

elif target == 'oboe':
    sig_target1, fs = sf.read(op.join('stimuli','oboe_new.wav'))
    sig_target2, fs = sf.read(op.join('stimuli','oboe_new_short.wav'))
    
    sig_standard1, fs = sf.read(op.join('stimuli','clarinet_new.wav'))
    sig_standard2, fs = sf.read(op.join('stimuli','clarinet_new_short.wav')) 
    
# In case of stereo signals, take the first column
gap =  np.zeros(int(GapSize*fs))
sig_target = np.concatenate((sig_target1[:,1], gap, sig_target2[:,1]))
sig_standard = np.concatenate((sig_standard1[:,1], gap, sig_standard2[:,1]))
 
if plot_signals:
    plt.figure()
    plt.subplot(2, 1, 1)
    plt.plot(sig_target)
    plt.title('target: ' + target)
    plt.subplot(2, 1, 2)
    plt.plot(sig_standard)
    plt.title('standard')
    
#%% Generate playlist and Jitter
#------------------------------------------------------------------------------
# Initialize random number generator
rng = np.random.default_rng(seed=None)

# playmatrix is a matrix containing 0s and 1s defining standard and target trials
# standard: 0
# targets 1
trialtypes = {'standard': 0,
              'target': 1}

playmatrix = np.concatenate((trialtypes['standard']*np.ones(NumStandards,dtype=int),
                             trialtypes['target']*np.ones(NumTargets,dtype=int)))
# Here you could impose some special rules on the permutation!
# 1: The first four trials are always standards
# 2: No more than two targets in succession

# Update playmatrix as long as imposed conditions are not fullfilled
update_playmatrix = True
while update_playmatrix:
    
    condition1 = ~(playmatrix[0:4] == trialtypes['standard']*np.ones(4,dtype=int)).all()
    # trialtypes['target'] > 0 so that convolution operation works
    condition2 = (3*trialtypes['target'] in np.convolve(playmatrix,np.ones(3,dtype=int),'full'))
        
    if (condition1 or condition2):
        playmatrix = rng.permutation(playmatrix)
    else:    
        update_playmatrix = False
 
# triallabel 
#-----------
triallabel = ['standard' if n==trialtypes['standard'] else 'target' for n in playmatrix]

# Jitter
#-------
jitterlist = jitter_interval[0] + (jitter_interval[1]-jitter_interval[0])*rng.uniform(low=0.0, high=1.0, size=NumTrials)
jitterlist = jitterlist.round(decimals=3) # round to ms precision

#%%  Establishing a connection to VPixx hardware 
#------------------------------------------------------------------------------
dp.DPxOpen()
isReady = dp.DPxIsReady()
if not isReady:
    raise ConnectionError('VPixx Hardware not detected! Check your connection and try again.')
                
#%% Setting up Button Schedules and Analog Schedule
#------------------------------------------------------------------------------
# https://vpixx.com/vocal/psychopy/
# https://www.vpixx.com/manuals/psychtoolbox/html/DigitalIODemo3.html

# Enable debounce. When a DIN transitions, ignore further DIN transitions for 
# next 30 milliseconds (good for response buttons and other mechanical inputs)
dp.DPxEnableDinDebounce()
#Set our mode. The mode can be:
#  0 -- The schedules starts on a raising edge (press of RPx /MRI, release of RPx)
dp.DPxSetDoutButtonSchedulesMode(0)

baseAddressButton = int(9e6)
ButtonScheduleOnset = 0.0 # no delay
ButtonScheduleRate = 6 # waveform playback rate 6 samples/sec

# Due to 6 Hz sampling frequency and 3 samples duration, the trigger signal is
# 0.5s long
DoutValue = event_values['button']
blueSignal = [DoutValue, 0, 0] # single pulse 
blueAddress =  baseAddressButton + 4096*button_mapping['blue']
dp.DPxWriteDoutBuffer(blueSignal, blueAddress)

signalLength = len(blueSignal)

# Implements a digital output schedule in a DATAPixx
dp.DPxSetDoutSchedule(ButtonScheduleOnset, ButtonScheduleRate, signalLength+1, baseAddressButton)
# Enables automatic DOUT schedules upon DIN button presses
dp.DPxEnableDoutButtonSchedules()
dp.DPxWriteRegCache()

print('Automatic button schedule is running.\n')
listener = rp.ButtonListener(buttonDevice) 
dp.DPxWriteRegCache()

# Remark signalLength + 1
# Since the last value of the waveform gets replaced by the default value almost 
# instantly, your device reading the Digital In signal might not be triggered 
# by it. A possible fix is to specify to the Digital Out schedule an extra frame.

# Analog schedules
#-----------------
AnalogbufferAddress = int(0)
        
#%% Audio + Trigger
#------------------------------------------------------------------------------

reaction_times = []
flag = False # breakout / emergency stop

for trial, trialtype in enumerate(playmatrix):
      
    # emergency stop
    if flag:
        break
    
    # Standard
    #---------
    if trialtype == trialtypes['standard']:
        audio = sig_standard
        trigVal = event_values['standard']
        print('\nStandard trial')
        print('--------------')
        
    # Target
    #-------
    elif trialtype == trialtypes['target']:
        audio = sig_target
        trigVal = event_values['target']
        print('\nTarget trial')
        print('------------')

    if trialinfo:
        textStimulusTrial.setText('\n' + str(trial+1) + ' / ' + str(NumTrials) 
        + '\nTrial type: ' + triallabel[trial])
        win.flip()
        
    # Reset for detecting button presses
    no_response = True
    # Reset audio trigger
    no_trigger = True
        
    # Load data (audio + trigger) onto analog channels
    #--------------------------------------------------------------------------
    # nChans x nFrame list where each row of the matrix contains the sample data 
    # for one DAC channel. Each column of the list contains one sample for each DAC channel.
    analog_signal = np.stack((audio,audio),axis=0)
    
    numBufferFrames = len(audio)
    maxScheduleFrames = numBufferFrames
    StimDur = numBufferFrames / fs
    dp.DPxWriteDacBuffer(bufferData = analog_signal, 
                         bufferAddress = AnalogbufferAddress, 
                         channelList = channel)
    dp.DPxWriteRegCache()
    
    # Start playback
    #--------------------------------------------------------------------------
    dp.DPxSetDacSchedule(onSet = 0, # Onset delay
                         rateValue = fs, # sampling rate
                         rateUnits = "Hz", # rateUnits (str) – This can have three values: “Hz” for samples/seconds, “video” for samples/video frame or “nano” for seconds/samples
                         maxScheduleFrames = maxScheduleFrames, 
                         channelList = channel, # If provided, it needs to be a list of size nChans.
                         bufferBaseAddress = AnalogbufferAddress, 
                         numBufferFrames = numBufferFrames)
    dp.DPxStartDacSched() 
    
    # Turn on trigger channels  
    dp.DPxSetDoutValue(bit_value = trigVal, # turn on specific trigger channel
                       bit_mask = 16777215) # '111111111111111111111111' enable all 24 pins
    
    dp.DPxUpdateRegCache() # Read and Write (initiating sound and trigger at the same time)
    startTime = dp.DPxGetTime()
    passedTime = 0
    
    TrialDur = StimDur + jitterlist[trial] 
    while passedTime < (TrialDur): # check passed time  
        dp.DPxUpdateRegCache()
        currentTime = dp.DPxGetTime()     
        passedTime = currentTime - startTime
        
        keys = kb.getKeys(['escape'])
        # Emergency stop
        if 'escape' in keys:
            print('\n!!!Experiment stopped!!!')
            flag = True
            break
        
        # Turn off trigger channels 
        if passedTime > 0.1 and no_trigger: # after 100 ms
            dp.DPxSetDoutValue(bit_value = 0, # turn off all channels
                               bit_mask = 16777215) # '111111111111111111111111' enable all 24 pins
            no_trigger = False
        
        if (no_response):
            listener.updateLogs()
            output = listener.getNewButtonActivity(buttonSubset, recordPushes, recordReleases)
            
            # Check only for target trials
            if (trialtype == trialtypes['target']):
                
                if output != []:
                    # this prints out the timestamp of the last button push and the button that was pushed
                    print(f"Button presses! {output}")
                    timestamp = output[-1][0]
                    button = output[-1][1] # index only the last button that was pushed
                    
                    # Append reaction time
                    reactionTime = timestamp - startTime
                    reaction_times.append(reactionTime)
                    print(f"Reaction time: {reactionTime} s.")
                   
                    # Check pressed button
                    no_response = False # leave if-condition
                    
                    # trialinfo is updated when button is pressed
                    if trialinfo:
                        textStimulusTrial.setText('\n' + str(trial+1) + ' / ' + str(NumTrials) 
                        + '\nTrial type: ' + triallabel[trial]
                        + '\nReaction time: ' + str(round(reactionTime,3)) + " s")
                        win.flip()
                        
        # wait 1 ms before refresh?!
        core.wait(0.001) 
        
    # in case no button has been pressed (no reaction)
    if trialtype == trialtypes['target'] and no_response:
        reactionTime = float('inf')
        reaction_times.append(reactionTime)
        print('No Button pressed')
        print(f"Reaction time: {reactionTime} s.")
        
    print(f"Trial {trial+1} of {NumTrials} played.\n")

print('Audio playback finished.')

#%% Save experiment configuration
#------------------------------------------------------------------------------
results_cfg = {
       'playmatrix': playmatrix.tolist(),
       'triallabel': triallabel,
       'jitterlist': jitterlist.tolist(),
       'reaction times': reaction_times,
       }

## Path to save data
#-------------------
dir2save = op.join('results')
cfg_results_fname = subject + "task-oddball_" + str(run) + "_cfg_results.json"
if not os.path.exists(dir2save):
   os.makedirs(dir2save)
   
with open(op.join(dir2save,cfg_results_fname), "w") as outfile:
    json.dump(results_cfg, outfile) 

#%% Closing the connection to hardware
#------------------------------------------------------------------------------
core.wait(2) 
dp.DPxStopAllScheds()
dp.DPxWriteRegCache() 
dp.DPxClose() 

win.close()
