# -*- coding: utf-8 -*-
"""
Till Habersetzer, 11.12.2023
Communication Acoustics, CvO University Oldenburg
till.habersetzer@uol.de 

Application of Maxwell filtering
https://mne.tools/dev/auto_tutorials/preprocessing/60_maxwell_filtering_sss.html

- Loop over all subjects
- Loop over all runs
- bad channel detection before Maxwell filtering 
- changing parameter st switches between SSS and tSSS (default)
- a MNE report is creating showing PSD before and after Maxwell filter for each 
  file
  
Optional:
---------
- Application of oversampled temporal projection (otp) (takes too long...)
  Denoising algorithm                                                        
  https://mne.tools/stable/auto_examples/preprocessing/otp.html
- Computation and correction of head movements
  https://mne.tools/dev/auto_tutorials/preprocessing/59_head_positions.html
- Transformation to common head positions between runs. That means same
  head-dev-trafo for all runs
"""

#%% Settings
import os
import os.path as op
import mne
from mne.preprocessing import find_bad_channels_maxwell

subjects  = ['sub-01','sub-02','sub-03']
# subjects  = ['sub-01']
fnames = ['aef_run-1',
          'aef_run-2',
          'emptyroom']
          
# path to project (needs to be adjusted)
rootpath = op.join('C:',os.sep,'Users','tillhabersetzer','Nextcloud','Synchronisation','Projekte','GitHub','MEEG-experiments','SimpleAuditoryEvokedFields')

# Load crosstalk compensation and fine calibration files
crosstalk_file = os.path.join(rootpath,'derivatives','SSS', 'ct_sparse.fif')
fine_cal_file = os.path.join(rootpath,'derivatives','SSS', 'sss_cal.dat')

# Apply Oversampled Temporal Projection to reduce sensor noise before MaxFilter
OTP = 0
         
# Apply Headposition Transformation 
HPT = 1
ref_fname = 'aef_run-1'

# Apply and compute movement correction
MC = 0

#%% Headposition computations for movement correction

if MC: 
    for subject in subjects:
        
        figs_list= []
        captions_list = []
        dir2save =  os.path.join(rootpath,'derivatives',subject,'maxfilter')

        # use reduced set for head movement computations
        fnames_reduced = [fname for fname in fnames if 'aef' in fname]
        for fname in fnames_reduced:
            
            raw_fname = os.path.join(rootpath,'rawdata',subject,'meg',subject + '_task-' + fname + '.fif')
            headpos_fname = os.path.join(rootpath,'derivatives',subject,'maxfilter',subject + '_task-' + fname + '_head_pos_raw.pos')
            
            # Head positions are computed if raw meg file exists and positions
            # havent been computed yet
            if op.isfile(raw_fname) and not op.isfile(headpos_fname):
                
                raw = mne.io.read_raw_fif(raw_fname, allow_maxshield=False, verbose=True)
            
                #%% Compute head position
                chpi_amplitudes = mne.chpi.compute_chpi_amplitudes(raw)
                chpi_locs = mne.chpi.compute_chpi_locs(raw.info, chpi_amplitudes)
                head_pos = mne.chpi.compute_head_pos(raw.info, chpi_locs, verbose=True)
                
                if head_pos.shape[0]>0: # cHPI active
                
                    #%% Save head position     
                    if not op.exists(dir2save):
                        os.makedirs(dir2save)
                        print("Directory '{}' created".format(dir2save))
        
                    mne.chpi.write_head_pos(headpos_fname, head_pos)
                    
                    captions_list.append(fname)
                    figs_list.append(mne.viz.plot_head_positions(head_pos, mode='traces',show=False))
        
        # add to report if list is not empty
        if figs_list:
            #%% Add plots of the data to the HTML report
            report_fname = op.join(dir2save,subject+'-report.hdf5')
            report_html_fname = op.join(dir2save,subject+'-report.html')
            
            with mne.open_report(report_fname) as report:
                report.add_figure(
                figs_list,
                title='Extracting and visualizing subject head movement',
                caption=captions_list,
                replace=True
                )
            report.save(report_html_fname, overwrite=True,open_browser=False)  

