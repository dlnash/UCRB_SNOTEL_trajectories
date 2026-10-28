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

## fetch the data from the databases and save as .csv
df_data_list, peak_lst = fetch_wteq_for_dataframe(
                df_meta,
                element="WTEQ",
                duration="DAILY"
            )

peak_df_all = (
    pd.concat(peak_lst, ignore_index=True)
    .drop_duplicates(subset="site_id")
)

stations_to_netcdf(df_meta, df_data_list, peak_df_all, out_nc='../../data/UCRB_SNOTEL_SWE_data_with_median_peak.nc')