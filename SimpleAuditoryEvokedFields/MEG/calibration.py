# -*- coding: utf-8 -*-
"""
Created on Mon Nov 27 15:50:39 2023

@author: Till Habersetzer
         Carl von Ossietzky University Oldenburg
         till.habersetzer@uol.de
         
Click stimulus is a transient. Therefore, it is recommended to measure the peak 
instead of rms level and use a hold on mechanic.
         
Procedure (fast)
----------------
- Use if both headphones should be calibrated to the same level and the desired 
  level doesn't need to be precise (e.g. comfortable level)
- Adjust both headphones to same level:
   1. Playback click stimulus via headphones at comfortable level. If necessary 
      use attenuation (gaindB) to adjust the level.
      Measure peak-to-peak voltage with oscilloscope. Note down digital level of
      stimulus in dB (dBStim).
   2. Note down measured level L with sound level meter and calculate 
      calibration values CalVal =  L - dBStim
      
         
Procedure (Peak-to-peak-equivalent sound pressure level measurement)
--------------------------------------------------------------------
- Use if a definded SPL level is required
- Requires oscilloscope!
	1. Playback click stimulus via headphones at comfortable level. If necessary 
     use attenuation (gaindB) to adjust the level.
     Measure peak-to-peak voltage with oscilloscope. Note down digital level of
     stimulus in dB (dBStim).
  2. Play back sinusoidal tone (1000 Hz) and adjust gain until it fits same 
     peak-to-peak voltage on oscilloscope. 
  3. Check level L on sound level meter. The stimulus level is L dB peSPL.
  4. Note down measured level L and calculate calibration values CalVal
	  CalVal =  L - dBStim

ToDo:
    - Check how to stop the function
    
Recommended Calibration Equipment for Insert Earphones
------------------------------------------------------
B&K Type 4157 Ear Simulator
B&K External Ear Simulator DB2012 with sercure cap
B&K 2250 Sound Level Meter/Analyzer
B&K ZC-0032 microphone preamplifier 
B&K Type 4231 Sound Calibrator 

Last calibration (30.12.23)
---------------------------
# Use LCpeak?! (The C-weighted Peak measurement)

# Left -10 dB Fs -> 86.4 dB(C): CalVal = 96.4 dB

# Right -10 dB Ds -> 86.2 dB(C): CalVal = 96.2 dB

CalVal = [96.4, 96.2] dB
    
"""

#%% Import packages
#------------------------------------------------------------------------------
from pypixxlib import _libdpx as dp
import soundfile as sf
import numpy as np
import os.path as op
from psychopy import core
from psychopy.hardware import keyboard

#%% Function defintion
#------------------------------------------------------------------------------
def play_calsig(channel=0, gaindB = -10):
    """
    Playback of calibration signal (click) with infinite loop. The click signal 
    is looped using an ISI of 1s.
    
    channel: 0: AnalogOut 0 - left 
             1: AnalogOut 1 - right
    gaindB: channel gain in dB
            >0: amplification
            <0: attenuation
    """
    
    print("Please not down calibration equipment!")
    # Settings
    #--------------------------------------------------------------------------
    audiofile = 'click.wav'
    jitter_interval = 1 # sec
    
    kb = keyboard.Keyboard()
    kb.clearEvents() # clear events

    #  Establishing a connection to VPixx hardware 
    #---------------------------------------------
    dp.DPxOpen()
    isReady = dp.DPxIsReady()
    if not isReady:
        raise ConnectionError('VPixx Hardware not detected! Check your connection and try again.')

    # Load Click signal
    #--------------------------------------------------------------------------
    click, fs = sf.read(op.join(audiofile))
    Nsamples = round(fs*jitter_interval)

    # Extend to 1 s length
    click = np.hstack((click,np.zeros(Nsamples-len(click))))
    # Compute level in dB FS 
    level = 20*np.log10(max(click)) 
    print(f"Initial stimulus level: {level} dB FS")
    print(f"Stimulus Level changed by {gaindB} dB.")

    # Apply Gain
    #-----------
    Click = 10**(gaindB/20)*click
    level = 20*np.log10(max(Click))
    print(f"Adjusted stimulus level: dBStim: {level} dB FS.")
    print("\nNote down meausered stimulus level on Sound Level Meter (SLM) when comfortable level is reached.")
    print("Calibration Value (CalVal) is: Measuered level on SLM - Adjusted level dBStim")
    
    # Start Playback
    #--------------------------------------------------------------------------
    
    # Writes the data that will be used by the DAC buffer to drive the analogue outputs
    #----------------------------------------------------------------------------------
    dp.DPxWriteDacBuffer(bufferData = Click,
                         bufferAddress = int(0),
                         channelList = channel)
    dp.DPxWriteRegCache()
    
    # Configure a schedule for autonomous DAC analog signal acquisition
    #------------------------------------------------------------------
    dp.DPxSetDacSchedule(scheduleOnset = 0, 
                         scheduleRate = fs, 
                         rateUnits = "Hz", 
                         maxScheduleFrames = 0, # loops back
                         channelList = channel, # If provided, it needs to be a list of size nChans.
                         bufferBaseAddress= int(0), 
                         numBufferFrames = Nsamples)
    dp.DPxStartDacSched()  
    dp.DPxWriteRegCache()
    
    not_pressed = True

    while not_pressed:
        keys = kb.getKeys(['space','escape'])
        # Emergency stop
        if 'escape' in keys:
            print('\n!!!Experiment stopped!!!')
            not_pressed = False
            # sys.exit()
        core.wait(0.01) 

    print('Audio playback finished.')

    # Closing the connection to hardware
    #--------------------------------------------------------------------------
    dp.DPxStopAllScheds()
    dp.DPxWriteRegCache() 
    dp.DPxClose() 
    
#%% Calibration
#------------------------------------------------------------------------------
play_calsig(channel=[0], gaindB = -10)
