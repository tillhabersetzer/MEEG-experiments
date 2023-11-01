# -*- coding: utf-8 -*-
"""
Created on Thu Oct 26 16:25:32 2023

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
  
Hardware / Software details
-------------------------------------------------------------------------------
- Windows + Python + PsychoPy
Audio
-----
- RME Fireface Soundcard
- Playback via SoundMexPro (requires Windows)
- Trigger value is enconded in Amplitude of SPDIF signal and decoded into TTL 
- pulses via costum-made Triggerbox (University Oldenburg)
Button Presses
--------------
- Recorded with VPixx ResponsePixx / MRI response box via ButtonListener. 
- Button presses automatically send a digital trigger due to Button Scheduler.
  (Requires Datapixx device and corresponding software package for python) 
        
Wiring
------
In use: 
- Two analog audio channels + SPDIF channel (see code for exact channels)
- Audio triggers: 1,2,4,8 (STI001, STI002, STI003, STI004 blocked)
- Connect VPixx Dout 1 (Dout Value is set to 1) to STI005 in MEG Trigger Interface
  (sum channel STI101: 16)
   
Specifics
---------
Audio triggers from soundcard/triggerbox and button press triggers from response
box are both send to the MEG Trigger interface.
In order to make it work, trigger channel used by the button press must be switched
off in the Triggerbox cable connected to the MEG Trigger Interface. Therefore, 
the corresponding switch on the cable connector must be switched off. 

Optimization
------------
- Start soundmexpro with each trial so that the playback starts with the reaction
  time measurement
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

#%% TriggerBox - TriggerScaling
#------------------------------------------------------------------------------

def calculate_trig_word(TrigID, BitRef):
    """
    Computes the trigger amplitude for the SPDIF signal
    BitRef is 16 for MEG
    8 for EEG (NeurOne System)
    TrigID is the integer value in the sum channel
    """
    # removes prefix “0b”
    bitmask = bin(TrigID).replace("0b", "")
    # Extend Bitmask to BitRef bits
    bitmask = (BitRef - len(bitmask)) * '0' + bitmask
    # Convert to numpy array
    bitmask = np.array([int(bit) for bit in bitmask], dtype=np.uint8)
    powers_of_2 = np.power(2, np.arange(BitRef))
    TrigWord = np.dot(powers_of_2, bitmask) / 2**BitRef

    return TrigWord

#%% Settings
#------------------------------------------------------------------------------

# Plot Audio signals
plot_signals = False
# Show loaded audiotracks with SoundMexPro
ShowAudioTracks = True
# Show window in fullscreen mode
fullscrMode = False
# Show information for current trial
trialinfo = True
# Current Soundcard
# SetSoundcard = 'Fireface' 
SetSoundcard = 'Focusrite' 

# Experiment info gui
#--------------------
expInfo = {'sub':'01', 'run':'1','Target tone': ['clarinet','oboe']}
expInfo['date'] = str(datetime.datetime.now())
expInfo['Plot signals'] = str(plot_signals)
expInfo['Fullscreen Mode'] = str(fullscrMode)
expInfo['Selected Soundcard'] = SetSoundcard
expInfo['Show Audio Tracks'] = str(ShowAudioTracks)
expInfo['Show trial info'] = str(trialinfo)

# present a dialogue to change params
dlg = DlgFromDict(expInfo, 
                  title='Double Tone Auditory Oddball',
                  fixed=['date','Plot signals','Fullscreen Mode','Selected Soundcard','Show Audio Tracks','Show trial info'], 
                  order = ['date','sub','run','Target tone','Plot signals','Fullscreen Mode','Selected Soundcard','Show Audio Tracks','Show trial info'],
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

NumTrials = 160
NumStandards = int(NumTrials * 0.7)
NumTargets = int(NumTrials * 0.3)
GapSize = 0.1 # 100 ms
jitter_interval = [0.5, 0.9] # sec
TrigLen = 0.1 # 100 ms

event_values = {
    'target': [1,2], # MEG Triggerbox value
    'standard': [4,8], # MEG Triggerbox value
    'button': 1, # EventValue for DoutSchedule (means first Dout pin)
    }

# Set up DinValues
#-----------------
button_mapping = {
    'blue': 3, # needs to be known, depends in wiring
    }
buttonSubset = [button_mapping['blue']]
buttonDevice = 'mri 10 button'
recordPushes = True
recordReleases = False

# Set directory for SoundMexPro
bin_dir = r'C:\SoundMexPro\bin'

if SetSoundcard=='Focusrite':
    driver = 'Focusrite USB ASIO'
    output = [0, 1, 2]
if SetSoundcard == 'Fireface':
    driver = 'ASIO Fireface USB'
    output = [0, 1, 8]
    
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

# Trigger for doubles tones
#--------------------------
TrigLen_samp = int(TrigLen*fs)

a = np.zeros(len(sig_target1))
a[0:TrigLen_samp] = calculate_trig_word(event_values['target'][0], 16)
b = np.zeros(len(sig_target2))
b[0:TrigLen_samp] = calculate_trig_word(event_values['target'][1], 16)
trigger_target = np.concatenate((a,gap,b))

c = np.zeros(len(sig_standard1))
c[0:TrigLen_samp] = calculate_trig_word(event_values['standard'][0], 16)
d = np.zeros(len(sig_standard2))
d[0:TrigLen_samp] = calculate_trig_word(event_values['standard'][1], 16)
trigger_standard = np.concatenate((c,gap,d))
    
if plot_signals:
    plt.figure()
    plt.subplot(2, 1, 1)
    plt.plot(sig_target)
    plt.plot(trigger_target)
    plt.title('target: ' + target)
    plt.subplot(2, 1, 2)
    plt.plot(sig_standard)
    plt.plot(trigger_standard)
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
    
#%% Setting up Button Schedules and ButtonListener
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

#%% Initialize SoundMexPro
#------------------------------------------------------------------------------
## SoundMexPro
#-------------
sys.path.append(bin_dir)
# import soundmexpro
from soundmexpro import soundmexpro

smp_cfg = {
    'force': 1, # if set to 1, 'exit' is called internally before init
    'autocleardata': 1, # If parameter is set to 1 (default is 0), all audio data segments that were already played completely are freed from memory on every 'loadfile' or 'loadmem' command
    'driver': driver,
    'samplerate': fs,
    'output': output,
    'input': -1, # if -1 is specified, no input channels are used
    'track': 3,
    }
soundmexpro('init', smp_cfg)  

# Mapping of tracks
#------------------
smp_cfg = {
    'track': [0, 1, 2], # left, right, trigger
    }
soundmexpro('trackmap', smp_cfg)

# Naming
#-------
smp_cfg = {
    'track': [0, 1, 0, 1, 2],
    'name': ['audio left','audio right','trigger'],
    }
soundmexpro('trackname', smp_cfg)

smp_cfg = {
    'output': [0, 1, 2],
    'name': ['audio left','audio right','trigger'],
    }
soundmexpro('channelname', smp_cfg)

# show visualization
#-------------------
if ShowAudioTracks:
    soundmexpro('show')
    soundmexpro('showtracks')        
        
# start device in 'play-zeros-if-no-data-in-tracks'-mode
smp_cfg = {
    'length' : 0, # device is never stopped, zeros are played endlessly.
    }
soundmexpro('start', smp_cfg)
    
print('Hardware initialized and started: SoundMexPro + Datapixx3')

#%% Playback Audio + Trigger
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
        trigger = trigger_standard
        print('\nStandard trial')
        print('--------------')
        
    # Target
    #-------
    elif trialtype == trialtypes['target']:
        audio = sig_target
        trigger = trigger_target
        print('\nTarget trial')
        print('------------')
        
    if trialinfo:
        textStimulusTrial.setText('\n' + str(trial+1) + ' / ' + str(NumTrials) 
        + '\nTrial type: ' + triallabel[trial])
        win.flip()
        
    # Reset for detecting button presses
    no_response = True
        
    # Load data onto analog channels
    #--------------------------------------------------------------------------
    # Concatenate data into matrix
    analog_signal = np.stack((audio,audio,trigger),axis=1)
    
    # IMPORTANT NOTE: reading waves to memory with python creates interleaved data in memory
    # soundmexpro needs non-interleaved data: so force rearranging in memory!!
    analog_signal = np.asfortranarray(analog_signal)  
    
    StimDur = len(audio) / fs
   
    # Load data into memory
    #----------------------
    smp_cfg = {
        'data': analog_signal,
        'track': [0, 1, 2],                         
        'loopcount': 1,  
        'name': 'audio + trigger',                    
        }
    soundmexpro('loadmem', smp_cfg)
    
    if ShowAudioTracks:
        soundmexpro('updatetracks') 
    
    dp.DPxUpdateRegCache()
    startTime = dp.DPxGetTime() # start time of Trial
    passedTime = 0
    
    TrialDur = StimDur + jitterlist[trial] 
    while passedTime < TrialDur: # check passed time
        dp.DPxUpdateRegCache()
        currentTime = dp.DPxGetTime()     
        passedTime = currentTime - startTime
        
        keys = kb.getKeys(['escape'])
        # Emergency stop
        if 'escape' in keys:
            print('\n!!!Experiment stopped!!!')
            flag = True
            soundmexpro('exit')
            break
        
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

print('\nAudio playback finished.')

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

soundmexpro('exit')
win.close()
