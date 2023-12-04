%--------------------------------------------------------------------------
% Till Habersetzer, 01.12.2023
% Communication Acoustics, CvO University Oldenburg
% till.habersetzer@uol.de 
%
% This script checks the recorded triggers.
% - Plot events in STI001
% - Plot all triggers in sum channel (STI101)
% - Check Jitter
%--------------------------------------------------------------------------
close all
clear all
clc

% subject = 'sub-dummy';
subject = 'sub-03';
run     = '2'; 

path_dataset = fullfile('..','rawdata',subject,'meg',[subject,'_task-aef','_run-',num2str(run),'.fif']);

%% Load event information
%--------------------------------------------------------------------------
hdr   = ft_read_header(path_dataset);
event = ft_read_event(path_dataset);

smp = [event.sample];
typ = {event.type};
val = [event.value];

% experiment length
%------------------
% ~ time between first and last trigger
duration = (smp(end)-smp(1))/hdr.Fs;

%% Plot events in STI001
%--------------------------------------------------------------------------

idx           = and(strcmp(typ,'STI001'),val==5);
Num_of_Events = sum(idx);

figure
plot(smp(idx)/hdr.Fs,val(idx),'*')

% Check total amount of events
title(['sum of all events (STI001): ',num2str(Num_of_Events)])

%% Plot all triggers in sum channel (STI101)
%--------------------------------------------------------------------------

% plot events in scatter plot (only STI101)
idx            = strcmp(typ,'STI101');
val_sumchannel = val(idx);
trigIDs        = unique(val(idx));
figure
subplot(2,1,1)
plot(smp(idx)/hdr.Fs,val_sumchannel,'x')
title(['STI101 events found: ' num2str(sum(idx))])
ylim([0,10])
grid on
subplot(2,1,2)
for i = 1:length(unique(val(idx)))
    hold on
    plot(i,trigIDs(i),'x') % already sorted
    names{i} = [num2str(trigIDs(i))];
end
legend(names,'location','Northwest')
title(['sorted unique values: ' num2str(length(unique(val(idx))))])
ylim([0,10])
grid on


% trigger table (another option to depict trigger information)
%--------------------------------------------------------------------------
sample  = unique(smp)';
latency = (sample-1)/hdr.Fs;
type    = unique(typ)';

trigarray = nan(length(sample), length(type));

for i=1:numel(sample) % loop over samples
  sel = find(smp==sample(i));
  for j=1:numel(sel) % loop over different channel types for same sample
      trigarray(i, strcmp(type, typ{sel(j)})) = val(sel(j));
  end
end

trigtable = array2table(trigarray, 'VariableNames', type);
trigtable = [table(sample, latency) trigtable];

%% Check Jitter
%--------------------------------------------------------------------------
% Check jitter between trials
% Use STI101
idx    = and(strcmp(typ,'STI101'),val==1);
jitter = diff(smp(idx))*1000/hdr.Fs; % in ms

figure
histogram(jitter)
xlabel('t / ms')
ylabel('counts')
