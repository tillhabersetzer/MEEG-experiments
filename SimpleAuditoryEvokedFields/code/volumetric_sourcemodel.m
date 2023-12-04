%--------------------------------------------------------------------------
%  Till Habersetzer, 01.12.2023
% Communication Acoustics, CvO University Oldenburg
% till.habersetzer@uol.de
%
% Generate volumetric grid based sourcemodels
% 
% In order to do source reconstruction across multiple subjects, subjects
% specific grids are constructed that are mapped onto a template grid in 
% spatially normalized space (MNI). The source space can be restricted by 
% using regions of interest (ROIs)
% Check out: https://www.fieldtriptoolbox.org/tutorial/sourcemodel/
%--------------------------------------------------------------------------

close all
clear 
clc

%% Script settings
%--------------------------------------------------------------------------
eval('main_settings')

% select subject
subject = 'sub-01';

% Path to FieldTrip
path2fieldtrip = settings.path2fieldtrip;

% Path to rawdata
rawdata_path = fullfile(settings.path2project,'rawdata',subject);

% Directory for data storing
dir2save = fullfile(settings.path2project,'derivatives',subject);

%% Source model 
%--------------------------------------------------------------------------

% load template grid
%-------------------
% use 5 mm grid 
% template_grid = importdata(fullfile(path2fieldtrip,'template','sourcemodel','standard_sourcemodel3d5mm.mat'));
% use 4 mm grid 
template_grid          = importdata(fullfile(path2fieldtrip,'template','sourcemodel','standard_sourcemodel3d4mm.mat'));
template_grid          = ft_convert_units(template_grid,'mm'); 
template_grid.coordsys = 'mni';

% Use atlas to create a binary mask
%--------------------------------------------------------------------------
atlas = ft_read_atlas(fullfile(path2fieldtrip,'template','atlas','aal','ROI_MNI_V4.nii'));

% Select all temporal labels including Heschl
idx    = contains(atlas.tissuelabel,{'Temporal','Heschl'});
labels = atlas.tissuelabel(idx);

cfg       = [];
cfg.atlas = atlas;
% cfg.roi   = atlas.tissuelabel;  % here you can also specify a single label, i.e. single ROI
cfg.roi   = labels;  % here you can also specify a single label, i.e. single ROI
mask      = ft_volumelookup(cfg, template_grid);

template_grid.inside          = false(template_grid.dim);
template_grid.inside(mask==1) = true;
%--------------------------------------------------------------------------

% plot the atlas based grid
figure
ft_plot_mesh(template_grid.pos(template_grid.inside,:));

% Load coregistered mri and make the individual subjectsm grid
%--------------------------------------------------------------------------

% mri = ft_read_mri(fullfile(dir2save,[subject,'_anon.nii']));
mri = ft_read_mri(fullfile(dir2save,[subject,'_resliced.nii']));
mri.coordsys = 'neuromag';

cfg           = [];
cfg.warpmni   = 'yes';
cfg.template  = template_grid;
cfg.nonlinear = 'yes';
cfg.mri       = mri;
cfg.unit      = 'mm';
sourcemodel   = ft_prepare_sourcemodel(cfg);

% Plot the final source model together with the individual head model and the sensor array
% Check sourcemodel
%--------------------------------------------------------------------------
% get reference run
run_ref   = settings.ref_run_dev2head;
megfile   = fullfile(rawdata_path,'meg',[subject,'_task-aef_run-',num2str(run_ref),'.fif']);
shape     = ft_read_headshape(megfile,'unit','mm');
grad      = ft_convert_units(ft_read_sens(megfile,'senstype','meg','coilaccuracy',0),'mm'); 
headmodel = importdata(fullfile(dir2save,[subject,'_headmodel-singleshell.mat'])); % mm

figure
hold on   
ft_plot_headmodel(headmodel, 'facecolor', 'cortex', 'edgecolor', 'none');
alpha 0.5;  % camlight;
alpha 0.4;  % make the surface transparent
ft_plot_headshape(shape);
ft_plot_mesh(sourcemodel.pos(sourcemodel.inside,:)); % plot only locations inside the volume
ft_plot_sens(grad, 'style', '*b');
view ([0 -90 0])

% Save sourcemodel
%--------------------------------------------------------------------------
save(fullfile(dir2save,[subject,'_sourcemodel-volumetric.mat']),'sourcemodel'); % in mm
