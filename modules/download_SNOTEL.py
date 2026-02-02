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
        "returnFlags": "false",
        "returnOriginalValues": "false",
        "returnSuspectData": "false",
        "format": "json"
    }

    r = requests.get(baseurl, params=params, timeout=60)
    r.raise_for_status()

    data = r.json()

    try:
        values = data[0]["data"][0]["values"]
    except (KeyError, IndexError):
        return pd.DataFrame()

    df = pd.DataFrame(values)

    if df.empty:
        return df

    df["date"] = pd.to_datetime(df["date"])
    df = df.rename(columns={"value": element.lower()})
    df["site_id"] = site_id
    df["wteq_mm"] = df["wteq"] * 25.4

    if out_csv:
        df.to_csv(out_csv, index=False)

    return df

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
    for site_id in df["site_id"]:

        try:
            print(f"Fetching {site_id}...")
            df = fetch_wteq_station_data(
                 site_id=site_id,
                 element=element,
                 duration=duration,
                 out_csv=None
             )
            df_lst.append(df)

        except Exception as e:
            print(f"⚠️  Failed for {site_id}: {e}")

    return df_lst

def stations_to_netcdf(df_meta, df_data_list, out_nc):
    """
    Create a CF-style ragged NetCDF for SNOTEL SWE with daily SWE rate (mm/day).
    """

    station_ids = df_meta["site_id"].values
    station_lookup = {sid: i for i, sid in enumerate(station_ids)}

    times = []
    wteq = []
    wteq_rate = []
    station_index = []

    for df in df_data_list:
        sid = df["site_id"].iloc[0]
        idx = station_lookup[sid]

        # Ensure sorted by time
        df = df.sort_values("date").copy()
        time_vals = pd.to_datetime(df["date"].values)
        swe = df["wteq_mm"].values

        # Compute daily SWE change
        rate = np.diff(swe, prepend=np.nan)

        # Reset rate at water-year boundaries (Oct 1)
        wy = np.where((time_vals.month == 10) & (time_vals.day == 1))[0]
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
    })

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


