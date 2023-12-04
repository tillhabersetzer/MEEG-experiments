%--------------------------------------------------------------------------
% Till Habersetzer, 01.12.2023
% Communication Acoustics, CvO University Oldenburg
% till.habersetzer@uol.de
% 
% Within this script a singleshell headmodel is calculated which can be 
% used within MEG source modelling.
% 
% Nolte G. The magnetic lead field theorem in the quasi-static approximation 
% and its use for magnetoencephalography forward calculation in realistic 
% volume conductors. Phys Med Biol. 2003 Nov 21;48(22):3637-52. 
% doi: 10.1088/0031-9155/48/22/002. PMID: 14680264.
%
% Therefore, the mri is coregistered, resliced and segmented. 
% Optionally, the mri can be defaced.
% The resclided mri and / or the defaced and resliced mri are saved as a 
% nifti.
%--------------------------------------------------------------------------

close all
clear 
clc

%% Script settings
%--------------------------------------------------------------------------
eval('main_settings')

% select subject
subject = 'sub-01';

rawdata_path = fullfile(settings.path2project,'rawdata',subject);

% megfile
% get reference run
run_ref = settings.ref_run_dev2head;
megfile = fullfile(rawdata_path,'meg',[subject,'_task-aef_run-',num2str(run_ref),'.fif']);
% mrifile
mrifile  = fullfile(rawdata_path,'anat',[subject,'_T1w.nii']);

% directory for data storing
dir2save = fullfile(settings.path2project,'derivatives',subject);

%% Computation of headmodel
%--------------------------------------------------------------------------

% Extract Headshape
%------------------
headshape = ft_read_headshape(megfile,'unit','mm');

% Read in Mri
%------------
% ignore whether data is in bids formed, ignores reading sidecar files
mri_orig = ft_read_mri(mrifile,'readbids','no');

% 1. Coregistration to Neuromag Coordsystem based on Anatomical Landmarks
%--------------------------------------------------------------------------
cfg            = [];
cfg.method     = 'interactive';
cfg.coordsys   = 'neuromag';
mri_realigned1 = ft_volumerealign(cfg, mri_orig);

% Incorporate Headshape Information - automatic coregistration with icp
% algorithm (optional but recommended)
%--------------------------------------------------------------------------
cfg                       = [];
cfg.method                = 'headshape';
cfg.headshape.headshape   = headshape;
cfg.coordsys              = 'neuromag';
cfg.headshape.interactive = 'no';  % if manually: yes
cfg.headshape.icp         = 'yes'; % if manually: no / without automatic icp alignment - use only headshape
mri_realigned2            = ft_volumerealign(cfg, mri_realigned1);

% Check Results interactively in case of manual correction
%--------------------------------------------------------------------------
cfg                       = [];
cfg.method                = 'headshape';
cfg.headshape.headshape   = headshape;
cfg.coordsys              = 'neuromag';
cfg.headshape.interactive = 'yes';
cfg.headshape.icp         = 'no'; 
mri_coreg                 = ft_volumerealign(cfg, mri_realigned2);

% 2. Reslice
%--------------------------------------------------------------------------
% Check if full head is still in mri after reslicing. Might fail for big
% heads and is important in case you may need a bem headmodel which
% includes the scalp
cfg            = [];
cfg.resolution = 1;
cfg.dim        = [256 256 256];
cfg.yrange     = [-130,125]; % could be adjusted, see above remark, sum up to 255 -> 256 voxel
cfg.coordsys   = 'neuromag';
mri_resliced   = ft_volumereslice(cfg,mri_coreg); 

% Check 
%------
cfg = [];
ft_sourceplot(cfg, mri_coreg);
cfg = [];
ft_sourceplot(cfg, mri_resliced);

ft_write_mri(fullfile(dir2save,[subject,'_resliced.nii']), mri_resliced.anatomy, ...
            'transform', mri_resliced.transform, ...
            'coordsys','neuromag', ...
            'unit','mm', ...
            'dataformat', 'nifti');

% 3. Segmentation (most time consuming)
%--------------------------------------------------------------------------
cfg           = [];
cfg.output    = {'brain'}; % you only need brain for meg
mri_segmented = ft_volumesegment(cfg, mri_resliced);

% copy the anatomy into the segmentation for plotting
mri_segmented.anatomy = mri_resliced.anatomy;

% Check
%------
cfg              = [];
cfg.funparameter = 'brain';
ft_sourceplot(cfg, mri_segmented);

% 4. Headmodel
%--------------------------------------------------------------------------
cfg        = [];
cfg.method = 'singleshell';
vol        = ft_prepare_headmodel(cfg, mri_segmented);

% Check
%------
% Same Units for Plot
grad   = ft_read_sens(megfile,'senstype','meg','coilaccuracy',0); % cm
shape  = ft_read_headshape(megfile,'unit','cm');
vol_cm = ft_convert_units(vol,'cm');

figure
ft_plot_headmodel(vol_cm);
hold on
ft_plot_sens(grad, 'style', '*b');
ft_plot_headshape(shape);

% Save data
%----------
save(fullfile(dir2save,[subject,'_headmodel-singleshell.mat']),'vol'); % in mm

% 5. For defacing (optional)
%--------------------------------------------------------------------------
% check out for defacing:
% https://www.fieldtriptoolbox.org/faq/how_can_i_anonymize_an_anatomical_mri/

% add some padding to the brain by inflating it
% 5-voxel padding all around the brain
mri_segmented2       = mri_segmented;
se                   = strel('sphere', 5);
mri_segmented2.brain = imdilate(mri_segmented2.brain, se);

% Check
%------
cfg              = [];
cfg.funparameter = 'brain';
ft_sourceplot(cfg, mri_segmented2);

% MRI defacing 
%-------------
cfg         = [];
cfg.method  = 'spm';
mri_defaced = ft_defacevolume(cfg,mri_resliced);

% if automatic algorith fails - seems to fail, anatomy except brain is lost
% cfg         = [];
% mri_defaced = ft_defacevolume(cfg,mri_resliced);

% Check
%------
cfg = [];
ft_sourceplot(cfg, mri_defaced);

% Put the brain anatomy back using the padded brain segmentation
mri_defaced.anatomy(mri_segmented2.brain) = mri_resliced.anatomy(mri_segmented2.brain);

% Check
%-----
cfg = [];
ft_sourceplot(cfg, mri_defaced);

% Save as nifti
%--------------
ft_write_mri(fullfile(dir2save,[subject,'_anon.nii']), mri_defaced.anatomy, ...
    'transform', mri_defaced.transform, ...
    'coordsys','neuromag', ...
    'unit','mm', ...
    'dataformat', 'nifti');
