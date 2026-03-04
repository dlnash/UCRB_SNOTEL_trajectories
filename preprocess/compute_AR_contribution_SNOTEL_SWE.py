import xarray as xr
import pandas as pd
import numpy as np
import sys, os

sys.path.append('../modules')
from preprocess_SNOTEL import get_station, add_wteq_90th_binary
from download_SNOTEL import readNRCS_by_huc


percentile = 95 # this is the percentile we are targeting
start_date = '1990-01-01'
end_date = '2024-12-31'

## open SNOTEL netCDF data
fname = '../data/UCRB_SNOTEL_SWE_data.nc'
SNOTEL = xr.open_dataset(fname)

full_time_index = pd.date_range(
    start=str(SNOTEL.time.min().values),
    end=str(SNOTEL.time.max().values),
    freq="D"
)

n_obs = len(full_time_index)
n_stations = SNOTEL.sizes["station"]

# Initialize dense SWE array with NaNs
dense_wteq = np.full((n_obs, n_stations), np.nan)

## Fill in values from ragged dataset
for i, stn_id in enumerate(SNOTEL.station.values):
    # obs for this station
    stn_obs = SNOTEL.where(SNOTEL.station_index == i, drop=True)
    
    # align station obs times with full_time_index
    stn_times = pd.to_datetime(stn_obs.time.values)
    stn_wteq = stn_obs.wteq_rate.values
    
    # find indices in full_time_index
    idx = full_time_index.get_indexer(stn_times)
    
    dense_wteq[idx, i] = stn_wteq

## Create dense xarray Dataset
dense_ds = xr.Dataset(
    data_vars=dict(
        wteq=(["time", "station"], dense_wteq)
    ),
    coords=dict(
        time=("time", full_time_index),
        station=("station", SNOTEL.station.values),
        latitude=("station", SNOTEL.latitude.values),
        longitude=("station", SNOTEL.longitude.values),
        elevation=("station", SNOTEL.elevation.values)
    )
)

dense_ds.wteq.attrs.update({
    "long_name": "Daily change in snow water equivalent",
    "units": "mm day-1",
    "description": "Difference in SWE between consecutive days; positive indicates accumulation, negative melt"
})
dense_ds.time.attrs["standard_name"] = "time"
dense_ds.station.attrs["cf_role"] = "timeseries_id"

# slice to start and end date
dense_ds = dense_ds.sel(time=slice(start_date, end_date))

## add water year to data as coordinate
water_year = (dense_ds.time.dt.month >= 10) + dense_ds.time.dt.year
dense_ds.coords['water_year'] = water_year

## add extreme prec variable
dense_ds = add_wteq_90th_binary(dense_ds, percentile=percentile)

## Load tARgetv4 AR data
path_to_data = '/cw3e/mead/projects/cwp162/data/'
fname = path_to_data + 'downloads/globalARcatalog_ERA5_1940-2024_v4.0.nc'
ds = xr.open_dataset(fname, chunks="auto")[["kidmap"]]
ds = ds.chunk({"time": 365})
ds = ds.isel(lev=0, ens=0)
ds = ds.assign_coords({"lon": (((ds.lon + 180) % 360) - 180)}) # Convert DataArray longitude coordinates from 0-359 to -180-179
latmin, latmax, lonmin, lonmax = 10., 70., -140., -80.
ds = ds.sel(lat=slice(latmax, latmin), lon=slice(lonmin, lonmax))
ds = ds.sel(time=slice(start_date, end_date))

# resample on the full grid first
ds_daily = ds.kidmap.resample(time="1D").max()

## Subset the AR dataset to the SNOTEL lat/lon
# Get lat/lon for all SNOTEL stations
lat_sel = dense_ds.latitude
lon_sel = dense_ds.longitude

# Select nearest AR grid cell for each HUC8
AR_at_SNOTEL = ds_daily.sel(
    lat=lat_sel,
    lon=lon_sel,
    method="nearest"
)

## create a new dataset with SWE values from SNOTEL, extreme binary, AR indication, and water year
ds_all = xr.Dataset(
    data_vars=dict(
        SWE           = dense_ds.wteq,
        extreme       = dense_ds.wteq_90th_binary,
        AR            = AR_at_SNOTEL,
    ),
    coords=dict(
        time        = dense_ds.time,
        station     = dense_ds.station,
        water_year  = dense_ds.water_year,
    ),
)
ds_all.to_netcdf(
        f'../out/UCRB_SNOTEL_tARgetv4_1990-2024_{percentile}-percentile.nc',
        format="NETCDF4")

#######################################################
### Create list of unique ARIDs associated with SWE ###
#######################################################
ds_all = ds_all.compute()
# Mask invalid AR values
idx = (ds_all.AR >= 0) & (ds_all.extreme == 1)
AR_valid = ds_all.AR.where(idx, drop=True)

# Convert to numpy, flatten, remove NaNs, get unique values
ARIDs = np.unique(AR_valid.values[~np.isnan(AR_valid.values)])

# Convert to DataFrame for clean CSV output
df_ARIDs = pd.DataFrame({"ARID": ARIDs})

# Save to CSV
df_ARIDs.to_csv(f"../out/unique_ARIDs_{percentile}-percentile.csv", index=False)

# # Subset to NDJFMA
# idx = (ds_all.time.dt.month >= 11) | (ds_all.time.dt.month <= 4)
# ds_all = ds_all.sel(time=idx)

# compute Total extreme precipitation (denominator)
SNOTEL_90 = ds_all.where(ds_all.extreme == 1)

SNOTEL_90WY = (
    SNOTEL_90.SWE
    .groupby("water_year")
    .sum("time")
    .sum("water_year")
)

# compute AR-associated extreme precipitation (numerator)
SNOTEL_AR90 = ds_all.where(
    (ds_all.extreme == 1) & (ds_all.AR > 0)
)


SNOTEL_AR90WY = (
    SNOTEL_AR90.SWE
    .groupby("water_year")
    .sum("time")
    .sum("water_year")
)

fraction90WY = (SNOTEL_AR90WY / SNOTEL_90WY) * 100
fraction_df = (
    fraction90WY
    .to_dataframe(name="AR_fraction_extreme_SWE")
    .reset_index()
)

path_to_out = '../out/'
fraction_df.to_csv(
    os.path.join(path_to_out, f"AR_fraction_{percentile}-percentile_SWE_SNOTEL.csv"),
    index=False
)