#%% maxfilter processing

for subject in subjects:
    
    figs_list_before = []
    figs_list_after = []
    captions_list = []
    dir2save = os.path.join(rootpath,'derivatives',subject,'maxfilter')
    
    for fname in fnames:
        
        #%% Load data
        raw_fname = os.path.join(rootpath,'rawdata',subject,'meg',subject + '_task-' + fname + '.fif')
    
        if op.isfile(raw_fname):
            
            raw = mne.io.read_raw_fif(raw_fname, allow_maxshield=False, verbose=True)
        
            #%% Oversampled temporal projection
            if OTP:
                raw = mne.preprocessing.oversampled_temporal_projection(raw)
            
            #%% emptyroom 
            if 'empty' in fname:      
                destination = None
                head_pos = None
                st_duration = None
                coord_frame = "meg"
                    
            #%% recordings with subjects inside meg
            else:
                st_duration = 10
                coord_frame = 'head'
                
                #%% Head Position Transformation
                if HPT: 
                    # Use headposition of a recording as reference
                    destination = os.path.join(rootpath,'rawdata',subject,'meg',subject + '_task-'+ ref_fname + '.fif')
                else:
                    destination = None
                    
                #%% Movement Correction  
                if MC: 
                    headpos_fname = os.path.join(rootpath,'derivatives',subject,'maxfilter',subject + '_task-' + fname + '_head_pos_raw.pos')
                    if op.isfile(headpos_fname):
                        head_pos = headpos_fname    
                else:
                    head_pos = None       
                
            #%% Detect bad channels
            raw.info['bads'] = []
            raw_check = raw.copy()
            auto_noisy_chs, auto_flat_chs = find_bad_channels_maxwell(
                raw_check, cross_talk=crosstalk_file, calibration=fine_cal_file,
                coord_frame=coord_frame, return_scores=False, verbose=True)
            print(auto_noisy_chs)  
            print(auto_flat_chs)  
            
            # Update list of bad channels
            bads = raw.info['bads'] + auto_noisy_chs + auto_flat_chs
            raw.info['bads'] = bads
            
            #%% Apply MaxFilter
            raw_tsss = mne.preprocessing.maxwell_filter(
                raw, cross_talk=crosstalk_file, calibration=fine_cal_file, 
                st_duration=st_duration, head_pos=head_pos, destination=destination, coord_frame=coord_frame, verbose=True)
                
            #%% Save data
            if not op.exists(dir2save):
                os.makedirs(dir2save)
                print("Directory '{}' created".format(dir2save))
                
            raw_tsss.save(os.path.join(dir2save,subject + '_task-' + fname + '-raw_tsss.fif'),overwrite=True)

            #%% Add a plot of the data to the HTML report
            # report_fname = op.join(dir2save,subject+'-report.hdf5')
            # report_html_fname = op.join(dir2save,subject+'-report.html')
            # with mne.open_report(report_fname) as report:
            #     report.add_raw(raw=raw, title=f'Raw data before maxwell filter : {task}', psd=True, replace=True)
            #     report.add_raw(raw=raw_tsss, title=f'Raw data after maxwell filter: {task}', psd=True, replace=True)
            #     report.save(report_html_fname, overwrite=True,open_browser=False)
                
            figs_list_before.append(raw.compute_psd().plot(show=False, xscale='log'))
            figs_list_after.append(raw_tsss.compute_psd().plot(show=False, xscale='log'))
            captions_list.append(fname)
        
    #%% Append plots to report
    report_fname = op.join(dir2save,subject + '-report.hdf5')
    report_html_fname = op.join(dir2save,subject + '-report.html')
    with mne.open_report(report_fname) as report:
        report.add_figure(
        figs_list_before,
        title='PSD before maxwell filtering',
        caption=captions_list,
        replace=True
        )
        report.add_figure(
        figs_list_after,
        title='PSD after maxwell filtering',
        caption=captions_list,
        replace=True
        )
    report.save(report_html_fname, overwrite=True,open_browser=False)  