%--------------------------------------------------------------------------
% Till Habersetzer, 03.12.2023
% Communication Acoustics, CvO University Oldenburg
% till.habersetzer@uol.de 
%
% Check out: https://www.fieldtriptoolbox.org/workshop/natmeg/dipolefitting/
% 
% Computation of dipolefit
%-------------------------
% This script performs dipolfitting with a loop over all subjects
% steps:
% Fit for each condition (run-1, run-2) and each channeltype (megmag,
% megplanar, meg) -> 6 fits
% For each fit:
% - An initial symmetric dipolefit based on the 'N100m' component of the
%   is computed. The initial dipole is fitted based on a subject specific
%   dipole grid.
% - The initial dipolefit is refined afterwards with an unconstrained
%   nonlionear dipole search taking the symmetrical positions as a starting
%   point.
% - The estimated dipole locations are used to fit the entire dipole 
%   timecourse 
% - In case the dipole are estimated in different hemispheres, the fitted 
%   dipoles are rearranged in the fieldtrip data structure so that they can
%   be handled easier.
%--------------------------------------------------------------------------

close all
clear 
clc 

%% Script settings
%--------------------------------------------------------------------------
eval('main_settings')

% select subjects
subjects = [1,3];
% no mri available for sub-02 // template?!

% Correct dipole positions left / right
% dip.mom 1:3 (left), 4:6 (right)
% dip.pos(1) (left), dip.pos(2) (right)
correct_dippos = true;

% Choose channeltypes for fit
%----------------------------
% fit on combined sensors 'meg' should be avoided at the moment cause
% - https://www.fieldtriptoolbox.org/workshop/paris2019/handson_sourceanalysis/
% - requires prewhitening to equalize mags and grads
% - Unsure whether sphering option during dipolefitting is sufficient in
%   comparison with code in ft_denoise_prewhiten
% - in case of maxfilter regularization of the inverse

channeltypes = {'megmag', 'megplanar','meg'};
Nchantypes   = length(channeltypes);

% subject-specific settings
%--------------------------
% same for all subjects
timewin_struct.sub01 = [0.05, 0.18]; % 50-180 ms
timewin_struct.sub02 = [0.05, 0.18];
timewin_struct.sub03 = [0.05, 0.18];

%% Computation of dipolefit
%--------------------------------------------------------------------------

