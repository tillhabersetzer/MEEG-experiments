%--------------------------------------------------------------------------
% Till Habersetzer, 03.12.2023
% Communication Acoustics, CvO University Oldenburg
% till.habersetzer@uol.de 
%
% Within this script
%-------------------
% - Dipole locations - symmetric / non-symmetric for all conditions
% - Dipole locations in MNI space and labels for all conditions
% - Dipole residual variance over time for all conditions
% - Dipole timecourses (xyz, magnitude) for all conditions
%--------------------------------------------------------------------------

close all
clear
clc

%% Settings
%--------------------------------------------------------------------------
eval('main_settings')

% Select subject for plotting
subidx  = 1;
subject = ['sub-',num2str(subidx,'%02d')];

% directory where data has been stored
dir2save = fullfile(settings.path2project,'derivatives',subject);

% time interval for timecourse visualization
time2plot = [-250 750]; % ms

% Choose sensortype for visualization
channeltype = 'megplanar'; % gradiometers
% channeltype = 'megmag'; % magnetometers
% channeltype = 'meg'; % all

% Take subselection of conditions
conditions = {'Run-1','Run-2','Combined'};

%% Load data 
%--------------------------------------------------------------------------

data           = load(fullfile(dir2save,[subject,'_dipolefitting.mat']));
conditions_all = data.conditions; 
channeltypes   = data.channeltypes;
idx            = contains(conditions_all,conditions); % subselection
timewin        = data.timewin;

% Take all conditions for subselection of sensortypes
chanidx       = find(contains(channeltypes,channeltype));
sources_sym   = data.sources_sym(chanidx,idx); % symmetrical dipolefit on pooled data  
sources_nosym = data.sources_nosym(chanidx,idx); % unconstrained dipolefit on pooled data
sources       = data.sources(chanidx,idx); % entire dipole timecourse          
      
clear data
fprintf('\nData from %s loaded.',subject)

C = length(conditions);

% Sourcemodel, template_grad and mri for visualization
% Convert into SI units
sourcemodel   = importdata(fullfile(dir2save,[subject,'_sourcemodel-volumetric.mat']));
template_grid = importdata(fullfile(settings.path2fieldtrip,'template','sourcemodel','standard_sourcemodel3d4mm.mat')); 
mri           = ft_read_mri(fullfile(dir2save,[subject,'_resliced.nii']));
mri.coordsys  = 'neuromag';
% Keep it in SI-units
sourcemodel   = ft_convert_units(sourcemodel,'m'); 
mri           = ft_convert_units(mri,'m'); 
% same units as atlas
template_grid = ft_convert_units(template_grid,'mm');

%% Rescale units - optional for plotting (Am -> nAm)
%--------------------------------------------------------------------------
for conidx = 1:C
    sources{conidx}.dip.mom = 10^9*sources{conidx}.dip.mom;
end

%% Inspect dipole locations - symmetric vs non-symmetric
%--------------------------------------------------------------------------
% Creates a figure with symmetric and non-symmetric dipoles for each
% condition

for conidx = 1:C
    figure
    hold on
    % symmetric dipole fit 
    ft_plot_dipole(sources_sym{conidx}.dip.pos(1,:), mean(sources_sym{conidx}.dip.mom(1:3,:),2), 'color', 'g', 'unit','m')
    ft_plot_dipole(sources_sym{conidx}.dip.pos(2,:), mean(sources_sym{conidx}.dip.mom(4:6,:),2), 'color', 'g', 'unit','m')
    
    % refinement of symmetric dipole fit 
    ft_plot_dipole(sources_nosym{conidx}.dip.pos(1,:), mean(sources_nosym{conidx}.dip.mom(1:3,:),2), 'color', 'r', 'unit','m')
    ft_plot_dipole(sources_nosym{conidx}.dip.pos(2,:), mean(sources_nosym{conidx}.dip.mom(4:6,:),2), 'color', 'r', 'unit','m')
    
    pos = mean(sources_sym{conidx}.dip.pos,1);
    ft_plot_slice(mri.anatomy, 'transform', mri.transform, 'location', pos, 'orientation', [1 0 0], 'resolution', 0.001)
    ft_plot_slice(mri.anatomy, 'transform', mri.transform, 'location', pos, 'orientation', [0 1 0], 'resolution', 0.001)
    ft_plot_slice(mri.anatomy, 'transform', mri.transform, 'location', pos, 'orientation', [0 0 1], 'resolution', 0.001)
    
    ft_plot_crosshair(pos, 'color', [1 1 1]/2);
    
    axis tight
    axis off
    
    view(12, -10)

    sgtitle(conditions{conidx})
end

%% Inspect dipole locations in mni space
%--------------------------------------------------------------------------
% Labels for dipole locations are retrieved in the following way:
% - Starting point: Dipole locations on subject specific grid (sourcemodel)
%                   The grid has been inverse warped onto subject anatomy.
%                   Each grid point in subject specific coordinates refers 
%                   to a point in mni space on the template grid.
% - Find closest gridpoint in sourcemodel to fitted dipole locations.
% - Use index of the location to retrieve the corresponding MNI coordinates
%   in the template grid
% - Use ft_volumenlookup to get the label of the location in MNI
%   coordinates from an atlas

% read atlas
atlas = ft_read_atlas(fullfile(settings.path2fieldtrip,'template','atlas','aal','ROI_MNI_V4.nii')); % mm

cfg        = [];
cfg.atlas  = atlas;
cfg.output = 'single';

% left/right
dippos_label_sym   = cell(C,2); % conditions y left/right
dippos_label_nosym = cell(C,2);

