%--------------------------------------------------------------------------
% Till Habersetzer, 01.12.2023
% Communication Acoustics, CvO University Oldenburg
% till.habersetzer@uol.de
%
% Plot sensorlevel results for different conditions
% - single subject
% The conditions needs to be selected as a cell array
% conditions = {'Run-1','Run-1','Combined'};
%
% Check out: https://www.fieldtriptoolbox.org/tutorial/eventrelatedaveraging/
%--------------------------------------------------------------------------

close all
clear all
clc

%% Single subject or grand average data
%--------------------------------------------------------------------------
eval('main_settings')

% Select subject
%---------------
subidx  = 3;
subject = ['sub-',num2str(subidx,'%02d')];

dir2load = fullfile(settings.path2project,'derivatives',subject);

% conditions to plot
%-------------------
% conditions = {'Combined'};
% conditions = {'Run-1','Run-2'};
conditions = {'Run-1','Run-2','Combined'};
C          = length(conditions);

% Import data
%--------------------------------------------------------------------------
data           = load(fullfile(dir2load,[subject,'_erfs.mat']));
avgs           = data.avgs;
conditions_all = data.conditions;

if isfield(data,'trialinfo')
    N_trials = data.trialinfo;
end
clear data
fprintf('\nData from %s loaded.',subject)

% Take subselection of conditions for plotting
%--------------------------------------------------------------------------
idx = contains(conditions_all, conditions);
% Check whether conditions are included in loaded data
% Select subset of conditions
% - only pitch / loudness, not pooled
if sum(idx)~=C
    error('!!!Wrong number of selected conditions!!!')
end
avgs       = avgs(idx);
conditions = conditions_all(idx);

% Visualize data
%--------------------------------------------------------------------------

% The planar gradient magnitudes over both directions at each sensor can 
% also be combined into a single positive-valued number
avgs_cmb    = cell(size(avgs));
for cidx = 1:C
    cfg            = [];
    cfg.method     = 'sum';
    avgs_cmb{cidx} = ft_combineplanar(cfg,avgs{cidx});
end

% xlimits = [-0.1, 2];
xlimits = 'maxmin';

% Magnetometers
%--------------
cfg            = [];
cfg.showlabels = 'yes'; % show channel labels
cfg.fontsize   = 6;
cfg.layout     = 'neuromag306mag.lay';
cfg.xlim       = xlimits;
ft_multiplotER(cfg, avgs{:});
sgtitle([subject,': Magnetometers'])

% Gradiometers
%-------------
cfg            = [];
cfg.showlabels = 'yes'; 
cfg.fontsize   = 6;
cfg.layout     = 'neuromag306planar.lay'; 
cfg.xlim       = xlimits;
ft_multiplotER(cfg, avgs{:});
sgtitle([subject,': Gradiometers'])

% Combined Gradiometers
%----------------------
cfg            = [];
cfg.showlabels = 'yes'; 
cfg.fontsize   = 6;
cfg.layout     = 'neuromag306cmb.lay'; 
cfg.xlim       = xlimits;
ft_multiplotER(cfg, avgs_cmb{:});
sgtitle([subject,': Combined Gradiometers'])

% Topoplot over certain time period
%----------------------------------

sensortype = 'cmb';
switch sensortype
    case 'mag'
        layout    = 'neuromag306mag.lay';
        avgs2plot = avgs;
    case 'grad'
        layout    = 'neuromag306planar.lay'; 
        avgs2plot = avgs;
    case 'cmb'
        layout = 'neuromag306cmb.lay'; 
        avgs2plot = avgs_cmb;
end

% time window for topoplot
timewin = [0.05, 0.15];

figure
for cidx = 1:C
    subplot(1,C,cidx)
    cfg        = [];
    cfg.xlim   = timewin; % time window of maximum amplitude (N100m, or wave five for ABR)
    cfg.layout = layout;
    cfg.figure = 'gcf'; % embeds topoplot in current figure
    ft_topoplotER(cfg,avgs2plot{cidx}); 
    title([subject,': ', conditions{cidx}])
end
sgtitle(sensortype)
