######################################################################
# Filename:    calculate_trajectories.py
# Author:      Deanna Nash dnash@ucsd.edu
# Description: Script to run backwards trajectories for CO SNOTEL stations (all dates)
#
######################################################################

import os, sys
import yaml
import xarray as xr
import pandas as pd

path_to_repo = '/home/dnash/repos/eaton_scripps_CO_ARs/'
sys.path.append(path_to_repo+'modules')
from trajectory import calculate_backward_trajectory

path_to_data = '/expanse/nfs/cw3e/cwp140/'

## get HUC8 from config file
config_file = str(sys.argv[1]) # this is the config file name
job_info = str(sys.argv[2]) # this is the job name

config = yaml.load(open(config_file), Loader=yaml.SafeLoader) # read the file
ddict = config[job_info] # pull the job info from the dict

HUC8_ID = ddict['HUC8_ID']
event_date = ddict['date']

## set starting lat/lon
## choose this based on extreme precip days
fname = path_to_data + 'preprocessed/PRISM/PRISM_HUC8_CO_sp.nc'
ds = xr.open_dataset(fname)
# start with single event from single watershed
ds = ds.sel(HUC8=HUC8_ID)
# ds = ds.where(ds.extreme == 1, drop=True)

## calculate trajectory for current 
s = calculate_backward_trajectory(ds=ds, event_date=event_date)
df = s.compute_trajectory()
new_ds = df.to_xarray()

## save trajectory data to netCDF file
print('Writing {0} {1} to netCDF ....'.format(HUC8_ID, event_date))
out_fname = path_to_data + 'preprocessed/ERA5_trajectories_uncombined/PRISM_HUC8_{0}_{1}.nc'.format(HUC8_ID, event_date) 
new_ds.load().to_netcdf(path=out_fname, mode = 'w', format='NETCDF4')