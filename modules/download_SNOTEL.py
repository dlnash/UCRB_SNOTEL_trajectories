######################################################################
# Filename:    download_SNOTEL.py
# Author:      Deanna Nash dnash@ucsd.edu
# Description: Use the REST API from wcc to pull SNOTEL station data based on HUC2 value and save as csv
#
######################################################################

import pandas as pd
import requests
from pathlib import Path
import numpy as np
import xarray as xr

def readNRCS_by_huc(huc, element="WTEQ", duration="DAILY"):
    """
    Read NRCS SNOTEL station metadata for stations within a given HUC
    that report a specific element (default: SWE / WTEQ).

    Parameters
    ----------
    huc : str
        HUC identifier (e.g., '14' for HUC2, or full HUC14)
    element : str, optional
        AWDB element code (default 'WTEQ')
    duration : str, optional
        Data duration (default 'DAILY')

    Returns
    -------
    pandas.DataFrame
        Station metadata
    """

    baseurl = "https://wcc.sc.egov.usda.gov/awdbRestApi/services/v1/stations"

    params = {
        "stationTriplets": "*:*:SNTL",
        "elements": element,
        "durations": duration,
        "hucs": huc,  # prefix match: HUC2/HUC4/.../HUC14 all valid
        "activeOnly": "true",
        "returnForecastPointMetadata": "false",
        "returnReservoirMetadata": "false",
        "returnStationElements": "false",
        "format": "json"
    }

    response = requests.get(baseurl, params=params, timeout=30)
    response.raise_for_status()

    stations = response.json()
    df = pd.DataFrame(stations)

    if df.empty:
        return df

    # Standardize column names to match your existing workflow
    rename_map = {
        "stationTriplet": "site_id",
        "name": "site_name",
        "huc": "huc_id"
    }

    df = df.rename(columns=rename_map)

    return df

def fetch_wteq_station_data(
    site_id,
    element="WTEQ",
    duration="DAILY",
    begin_date="1900-01-01",
    end_date="2100-01-01",
    out_csv=None
):
    baseurl = "https://wcc.sc.egov.usda.gov/awdbRestApi/services/v1/data"

    params = {
        "stationTriplets": site_id,
        "elements": element,
        "duration": duration,
        "beginDate": begin_date,
        "endDate": end_date,
        "centralTendencyType": "MEDIAN",
        "returnFlags": "false",
        "returnOriginalValues": "false",
        "returnSuspectData": "false",
        "format": "json"
    }

    r = requests.get(baseurl, params=params, timeout=60)
    r.raise_for_status()

    data = r.json()

    # ---------------------------
    # 1. Time series values
    # ---------------------------
    try:
        values = data[0]["data"][0]["values"]
    except (KeyError, IndexError):
        return pd.DataFrame(), pd.DataFrame()

    df = pd.DataFrame(values)

    if df.empty:
        return df, pd.DataFrame()

    df["date"] = pd.to_datetime(df["date"])
    df["site_id"] = site_id

    # convert SWE (in → mm)
    df["wteq_mm"] = df["value"] * 25.4

    # ---------------------------
    # 2. Median WY peak metadata
    # ---------------------------
    try:
        peak_in = data[0]["data"][0]["timingCentralTendencies"]["medianPeak"]["value"]
    except (KeyError, IndexError, TypeError):
        peak_in = np.nan

    peak_df = pd.DataFrame({
        "site_id": [site_id],
        "wy_peak_median_mm": [peak_in * 25.4 if pd.notna(peak_in) else np.nan]
    })

    # ---------------------------
    # 3. Optional save
    # ---------------------------
    if out_csv:
        df.to_csv(out_csv, index=False)

    return df, peak_df

def fetch_wteq_for_dataframe(
    df,
    element="WTEQ",
    duration="DAILY"
):
    """
    Fetch WTEQ data for all stations in a metadata DataFrame.

    Parameters
    ----------
    df : pandas.DataFrame
        Must contain column 'site_id'
    """

    df_lst = []
    peak_lst = []
    for site_id in df["site_id"]:

        try:
            print(f"Fetching {site_id}...")
            df, peak_df = fetch_wteq_station_data(
                 site_id=site_id,
                 element=element,
                 duration=duration,
                 out_csv=None
             )
            df_lst.append(df)
            peak_lst.append(peak_df)

        except Exception as e:
            print(f"⚠️  Failed for {site_id}: {e}")

    return df_lst, peak_lst
    
