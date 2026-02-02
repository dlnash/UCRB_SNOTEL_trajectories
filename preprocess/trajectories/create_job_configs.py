######################################################################
# Filename:    create_job_configs.py
# Author:      Deanna Nash dnash@ucsd.edu
# Description: Script to create .yaml configuration file to run job_array with slurm for running ERA5 CO PRISM HUC8 trajectories
#
######################################################################

import yaml
from itertools import chain
import xarray as xr
import pandas as pd

## get list of HUC8 trajectories
path_to_data = '/expanse/nfs/cw3e/cwp140/'
fname = path_to_data + 'preprocessed/PRISM/PRISM_HUC8_CO_sp.nc'
ds = xr.open_dataset(fname)
ds = ds.sel(date=slice('2000-01-04', '2023-12-31')) ## have to remove Jan 1 and Jan 2 2000 dates bc we don't have Dec 30 and 31, 1999 data

# HUC8_lst = ds.HUC8.values
HUC8_lst = ['10180001']

jobcounter = 0
filecounter = 0
## loop through to create dictionary for each job
d_lst = []
dest_lst = []
njob_lst = []
for i, HUC8_ID in enumerate(HUC8_lst):
    tmp = ds.sel(HUC8=HUC8_ID)
    # tmp = tmp.where(tmp.extreme == 1, drop=True)
    
    tmp = tmp.where(tmp.prec >= 2.54, drop=True) # run trajectories for all days where precip is greater than 0.1 inch
    event_dates = tmp.date.values
    
    ### Loop through events for each HUC8 ###
    for j, edate in enumerate(event_dates):
        ts = pd.to_datetime(str(edate)) 
        ed = ts.strftime('%Y%m%d')
        print(HUC8_ID, ed)
    
        jobcounter += 1
        d = {'job_{0}'.format(jobcounter):
             {'HUC8_ID': HUC8_ID,
              'date': ed}}
        d_lst.append(d)
        
        if (jobcounter == 999):
            filecounter += 1
            ## merge all the dictionaries to one
            dest = dict(chain.from_iterable(map(dict.items, d_lst)))
            njob_lst.append(len(d_lst))
            ## write to .yaml file and close
            file=open("config_{0}.yaml".format(str(filecounter)),"w")
            yaml.dump(dest,file, allow_unicode=True, default_flow_style=None)
            file.close()
            
            ## reset jobcounter and d_lst
            jobcounter = 0
            d_lst = []
        
## now save the final config
filecounter += 1
## merge all the dictionaries to one
dest = dict(chain.from_iterable(map(dict.items, d_lst)))
njob_lst.append(len(d_lst))
## write to .yaml file and close
file=open("config_{0}.yaml".format(str(filecounter)),"w")
yaml.dump(dest,file, allow_unicode=True, default_flow_style=None)
file.close()

## create calls.txt for config_1(-8)

for i, njobs in enumerate(njob_lst):
    call_str_lst = []
    for j, job in enumerate(range(1, njobs+1, 1)):
        call_string = "python run_trajectories.py config_{0}.yaml 'job_{1}'".format(i+1, j+1)
        call_str_lst.append(call_string)
        
    ## now write those lines to a text file
    with open('calls_{0}.txt'.format(i+1), 'w',encoding='utf-8') as f:
        for line in call_str_lst:
            f.write(line)
            f.write('\n')
        f.close()