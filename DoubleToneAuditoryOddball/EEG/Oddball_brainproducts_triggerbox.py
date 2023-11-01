# -*- coding: utf-8 -*-
"""
Created on Wed Nov  1 13:00:17 2023

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
- Trigger are send via Brainproducts Triggerbox

Button Presses
--------------
- Recorded via keyboard. Additionaly, Brainproducts triggerbox is used to send 
  a trigger pulse
        
Wiring
------
In use: 
- Two analog audio channels (see code for exact channels)
- Audio triggers: 1,2 Button press: 4 
- Laptop is connected to Brainproducts triggerbox which is connected to eeg
  main station. comPort needs to be specified for the trigegrbox.
- No Additional wiring for button repsonse. Keyboard is used. 

# Specifics
#-----------
Due to soundplayback via SoundMexPro and usage of brainproducts triggerbox,
only the start of each double tone is triggered. Therefore, two instead of four
event values are in use.

"""

#%% Import packages
#------------------------------------------------------------------------------

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

# Triggerbox
import serial
import time
import threading

#%% Brainproducts Triggerbox 
#------------------------------------------------------------------------------

Connected = True
PulseWidth = 0.01 # 100 ms
comPort = "COM6" # needs to be specified
def ReadThread(port):
    while Connected:
        if port.inWaiting() > 0:
            print ("0x%X"%ord(port.read(1)))

# Open the Windows device manager, search for the "TriggerBox VirtualSerial Port (COM6)"
# in "Ports (COM & LPT)" and enter the COM port number in the constructor.
port = serial.Serial(comPort)
# Start the read thread
thread = threading.Thread(target=ReadThread, args=(port,))
thread.start()
# Set the port to an initial state
port.write([0x00])
time.sleep(PulseWidth)

#%% Settings
#------------------------------------------------------------------------------

# Plot Audio signals
plot_signals = True
# Show loaded audiotracks with SoundMexPro
ShowAudioTracks = True
# Show window in fullscreen mode
fullscrMode = False
# Show information for current trial
trialinfo = True
# Current Soundcard
# SetSoundcard = 'Fireface' 
SetSoundcard = 'Fireface' 

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

event_values = {
    'target': 0x01,  
    'standard': 0x02, 
    'button': 0x04, 
    }

# Set directory for SoundMexPro
bin_dir = r'C:\SoundMexPro\bin'

if SetSoundcard=='Focusrite':
    driver = 'Focusrite USB ASIO'
if SetSoundcard == 'Fireface':
    driver = 'ASIO Fireface USB'

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
print('Press "SPACE" when a target tone occurs.')
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

#%% Build double tones and Triggers
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
    'output': [0,1],
    'input': -1, # if -1 is specified, no input channels are used
    'track': 2,
    }
soundmexpro('init', smp_cfg)  

# Mapping of tracks
#------------------
smp_cfg = {
    'track': [0, 1], # left, right
    }
soundmexpro('trackmap', smp_cfg)

# Naming
#-------
smp_cfg = {
    'track': [0, 1],
    'name': ['audio left','audio right'],
    }
soundmexpro('trackname', smp_cfg)

smp_cfg = {
    'output': [0, 1],
    'name': ['audio left','audio right','trigger'],
    }
soundmexpro('channelname', smp_cfg)

# show visualization
#-------------------
if ShowAudioTracks:
    soundmexpro('show')
    soundmexpro('showtracks')        
    
print('Hardware initialized: SoundMexPro')

#%% Experiment: Audio + Trigger + Keyboard
#------------------------------------------------------------------------------

trialClock = core.Clock()
reaction_times = []
flag = False # breakout / emergency stop

for trial, trialtype in enumerate(playmatrix):
      
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
        
    # Load data onto analog channels
    #--------------------------------------------------------------------------
    # Concatenate data into matrix
    analog_signal = np.stack((audio,audio),axis=1)
    
    # IMPORTANT NOTE: reading waves to memory with python creates interleaved data in memory, bit_length
    # soundmexpro needs non-interleaved data: so force rearranging in memory!!
    analog_signal = np.asfortranarray(analog_signal)  
    
    StimDur = len(audio) / fs
    
    # Reset times
    #------------
    kb.clock.reset()  # timer (re)starts
    trialClock.reset()
   
    # Load data into memory and start playback
    #-----------------------------------------
    smp_cfg = {
        'data': analog_signal,
        'track': [0, 1],                         
        'loopcount': 1,  
        'name': 'audio + trigger',                    
        }
    soundmexpro('loadmem', smp_cfg)
    
    # Start playback and send trigger (time-aligned)
    smp_cfg = {
        'length' : -1, # device is stopped (playback and record) after all tracks played their data.
        }
    soundmexpro('start', smp_cfg)
    
    # Send trigger
    #-------------
    port.write([trigVal])
    time.sleep(PulseWidth)
    # Reset Bit 0, Pin 2 of the Output(to Amp) connector
    port.write([0x00])
    time.sleep(PulseWidth)
    
    if ShowAudioTracks:
        soundmexpro('updatetracks') 
        
    TrialDur = StimDur + jitterlist[trial]
    while trialClock.getTime() < TrialDur:  
        
        # Check only for deviants
        if (trialtype == trialtypes['target']):
              
                if 'space' in keys:
                    print('Button pressed')
                    # reaction time - only look at first key
                    reactionTime = keys[0].rt
                    reaction_times.append(reactionTime)
                    print(f"Reaction time: {round(reactionTime,3)} s.") # ms precision
                    
                    # Check pressed button
                    no_response = False # leave if-condition
            
                    # trialinfo is updated when button is pressed
                    if trialinfo:
                        textStimulusTrial.setText('\n' + str(trial+1) + ' / ' + str(NumTrials) 
                        + '\nTrial type: ' + triallabel[trial]
                        + '\nReaction time: ' + str(round(reactionTime,3)) + " s")
                        win.flip()
                        
                    # Send trigger
                    port.write([event_values['button']])
                    time.sleep(PulseWidth)
                    # Reset Bit 0, Pin 2 of the Output(to Amp) connector
                    port.write([0x00])
                    time.sleep(PulseWidth)
            
        # wait 1 ms before refresh?!
        core.wait(0.001)
            
    if trialtype == trialtypes['target'] and no_response:
        reactionTime = float('inf')
        reaction_times.append(reactionTime)
        print('No Button pressed')
        print(f"Reaction time: {reactionTime} s.")
        
    print(f"Trial {trial+1} of {NumTrials} played.")
        
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
# Terminate the read thread
Connected = False
thread.join(1.0)
# Close the serial port
port.close()

soundmexpro('exit')
win.close()

