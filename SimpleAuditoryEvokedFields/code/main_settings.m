%--------------------------------------------------------------------------
% Till Habersetzer, 03.12.2023
% Communication Acoustics, CvO University Oldenburg
% till.habersetzer@uol.de
%--------------------------------------------------------------------------

% ensure that we don't mix up settings
clear settings

% Define paths
%-------------
% FieldTrip path
settings.path2fieldtrip   = fullfile('C:','Users','tillhabersetzer','Nextcloud','Synchronisation','Projekte','Toolboxen','fieldtrip-20231113');
% Project path, contains code, rawdata, and derivatives directory
settings.path2project     = fullfile('C:','Users','tillhabersetzer','Nextcloud','Synchronisation','Projekte','GitHub','MEEG-experiments','SimpleAuditoryEvokedFields');
settings.subjects         = {'sub-01','sub-02','sub-03'};
settings.ref_run_dev2head = 1; % run with reference dev-to-head trafo during coregistration
% Optional
%---------
% Channels are removed for all participants. Badchannel rejection is only
% applied if maxfilter wasn't used.
settings.badchannels = {'-MEG0721'}; 

% Create directories
%-------------------
for sidx = 1:length(settings.subjects)
    subject = settings.subjects{sidx};
    dir_path = fullfile(settings.path2project,'derivatives',subject);
    if ~exist(dir_path, 'dir')
       mkdir(dir_path)
    end
end
clear sidx dir_path subject