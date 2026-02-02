######################################################################
# Filename:    concat_trajectories.py
# Author:      Deanna Nash dnash@ucsd.edu
# Description: Script to concatenate trajectories from each watershed
#
######################################################################

import sys
import xarray as xr
import numpy as np
import pandas as pd

server='expanse'
if server == 'comet':
    path_to_data = '/data/projects/Comet/cwp140/'
elif server == 'expanse':
    path_to_data = '/expanse/nfs/cw3e/cwp140/'

fname = path_to_data + 'preprocessed/PRISM/PRISM_HUC8_CO_sp.nc'
ds = xr.open_dataset(fname)
ds = ds.sel(date=slice('2000-01-04', '2023-12-31')) ## have to remove Jan 1 and Jan 2 2000 dates bc we don't have Dec 30 and 31, 1999 data

## get list of HUC8 IDs
# HUC8_IDs = ds.HUC8.values
# HUC8_IDs = ['14010002']
HUC8_IDs = ['10180001'] ## North Platte Headwaters

## loop through all HUC8s
for i, HUC8_ID in enumerate(HUC8_IDs):
    print('Processing HUC8 {0}'.format(HUC8_ID))
    # get list of event dates from first HUC8
    tmp = ds.sel(HUC8=HUC8_ID)
    # tmp = tmp.where(tmp.extreme == 1, drop=True)
    tmp = tmp.where(tmp.prec >= 2.54, drop=True) # run trajectories for all days where precip is greater than 0.1 inch
    event_dates = tmp.date.values
    nevents = len(event_dates)
    
    ## append filenames to a list
    print('... gathering filenames ...')
    fname_lst = []
    for j, dt in enumerate(event_dates):
        ts = pd.to_datetime(str(dt)) 
        d = ts.strftime("%Y%m%d")
        fname = path_to_data + 'preprocessed/ERA5_trajectories_uncombined/PRISM_HUC8_{0}_{1}.nc'.format(HUC8_ID, d)
        fname_lst.append(fname)


    ## open all files for current HUC8
    ds_lst = []
    for j, fname in enumerate(fname_lst):
        ds_new = xr.open_dataset(fname)
        ds_lst.append(ds_new)

    ## save all trajectories for current HUC8 as single netcdf
    print('...saving as a single netcdf')
    final_ds = xr.concat(ds_lst, pd.Index(event_dates, name="start_date"))

    out_fname = '/expanse/nfs/cw3e/cwp140/preprocessed/ERA5_trajectories/combined/PRISM_HUC8_{0}.nc'.format(HUC8_ID)
    final_ds.to_netcdf(path=out_fname, mode = 'w', format='NETCDF4')