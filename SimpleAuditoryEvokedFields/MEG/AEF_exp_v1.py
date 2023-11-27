# -*- coding: utf-8 -*-
"""
Created on Mon Nov 27 13:33:38 2023

@author: Till Habersetzer
         Carl von Ossietzky University Oldenburg
         till.habersetzer@uol.de
         
Auditory Evoked Fields experiment (N100m) 
-----------------------------------------
- Playback of simple clicks with NumTrials repititions. The ISI is jittered 
  between [1, 1.2] s.
- duration ~ N_samples * mean(jitterlist) ~ 400*1.1 s = 440 s = 7.33 min
- No settings are saved
- No visual component included
- Use calibration.py to measure / calculate Calibration Values (CalVal)

Hardware / Software details
-------------------------------------------------------------------------------
- DATAPixx + Python + PsychoPy

Audio
-----
- DATAPixx AnalogOut 1 (left)
- DATAPixx AnalogOut 2 (right)

Trigger
-------
- DATAPixx AnalogOut 3

Wiring
------
In use: 
- 3 analog channels 
  - 2 BNCs for audio to headphone amplifier
  - 1 BNC for audio triggers
    BNC (Analog3) to MEG Trigger Interface (STI001) 
    Wiring defines the event value for the MEG      
    
ToDo:
    - Check if DPxWriteDacBuffer needs to be executed once before the loop or
      every loop
    - Check Calibration
"""

#%% Import packages
#------------------------------------------------------------------------------
from pypixxlib import _libdpx as dp
import soundfile as sf
import numpy as np
import os.path as op
from psychopy import core
from psychopy.hardware import keyboard
import matplotlib.pyplot as plt
import sys

#%% Settings
#------------------------------------------------------------------------------

# Plot Click
plot_click = False

# Audio signal
NumTrials = 20
audiofile = 'click.wav'
jitter_interval = [1, 1.2] # sec
TrigLen = 0.1 # 100 ms

# Define calibration values
#--------------------------
# Gain is applied so so that targetlevel is reached
TargetLevel = 85 # dB (dB Peak SPL, dB -p peSPL, depends on the calibration method)
CalVal = [114,114] # Result of calibration

# Channel mapping for AnalogOut
#------------------------------
# 0,1: audio left / right
# 2: trigger click
channel = [0,1,2]

#  Establishing a connection to VPixx hardware 
#---------------------------------------------
dp.DPxOpen()
isReady = dp.DPxIsReady()
if not isReady:
    raise ConnectionError('VPixx Hardware not detected! Check your connection and try again.')

#%% Load Click signal
#------------------------------------------------------------------------------
click, fs = sf.read(op.join(audiofile))
Nsamples = round(fs*0.5)
dBStim = 20*np.log10(max(click)) 

# Extend to 500 ms length
click = np.hstack((click,np.zeros(Nsamples-len(click))))

# trigger
#--------
trigger = np.zeros(Nsamples)
# set 100 ms to 5V
trigger[0:round(round(0.1*fs))] = 5
    
# Jitter
#-------
# Initialize random number generator
rng = np.random.default_rng(seed=None)

jitterlist = jitter_interval[0] + (jitter_interval[1]-jitter_interval[0])*rng.uniform(low=0.0, high=1.0, size=NumTrials)
jitterlist = jitterlist.round(decimals=3) # round to ms precision   
  
if plot_click:
    timevec = np.linspace(0, Nsamples/fs-1/fs, Nsamples)*1000
    plt.figure()
    plt.subplot(2, 1, 1)
    plt.plot(timevec, click, label='Click')
    plt.plot(timevec, trigger, label = 'Trigger')
    plt.legend(loc="upper right")
    plt.title('Analog Signals')
    plt.xlabel('t / ms')
    plt.subplot(2, 1, 2)
    plt.hist(jitterlist, label = 'Jitter')
    plt.legend(loc="upper right")
    plt.xlabel('t / s')
    
# Calibration of signals
#-----------------------
# gaindB + dBStim + CalVal = TargetLevel
gaindB = TargetLevel - dBStim - CalVal

gain = [1,1]
gain[0] = 10.**(gaindB[0]/20)
gain[1] = 10.**(gaindB[0]/20)

click_left = gain[0] * click
click_right = gain[1] * click

# Stack audio and trigger (left, right, trigger)
#-----------------------------------------------
# nChans x nFrame list where each row of the matrix contains the sample data 
# for one DAC channel. Each column of the list contains one sample for each DAC channel.
audio_data = np.stack((click_left,click_right,trigger),axis=0)    

#%% Welcome Message
#------------------------------------------------------------------------------
kb = keyboard.Keyboard()
kb.clearEvents() # clear events
  
print('\nAuditory Evoked Fields Experiment')
print('---------------------------------')
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
    
#%% Start Playback
#------------------------------------------------------------------------------
    
# Writes the data that will be used by the DAC buffer to drive the analogue outputs
#----------------------------------------------------------------------------------
dp.DPxWriteDacBuffer(bufferData = audio_data,
                     bufferAddress = int(0),
                     channelList = channel)
dp.DPxWriteRegCache()

# Loop over Trials
#-----------------
for trial in range(0,NumTrials):
    
    # Configure a schedule for autonomous DAC analog signal acquisition
    #------------------------------------------------------------------
    dp.DPxSetDacSchedule(scheduleOnset = 0, 
                         scheduleRate = fs, 
                         rateUnits = "Hz", 
                         maxScheduleFrames = Nsamples, 
                         channelList = channel, # If provided, it needs to be a list of size nChans.
                         bufferBaseAddress= int(0), 
                         numBufferFrames = Nsamples)
    dp.DPxStartDacSched()  
    dp.DPxUpdateRegCache() # Read and Write
    startTime = dp.DPxGetTime()
    passedTime = 0
    
    # Wait until trial has finished 
    #------------------------------
    while passedTime < jitterlist[trial]:
        
        dp.DPxUpdateRegCache()
        currentTime = dp.DPxGetTime()     
        passedTime = currentTime - startTime
        
        keys = kb.getKeys(['space','escape'])
        # Emergency stop
        if 'escape' in keys:
            print('\n!!!Experiment stopped!!!')
            sys.exit()
            
        # wait 1 ms before refresh?!
        core.wait(0.001) 
    
    print(f"Trial {trial+1} of {NumTrials} played.")

print('Audio playback finished.')

#%% Closing the connection to hardware
#------------------------------------------------------------------------------
dp.DPxStopAllScheds()
dp.DPxWriteRegCache() 
dp.DPxClose() 