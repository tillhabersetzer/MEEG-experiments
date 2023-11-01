# -*- coding: utf-8 -*-
"""
Created on Fri Oct 27 21:09:01 2023

@author: Till Habersetzer
         Carl von Ossietzky University Oldenburg
         till.habersetzer@uol.de

Identifies button presses using the ButtonListener class. The decimal DinValues
are handled in the back-end with nested functions and mapped to higher level
ButtonIDs. Basically, the ButtonIDs correspond to the pin position of the 
button in the binary sequence. For example RED is 0, which is the first pin 
in the 16-bit binary sequence 1111111111111110.
These ButtonIDs are stored along with the color of the button in a dictionary. 

Inspired by 
https://vpixx.com/vocal/psychopy/

Logged button events take the format [timetag, buttonID, eventType], e.g. [[3548.1378541, 0, 'Push']]
- timetag is the time in seconds since your VPixx hardware last booted up
- buttonID is the button that was active. 
  Below is a list of button IDs to help interpret code:  
  - "handheld" button IDs:       {0:'red',1:'yellow',2:'green',3:'blue',4:'white'}
  - "handheld - mri" button IDs: {0:'red',1:'yellow',2:'green',3:'blue'}
  - "dual - mri" button IDs:     {0:'red',1:'yellow',2:'green',3:'blue'}
  - "dual handheld" button IDs:  {0:'red',1:'yellow',2:'green',3:'blue'}
  - "mri 10 button" button IDs:  {0:'red left',1:'yellow left',2:'green left',3:'blue left',
                                  4:'white left',5:'red right',6:'yellow right',7:'green right',
                                  8:'blue right',9:'white right'}
- eventType can be either "Push" or "Release"
    
Note (30.10.23)
---- 
The suggested mapping between buttonIDs and colors can be different depending
on the connected Response device and wiring.
At the moment, the mapping at the MEG in Oldenburg differs in the following
way. 
Multiple ReponsePixx devices can be connected to the datapixx at the same time.
Therefore, the mapping above might not fit your setup.
At the MEG a Dual handheld 2-button fiber-optic Response box (dual - mri)  
and a Handheld 4-button fiber-optic Response box (handheld - mri) are connected 
simultaneously (8 out of 10 inputs are taken). The 4-button fiber-optic Response 
box takes the later input ports. 
In order to deal with all the input devices, the "mri 10 button" option needs to
be selected for the ButtonListener. 

Described case: 
"handheld - mri" button IDs: {9:'red',6:'yellow',7:'green',8:'blue'}

"""

from pypixxlib import _libdpx as dp, responsepixx as rp
from psychopy import core
import json
from psychopy.hardware import keyboard


#%% Define function that reads in button presses
#------------------------------------------------------------------------------
def read_button_presses(device = "mri 10 button"):
    """
    Returns buttonID of pressed button. 
    
    Parameters
    ----------
    device: str
    The default is "mri 10 button".
                 
    Returns
    -------
    buttonID: int

    """
     
    recordPushes = True
    recordReleases = False
    buttonSubset = None # record all buttons
    listener = rp.ButtonListener(device)
    dp.DPxUpdateRegCache()
    
    Running = True 

    while Running: 
        
        dp.DPxUpdateRegCache()
        listener.updateLogs()
        output = listener.getNewButtonActivity(buttonSubset, recordPushes, recordReleases)
         
        if output != []:
            print(output) # this prints out the timestamp of the last button push and the button that was pushed
            buttonID = output[-1][1] # index only the last button that was pushed
            # print only the last button that was pushed
            printStr = 'Button pressed! ButtonID: ' + str(buttonID) 
            print(printStr) 
            # stop loop
            Running = False
            
            return buttonID
        
        keys = kb.getKeys(['escape'])
        if 'escape' in keys:
            print('!!! Execution stopped !!!')
            Running = False
            return # implicitly returns None
        
        core.wait(0.1) 

#%% Record button dictionary
#------------------------------------------------------------------------------
kb = keyboard.Keyboard()
kb.clearEvents() # clear events

# Some settings
#--------------
# read note, mri 10 button allows to readin all input channels
device = "mri 10 button"
recordPushes = True
recordReleases = False
buttonSubset = None # omitted (defaulted to None), which specifies to use all buttons

# Create dictionary
# Define buttons that you want to check for your setup
buttons = ['green','yellow','red','blue']
button_dict = dict.fromkeys(buttons)

listener = rp.ButtonListener(device)
dp.DPxUpdateRegCache()

print('This demo will create and save a button dictionary in the current directory.')
print('The file contains a lookup table of ButtonIDs and their button labels.')
print('You will need to have a RESPONSEPixx plugged in to a VPixx device, with the device turned on.')
print('Press "esc" if you want to terminate the script.')
print('----------------------------------------------------------------------')

# Let's create a loop which checks for button presses every 0.1 seconds.
# Any time a button press is found, we print the timestamp and button pressed. 
# If a designated exit button is pressed, we disconnect
for color in buttons:
    
    print(f"\n---Press the '{color}' button---")
    # print('Press "l" if you want to log the button code.'
    
    buttonID = read_button_presses(device=device)
    
    if buttonID == None:
        break
    
    # Log button
    button_dict[color] = buttonID
    
    print(f"'{color}: {buttonID}' has been logged.")   
    
    # wait shortly before next button
    core.wait(0.1)
    
print('\nThe dictionary is complete.')
print('---------------------------')

#%% Save dictionary
#------------------------------------------------------------------------------

value = input('\nDo you want to save the button dictionary? (y/n) ')
if value == 'y':
    with open("buttonIDs.json", "w") as outfile:
        json.dump(button_dict, outfile)
else:
    pass
    
#%% Test dictionary (optional)
#------------------------------------------------------------------------------
value = input('\nDo you want to test the button dictionary? (y/n) ')

if value == 'y':
    try:
        with open("buttonIDs.json") as json_data_file:
            buttonCodes = json.load(json_data_file)
        
        # Swap values
        #------------
        buttonCodes = {value:key for key, value in buttonCodes.items()}
        
        print('\nPress "esc" if you want to terminate the script.')
        print('------------------------------------------------')
          
        Running = True
        while Running:
            buttonID = read_button_presses(device=device)
            
            if buttonID == None:
                Running = False
            else:
                buttonColor = buttonCodes[buttonID]
                print(f"Button pressed! Button Color: {buttonColor} / Button ID: {buttonID}\n")
        
    except:
        print('No button dictionary present!')
        
    finally:
        print('Script finished.')
        
else:
    print('Script finished.')