def stations_to_netcdf(df_meta, df_data_list, peak_df_all, out_nc):
    """
    Create a CF-style ragged NetCDF for SNOTEL SWE with daily SWE rate (mm/day).
    """
    df_meta = df_meta.merge(peak_df_all, on="site_id", how="left")
    
    station_ids = df_meta["site_id"].values
    station_lookup = {sid: i for i, sid in enumerate(station_ids)}

    times = []
    wteq = []
    wteq_rate = []
    station_index = []

    for df in df_data_list:
        if df.empty:
            continue
        sid = df["site_id"].iloc[0]
        idx = station_lookup[sid]

        # Ensure sorted by time
        df = df.sort_values("date").copy()
        time_vals = pd.to_datetime(df["date"].values)
        swe = df["wteq_mm"].values

        # Compute daily SWE change
        rate = np.diff(swe, prepend=np.nan)

        # Reset rate at water-year boundaries (Oct 1)
        wy = np.where(
            (pd.DatetimeIndex(time_vals).month == 10) &
            (pd.DatetimeIndex(time_vals).day == 1)
        )[0]
        rate[wy] = np.nan

        times.append(time_vals)
        wteq.append(swe)
        wteq_rate.append(rate)
        station_index.append(np.full(len(df), idx, dtype=int))

    # Concatenate ragged obs
    times = np.concatenate(times)
    wteq = np.concatenate(wteq)
    wteq_rate = np.concatenate(wteq_rate)
    station_index = np.concatenate(station_index)

    # Create Dataset
    ds = xr.Dataset(
        data_vars=dict(
            wteq=(["obs"], wteq),
            wteq_rate=(["obs"], wteq_rate),
            station_index=(["obs"], station_index),
        ),
        coords=dict(
            time=(["obs"], times),
            station=(["station"], station_ids),
        ),
    )

    # Station metadata (1D only)
    ds = ds.assign({
        "latitude": ("station", df_meta["latitude"].values),
        "longitude": ("station", df_meta["longitude"].values),
        "elevation": ("station", df_meta["elevation"].values),
        "wy_peak_median": ("station", df_meta["wy_peak_median_mm"].values)
    })

    print(ds)
    print(np.nanmin(ds.wy_peak_median.values), np.nanmax(ds.wy_peak_median.values))

    # compute SWE as a fraction of median peak
    ds["wteq_pct_of_median_peak"] = (
    ds["wteq"] / ds["wy_peak_median"][ds["station_index"]]
)
    # compute normalized accumulation rate
    ds["wteq_rate_norm"] = (
    ds["wteq_rate"] / ds["wy_peak_median"][ds["station_index"]]
)

    # Attributes
    ds["wteq"].attrs.update({
        "long_name": "Snow Water Equivalent",
        "units": "mm",
        "standard_name": "lwe_thickness"
    })

    ds["wteq_rate"].attrs.update({
        "long_name": "Daily change in snow water equivalent",
        "units": "mm day-1",
        "description": "Difference in SWE between consecutive days; positive indicates accumulation, negative melt"
    })

    ds["wy_peak_median"].attrs.update({
    "long_name": "Median water year peak SWE (1991-2020)",
    "units": "mm",
    "description": "Median of annual maximum SWE (WTEQ) for water years 1991–2020"
    })

    ds["wteq_pct_of_median_peak"].attrs.update({
    "long_name": "SWE as fraction of median water year peak",
    "units": "1",
    "description": "Ratio of SWE to 1991–2020 median water year peak SWE"
})
    ds["wteq_rate_norm"].attrs.update({
    "long_name": "Normalized SWE change rate",
    "units": "day-1",
    "description": "Daily SWE change normalized by median water year peak SWE"
})

    ds["time"].attrs["standard_name"] = "time"
    ds["station"].attrs["cf_role"] = "timeseries_id"

    ds.to_netcdf(
        out_nc,
        format="NETCDF4",
        encoding={
            "wteq": {"zlib": True, "complevel": 4},
            "wteq_rate": {"zlib": True, "complevel": 4},
            "station_index": {"zlib": True, "complevel": 4},
        },
    )

    return ds


