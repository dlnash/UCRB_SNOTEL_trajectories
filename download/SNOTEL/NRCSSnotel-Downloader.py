######################################################################
# Filename:    NRCSSnotel-Downloader.py
# Author:      Deanna Nash dnash@ucsd.edu
# Description: Script to fetch and save SNOTEL data as csv files.
#
######################################################################
import sys
import os
import pandas as pd

sys.path.append('../../modules')
from download_SNOTEL import readNRCS_by_huc, fetch_wteq_for_dataframe, stations_to_netcdf

# ------------ Main -------------#
## get list of station metadata for stations in the HUC2 = 14
HUC = "14"
df_meta = readNRCS_by_huc(HUC)
df_meta = df_meta.set_index(pd.to_datetime(df_meta['beginDate']))
## limit to stations that have data starting in 1990 or earlier
idx = (df_meta.index <= '1990-01-01')
df_meta = df_meta.loc[idx]

## fetch the data from the databases and save as .csv
df_data_list = fetch_wteq_for_dataframe(
                df_meta,
                element="WTEQ",
                duration="DAILY"
            )

stations_to_netcdf(df_meta, df_data_list, '../../data/UCRB_SNOTEL_SWE_data.nc')