% Loop over conditions
%---------------------
for conidx = 1:C
    % positions of closest grid points
    dippos_sym       = sources_sym{conidx}.dip.pos;
    idx              = dsearchn(sourcemodel.pos,dippos_sym); % returns the indices of the closest points in P to the query points in PQ measured in Euclidean distance
    dippos_sym_mni   = template_grid.pos(idx,:);
    
    dippos_nosym     = sources_nosym{conidx}.dip.pos;
    idx              = dsearchn(sourcemodel.pos,dippos_nosym); 
    dippos_nosym_mni = template_grid.pos(idx,:);
    
    % Loop over both positions left / right
    %--------------------------------------
    for p=1:2
        % symmetric
        cfg.roi                    = dippos_sym_mni(p,:); 
        labels                     = ft_volumelookup(cfg, atlas);
        [~, indx]                  = max(labels.count);
        dippos_label_sym{conidx,p} = labels.name(indx);
    
        % non-symmetric
        cfg.roi                      = dippos_nosym_mni(p,:); 
        labels                       = ft_volumelookup(cfg, atlas);
        [~, indx]                    = max(labels.count);
        dippos_label_nosym{conidx,p} = labels.name(indx);
    end  
end

%% Plot residual variance over time
%--------------------------------------------------------------------------
% goodness of fit: 1-rv?
colors = {'r','b','m'};
names = cell(1,2*C);

figure
for conidx = 1:C
    subplot(2,1,1)
    hold on
    plot(sources_sym{conidx}.time*1000, sources_sym{conidx}.dip.rv,'LineStyle','--', 'Color', colors{conidx})
    plot(sources_nosym{conidx}.time*1000, sources_nosym{conidx}.dip.rv, 'LineStyle','-', 'Color', colors{conidx})
    grid on
    xlabel('t / ms')
    ylabel('residual variance')
    title(['Fit on timewindow: ',num2str(timewin),' s'])
    names{2*conidx-1} =  ['Symmetric fit: ',conditions{conidx}];
    names{2*conidx}   =  ['Non-symmetric fit: ',conditions{conidx}];
    if conidx==C
        legend(names)
    end

    subplot(2,1,2)
    hold on
    plot(sources{conidx}.time*1000, sources{conidx}.dip.rv,'Color', colors{conidx})
    grid on
    xlabel('t / ms')
    ylabel('residual variance')
    title('Fit on entire timecourse with non-symmetric positions')
    if conidx==C
        legend(conditions)
    end
end

%% Inspect timecourses - All moments, xyz-directions and both hemispheres
%--------------------------------------------------------------------------
color = {'r','b','m'};

% Add dipole magnitude 
%---------------------
% choose metric
% euclidian distance / vector magnitude
dipmags = cell(1,C);
for conidx = 1:C
    dipmag = zeros(2,length(sources{1}.time)); 
    dipmag(1,:) = sqrt(sum(sources{conidx}.dip.mom(1:3,:).^2,1)); % left
    dipmag(2,:) = sqrt(sum(sources{conidx}.dip.mom(4:6,:).^2,1)); % right
    dipmags{conidx} = dipmag;
end

for conidx = 1:C

    % Get limits
    %-----------
    time    = sources{conidx}.time*1000; 
    mini    = min([sources{conidx}.dip.mom;dipmags{conidx}],[],'all');
    maxi    = max([sources{conidx}.dip.mom;dipmags{conidx}],[],'all');
    axisvec = horzcat(time2plot,[mini,maxi]);
    axs     = cell(1,8);

    figidxs = [1,2;3,4;5,6;7,8]; % index for subplots (4x2, xyz left/right)
    figure
    for i=1:2 % i=1:left / i=2:right
    
        if i==1
            idx = 1:3; % 1st dipole (left)
        else
            idx = 4:6; % 2nd dipole (right)
        end
    
        figidx = figidxs(:,i);
        
        % all directions
        axs{figidx(1)} = subplot(4,2,figidx(1)); 
        plot(time, sources{conidx}.dip.mom(idx,:))
        hold on
        plot(time, dipmags{conidx}(i,:),'LineWidth',2)
        if i==1; ylabel('dipole moment / nAm'); end
        axis(axisvec) 
        grid on
        if i==1
            title(['left hemisphere (', dippos_label_nosym{conidx,i}{1}, ') all directions'],'Interpreter','none')
        else
            title(['right hemisphere (', dippos_label_nosym{conidx,i}{1}, ') all directions'],'Interpreter','none')
            legend({'x','y','z','magnitude'})
        end
        
        % x-direction
        axs{figidx(2)} = subplot(4,2,figidx(2)); 
        plot(time, sources{conidx}.dip.mom(idx(1),:))
        if i==1; ylabel('dipole moment / nAm'); end
        axis(axisvec) 
        grid on
        title('x')
        
        % y-direction
        axs{figidx(3)} = subplot(4,2,figidx(3)); 
        plot(time, sources{conidx}.dip.mom(idx(2),:))
        if i==1; ylabel('dipole moment / nAm'); end
        axis(axisvec)
        grid on
        title('y')
        
        % z-direction
        axs{figidx(4)} = subplot(4,2,figidx(4)); 
        plot(time, sources{conidx}.dip.mom(idx(3),:))
        xlabel('t / ms')
        if i==1; ylabel('dipole moment / nAm'); end
        axis(axisvec)
        grid on
        title('z')
    end

    sgtitle([subject,': ',conditions{conidx}])
    
end

linkaxes([axs{:}],"x")
