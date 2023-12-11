%--------------------------------------------------------------------------
% Till Habersetzer, 01.12.2023
% Communication Acoustics, CvO University Oldenburg
% till.habersetzer@uol.de
%
% Computation of auditory evoked fields (AEFs)
% The data has been recorded in two runs. The AEFs are computed for each
% run and on the combined runs. 
% There was no task during the experiment. The subject (passively) listened
% to N=400 Click stimuli per run.
%
% Computation of event related fields over subjects (1,2,...) and 
% conditions {'Run-1','Run-2','combined'}
%
% Pipeline
%---------
% Loop over subects 
% For each subject the recordings of each run are
% - filtered, epoched, baseline corrected and a semi-automatic artifact 
%   rejection based on z-value can be applied separately on gradiometers 
%   and magnetometers separately on combined runs
% - as a 3rd conditions all runs (1,2) are combined 
% - averages over all conditions are computed
%--------------------------------------------------------------------------

close all
clear 
clc 

%% Script settings
%--------------------------------------------------------------------------
eval('main_settings')

% select subjects
subjects = [1,2,3];

% runs
runs = [1,2];
R    = length(runs);

% Trigger IDs
TrigID = 1;

% epoch length 
interval       = [-0.25,0.75];  
baselinewindow = [-0.25,0]; 
% filter settings
filter_freqs = [1,45]; % (highpass, lowpass)

% Semi automatic rejection of artifacts
artifact_rejection = true;

% Use SSP 
use_ssp = false;

% Use maxfiltered files
use_maxfilter = true;

% Check frequency spectrum
check_spectrum = false;

% reference file for headposition that was used during coregistration
%--------------------------------------------------------------------
% run 2 has been used
run_ref = settings.ref_run_dev2head;

%% Compute single subject Event Related Fields (ERFs)
%--------------------------------------------------------------------------

