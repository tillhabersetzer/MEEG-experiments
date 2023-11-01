# -*- coding: utf-8 -*-
"""
Created on Thu Sep  7 19:13:39 2023

@author: tillhabersetzer
"""

 # -*- coding: utf-8 -*-
"""
Created on Mon Jul 24 17:55:01 2023

@author: tillhabersetzer
"""

import numpy as np
import matplotlib.pyplot as plt
import soundfile as sf
import os.path as op

clarinet, fs1 = sf.read(op.join('stimuli','clarinet_new.wav'))
clarinet_short, fs2 = sf.read(op.join('stimuli','clarinet_new_short.wav'))
L1 = len(clarinet)/fs1
L2 = len(clarinet_short)/fs2

oboe, fs3 = sf.read(op.join('stimuli','oboe_new.wav'))
oboe_short, fs4 = sf.read(op.join('stimuli','oboe_new_short.wav'))
L3 = len(oboe)/fs3
L4 = len(oboe_short)/fs4

plt.figure()
plt.subplot(2, 1, 1)
plt.plot(clarinet)
plt.subplot(2, 1, 2)
plt.plot(clarinet_short)
plt.title('clarinet')

plt.figure()
plt.subplot(2, 1, 1)
plt.plot(oboe)
plt.subplot(2, 1, 2)
plt.plot(oboe_short)
plt.title('oboe')

# check rms values 

# levels
#-------
db_clarinet = 20 * np.log10(np.sqrt(np.mean(clarinet ** 2)))
db_clarinet_short = 20 * np.log10(np.sqrt(np.mean(clarinet_short ** 2)))
db_oboe = 20 * np.log10(np.sqrt(np.mean(oboe ** 2)))
db_oboe_short = 20 * np.log10(np.sqrt(np.mean(oboe_short ** 2)))


# Visualize Stimuli
#------------------

target = 'clarinet'

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
GapSize = 0.1
gap =  np.zeros(int(GapSize*fs))
sig_target = np.concatenate((sig_target1[:,1], gap, sig_target2[:,1]))
sig_standard = np.concatenate((sig_standard1[:,1], gap, sig_standard2[:,1]))

timevec_target = np.arange(0, len(sig_target))*1000/fs
timevec_standard = np.arange(0, len(sig_standard))*1000/fs

plt.figure()
plt.subplot(2, 1, 1)
plt.plot(timevec_standard,sig_standard)
plt.subplot(2, 1, 2)
plt.plot(timevec_target,sig_target)