for subidx=subjects % loop over subjects

    subject  = ['sub-',num2str(subidx,'%02d')];

    % Select timewindow for fit
    timewin = timewin_struct.(replace(subject,'-',''));

    % Load the data
    %--------------
    % directory for data storing
    dir2save   = fullfile(settings.path2project,'derivatives',subject);
    data       = load(fullfile(dir2save,[subject,'_erfs.mat']));
    avgs       = data.avgs;
    avg_noise  = data.avg_noise; % for sphering
    conditions = data.conditions;
    C          = length(conditions);

    clear data
    
    % Load sourcemodel and headmodel
    %-------------------------------
    % Proceed in SI-units. Leads apparantly to correct units for dipole moments in Am
    sourcemodel = importdata(fullfile(dir2save,[subject,'_sourcemodel-volumetric.mat']));
    sourcemodel = ft_convert_units(sourcemodel, 'm'); 

    headmodel = importdata(fullfile(dir2save,[subject,'_headmodel-singleshell.mat']));
    headmodel = ft_convert_units(headmodel, 'm');

    % Initialize cell for results
    %----------------------------
    sources_sym   = cell(Nchantypes,C); % symmetric fit
    sources_nosym = cell(Nchantypes,C); % refined non-symmmetric fit
    sources       = cell(Nchantypes,C); % entire timecourse fitted
    
    % loop over different channeltyes
    %--------------------------------
    for chanidx = 1:Nchantypes

        % Apply Sphering if magnetometers and gradiometers are used
        % together (postponed)
        %----------------------------------------------------------
        switch channeltypes{chanidx}
            case 'megmag'
                channeltype = 'megmag';
                sphering    = false;
            case 'megplanar'
                channeltype = 'megplanar';
                sphering    = false;
            case 'meg'
                channeltype = 'meg';
                sphering    = true;
        end

        % Loop ober conditions
        %---------------------
        for conidx = 1:C   

            %% Fit initial dipole model with symmetric constraint - pooled condition
            %-----------------------------------------------------------------------
            % Since we expect activity in both auditory cortices, we will use a 
            % two-dipole model. Scanning the whole brain with two separate 
            % dipoles is not possible, but we can also start with the assumption 
            % that the two dipoles are symmetric.

            % Symmetrical gridsearch
            %-----------------------
            cfg                         = [];
            cfg.latency                 = timewin;
            cfg.model                   = 'regional';% A regional dipole model has the same position for each timepoint or component, and a different orientation.
            cfg.numdipoles              = 2; % fit 2 dipoles
            cfg.symmetry                = 'x'; % expect activity in both auditory cortices, fit symmetric dipole
            cfg.sourcemodel             = sourcemodel;
            cfg.headmodel               = headmodel;
            cfg.gridsearch              = 'yes';
            cfg.senstype                = 'meg';
            cfg.channel                 = channeltype;
            if sphering; cfg.dipfit.noisecov = avg_noise.cov; end
            sources_sym{chanidx,conidx} = ft_dipolefitting(cfg, avgs{conidx});

            %% Release symmetry constraint and refine fit - pooled condition
            %---------------------------------------------------------------
            % Since we know where to start with the gradient-descent non-linear 
            % optimization, we do not have to perform the grid-search.
        
            cfg                           = [];
            cfg.latency                   = timewin;
            cfg.numdipoles                = 2;
            cfg.symmetry                  = []; % no symmetry constraint
            cfg.gridsearch                = 'no'; % perform global search for initial guess for the dipole parameters
            cfg.nonlinear                 = 'yes'; % non-linear search for optimal dipole parameters
            cfg.sourcemodel.unit          = sourcemodel.unit; % defines units of dipole positions
            cfg.headmodel                 = headmodel;
            cfg.dip.pos                   = sources_sym{chanidx,conidx}.dip.pos;
            cfg.senstype                  = 'meg';
            cfg.channel                   = channeltype;
            if sphering; cfg.dipfit.noisecov = avg_noise.cov; end
            sources_nosym{chanidx,conidx} = ft_dipolefitting(cfg, avgs{conidx});

            %% Fit dipole for entire timecourse 
            %----------------------------------
         
            % estimate the amplitude and orientation
            cfg                     = [];
            cfg.latency             = 'all'; % entire timecourse
            cfg.numdipoles          = 2;
            cfg.symmetry            = [];
            cfg.nonlinear           = 'no'; % use a fixed position
            cfg.gridsearch          = 'no';
            cfg.dip.pos             = sources_nosym{chanidx,conidx}.dip.pos;
            cfg.sourcemodel.unit    = sourcemodel.unit;
            cfg.headmodel           = headmodel;
            cfg.senstype            = 'meg';
            cfg.channel             = channeltype;
            if sphering; cfg.dipfit.noisecov = avg_noise.cov; end
            sources{chanidx,conidx} = ft_dipolefitting(cfg, avgs{conidx});

            % Correct dipole positions - left / right
            %----------------------------------------------------------------------
            if correct_dippos
                % dip.mom: 
                % 1:3 left, 4:6 right
                % dip.pos:
                % 1: left, 2: right
    
                % symmetric dipoles
                %------------------
                positions = sources_sym{chanidx,conidx}.dip.pos;
                moments   = sources_sym{chanidx,conidx}.dip.mom;
                try
                    mapping = check_diploc(positions); 
                catch error % in case dipoles are in some hemisphere
                    mapping = [1,2]; % dont change anything
                end
        
                % change moments and positions of entries if first dipole  is in 
                % right hemisphere
                if mapping(1) == 2 
                    sources_sym{chanidx,conidx}.dip.pos = positions([2,1],:);
                    sources_sym{chanidx,conidx}.dip.mom = moments([4,5,6,1,2,3],:);
                end
    
                % non-symmetric dipoles
                %----------------------
                positions = sources_nosym{chanidx,conidx}.dip.pos;
                moments   = sources_nosym{chanidx,conidx}.dip.mom;
                try
                    mapping = check_diploc(positions); 
                catch error
                    mapping = [1,2]; % dont change anything
                end
        
                % change moments and positions of entries if first dipole  is in 
                % right hemisphere
                if mapping(1) == 2 
    
                    sources_nosym{chanidx,conidx}.dip.pos = positions([2,1],:);
                    sources_nosym{chanidx,conidx}.dip.mom = moments([4,5,6,1,2,3],:);
  
                    % Correct fit for entire timecourse
                    moments                         = sources{chanidx,conidx}.dip.mom;
                    sources{chanidx,conidx}.dip.pos = positions([2,1],:);
                    sources{chanidx,conidx}.dip.mom = moments([4,5,6,1,2,3],:);
                end

            end
            %--------------------------------------------------------------
                        
        end % loop over conditions

    end % loop over channels
    
    % Save data
    %----------------------------------------------------------------------
    results.conditions     = conditions;
    results.timewin        = timewin;
    results.channeltypes   = channeltypes;
    % dipolfits
    results.correct_dippos = correct_dippos;
    results.sources_sym    = sources_sym;
    results.sources_nosym  = sources_nosym;
    results.sources        = sources; % channeltypes x conditions
  
    save(fullfile(dir2save,[subject,'_dipolefitting.mat']),'-struct','results'); % in mm

    clear results
    
end % loop over subjects

function [mapping] = check_diploc(pos)
%--------------------------------------------------------------------------
% Till Habersetzer (25.01.2022)
% Dipole locations of a 2-dipol-fit are checked in terms of their mappings
% to the left and right hemisphere.
%
% Input:
%   pos: dipole locations (2,3) of 2 dipoles
%
% Output:
%   mapping: [1,2]: first dipole (1st row) is in left hemisphere
%            second dipole (2nd row) is in right hemisphere
%            [2,1]: Other way around
%   If both dipoles belong to the same hemisphere, the functions returns an
%   error.
%--------------------------------------------------------------------------
% check if source locations have different signs in x-direction

s1 = sign(pos(1,1)); % sign first position
s2 = sign(pos(2,1)); % sign second position
if ~isequal(s1,s2)
   if s1<0 %left
       mapping = [1,2];
   else
       mapping = [2,1];
   end
else
    error('Source locations are invalid. Both locations belong to same hemisphere.')
end

end