for subidx=subjects % loop over subjects

    subject = ['sub-',num2str(subidx,'%02d')];

    % directory for data storing
    dir2save = fullfile(settings.path2project,'derivatives',subject);

    epochs = cell(1,R+1); % 1 x (NumRuns + combined)

    % Append data over all runs
    for ridx = 1:R

        % current run number
        run = runs(ridx);

        % difrectory for rawdata
        if use_maxfilter
            rawdata_path = fullfile(settings.path2project,'derivatives',subject,'maxfilter');
            datapath = fullfile(rawdata_path,[subject,'_task-aef_run-',num2str(run),'-raw_tsss.fif']);
            % remove bad channels in case maxfilter wasnt used. Maxfilter
            % repairs noisy channels so that they can be reused.
            badchannels = {};
        else
            rawdata_path = fullfile(settings.path2project,'rawdata',subject);
            datapath     = fullfile(rawdata_path,'meg',[subject,'_task-aef_run-',num2str(run),'.fif']);
            badchannels  = settings.badchannels; 
        end

        % Filter continuous data to avoid edge artifacts
        %-----------------------------------------------

        % lowpass
        %--------
        cfg              = [];
        cfg.channel      = [{'meg'},badchannels]; 
        cfg.continuous   = 'yes';
        cfg.coilaccuracy = 0; % SI units
        cfg.lpfilter     = 'yes';
        cfg.lpfreq       = filter_freqs(2);
        cfg.dataset      = datapath;
        data             = ft_preprocessing(cfg); 
        
        % highpass
        %---------
        cfg              = [];
        cfg.channel      = 'meg'; 
        cfg.continuous   = 'yes';
        cfg.coilaccuracy = 0; % SI units
        cfg.hpfilter     = 'yes';
        cfg.hpfreq       = filter_freqs(1);
        data             = ft_preprocessing(cfg,data); 

        % notch filter for train (16.7 Hz) - Avoid this - use maxfilter
        %---------------------------------
        % cfg              = [];
        % cfg.channel      = 'meg'; 
        % cfg.continuous   = 'yes';
        % cfg.coilaccuracy = 0; % SI units
        % % cfg.dftfilter    = 'yes';% does not work (only 50 Hz...)
        % % cfg.dftfreq      = 16.7;
        % % cfg.dftreplace   = 'zero'; % 'zero' implies DFT filter
        % cfg.bsfilter     = 'yes';
        % cfg.bsfreq       = [16, 17]; 
        % data             = ft_preprocessing(cfg,data); 


        % Check spectrum
        %------------------------------------------------------------------
        if check_spectrum

            % Databrowser
            %--------------------------------------------------------------
            cfg           = [];
            cfg.blocksize = 10;
            cfg.viewmode  = 'vertical';
            cfg.channel   = 'megmag';
            ft_databrowser(cfg,data)
         

            % Computation
            %--------------------------------------------------------------
            cfg          = [];
            cfg.length   = 10; % the data is cutted in trials of 10s length
            cfg.overlap  = 0.5; % there is no overlap between trials
            data_epoched = ft_redefinetrial(cfg, data);
            
            cfg        = [];
            cfg.output = 'pow';
            cfg.method = 'mtmfft'; 
            cfg.taper  = 'hanning'; 
            cfg.foilim = [0,300]; 
            spectrum   = ft_freqanalysis(cfg, data_epoched);

            cfg                = [];
            cfg.channel        = 'megmag';
            spectrum_megmag    = ft_selectdata(cfg,spectrum);
            cfg.channel        = 'megplanar';
            spectrum_megplanar = ft_selectdata(cfg,spectrum);

            % Plot spectrum - butterfly plot
            %-------------------------------
            axs = cell(1,2);
            figure
            for i=1:2
                if i==1
                    channels = 'megmag';
                else
                    channels = 'megplanar';
                end

                cfg                = [];
                cfg.channel        = channels;
                spectrum_selection = ft_selectdata(cfg,spectrum);

                axs{i} = subplot(2,1,i);
                loglog(spectrum_selection.freq,spectrum_selection.powspctrm,'Color',[0.5 0.5 0.5 0.2]);
                xlabel('Frequency (Hz)');
                ylabel('log(absolute power)');
                xlim([0,200])
                title(channels)
                grid on
            end
            linkaxes([axs{:}],"x")
            sgtitle('Spectrum','interpreter','none')

            % Magnetometers
            %--------------
            cfg            = [];
            cfg.showlabels = 'yes'; % show channel labels
            cfg.fontsize   = 6;
            cfg.layout     = 'neuromag306mag.lay';
            cfg.xlim       = [0,200];
            ft_multiplotER(cfg, spectrum);
            sgtitle([subject,': Magnetometers'])
            
            % Gradiometers
            %-------------
            cfg            = [];
            cfg.showlabels = 'yes'; 
            cfg.fontsize   = 6;
            cfg.layout     = 'neuromag306planar.lay'; 
            cfg.xlim       = [0,200];
            ft_multiplotER(cfg, spectrum);
            sgtitle([subject,': Gradiometers'])
            clear data_epoched spectrum

        end
        %------------------------------------------------------------------

        % Apply SSP
        %------------------------------------------------------------------
        if use_ssp
            cfg            = [];
            cfg.ssp        = 'all';
            cfg.trials     = 'all';
            cfg.updatesens = 'yes';
            data           = ft_denoise_ssp(cfg, data);
        end

        % Define trials
        %------------------------------------------------------------------
        cfg                     = [];
        cfg.dataset             = datapath;
        cfg.trialfun            = 'ft_trialfun_general'; 
        cfg.trialdef.eventtype  = 'STI101';
        cfg.trialdef.eventvalue = TrigID;
        cfg.trialdef.prestim    = -interval(1);             
        cfg.trialdef.poststim   = interval(2);                
        cfg                     = ft_definetrial(cfg);
        trl                     = cfg.trl;

        % Check number of trials
        %-----------------------
        if length(trl)~=400
            error('!!!Unexpected number of trials!!!')
        end
 
        % Epoch data
        %-----------
        cfg          = [];
        cfg.trl      = trl;  
        epochs{ridx} = ft_redefinetrial(cfg,data); 

        % Get reference grad structure for correct sensor positions
        %----------------------------------------------------------
        if run == run_ref
            grad = data.grad;
        end

        % Apply baseline correction
        %--------------------------
        cfg                = [];
        cfg.demean         = 'yes';
        cfg.baselinewindow = baselinewindow;
        epochs{ridx}       = ft_preprocessing(cfg,epochs{ridx});
        clear data 

        if artifact_rejection
            % Semi automatic artifact rejection on combined runs
            %------------------------------------------------------------------
            % separately for gradiometers
            cfg             = [];
            cfg.metric      = 'zvalue';
            cfg.channel     = 'megplanar';
            cfg.keepchannel = 'yes';  % This keeps those channels that are not displayed in the data
            epochs{ridx}    = ft_rejectvisual(cfg,epochs{ridx});
            
            % separately for magnetometers
            cfg.channel     = 'megmag';
            epochs{ridx}    = ft_rejectvisual(cfg,epochs{ridx});
        end 

    end

    % Combine epochs
    %----------------------------------------------------------------------
    cfg                = [];
    cfg.keepsampleinfo ='no';
    epochs{ridx+1}     = ft_appenddata(cfg, epochs{1:2}); 
    
    % It is crucial to select the gradiometer information from the
    % reference fif-file that was used during coregistration for source
    % modelling
    epochs{ridx+1}.grad = grad; % add lost information
    clear grad

    % Compute Average
    %----------------------------------------------------------------------
    % conditions: Run-1, Run-2, Combined
    N_trials = zeros(1,3); % number of trials per condition
    avgs     = cell(1,3);
    
    for cidx = 1:3 % loop over conditions
        
        % Note down amount of preserved epochs
        %-------------------------------------
        N_trials(cidx) = length(epochs{cidx}.trial);

        % Timelockanalysis
        %-----------------
        cfg        = [];
        avgs{cidx} = ft_timelockanalysis(cfg, epochs{cidx});

    end

    clear epochs 

    % Compute noise covariances (for sphering if all mags and grads are
    % used together during dipolefitting) - Does not work at the moment!!!
    %----------------------------------------------------------------------

    if use_maxfilter
        rawdata_path = fullfile(settings.path2project,'derivatives',subject,'maxfilter');
        datapath     = fullfile(rawdata_path,[subject,'_task-emptyroom-raw_tsss.fif']);
        badchannels  = {};
    else
        rawdata_path = fullfile(settings.path2project,'rawdata',subject);
        datapath     = fullfile(rawdata_path,'meg',[subject,'_task-emptyroom.fif']);
        badchannels  = settings.badchannels;
    end

    % lowpass
    %--------
    cfg              = [];
    cfg.channel      = [{'meg'},badchannels]; 
    cfg.continuous   = 'yes';
    cfg.coilaccuracy = 0; % SI units
    cfg.lpfilter     = 'yes';
    cfg.lpfreq       = filter_freqs(2);
    cfg.dataset      = datapath;
    noise            = ft_preprocessing(cfg); 
    
    % highpass
    %---------
    cfg              = [];
    cfg.channel      = 'meg'; 
    cfg.continuous   = 'yes';
    cfg.coilaccuracy = 0; % SI units
    cfg.hpfilter     = 'yes';
    cfg.hpfreq       = filter_freqs(1);
    cfg.dataset      = datapath;
    noise            = ft_preprocessing(cfg,noise); 

    % Apply SSP
    %----------
    if use_ssp
        cfg            = [];
        cfg.ssp        = 'all';
        cfg.trials     = 'all';
        cfg.updatesens = 'yes';
        noise          = ft_denoise_ssp(cfg, noise);
    end

    % Noise Covariance
    %-----------------
    cfg                  = [];
    cfg.removemean       = 'yes'; % default for covariance computation
    cfg.covariance       = 'yes';
    cfg.covariancewindow = 'all';
    avg_noise            = ft_timelockanalysis(cfg,noise);

    % imagesc(avg_noise.cov)

    %----------------------------------------------------------------------

    % Save data
    %----------------------------------------------------------------------
    results.conditions    = {'Run-1','Run-2','Combined'};
    results.avgs          = avgs;
    results.trialinfo     = N_trials;
    results.use_maxfilter = use_maxfilter; % maxfilter status
    cfg.use_ssp           = use_ssp; % ssp status
    results.avg_noise     = avg_noise; % contains noise covariance matrix

    save(fullfile(dir2save,[subject,'_erfs.mat']),'-struct','results'); % in mm

    clear avgs results
end
