import xarray as xr
import numpy as np

def add_wteq_90th_binary(dense_ds, threshold_min=2.54, percentile=90):
    """
    Add a binary variable to a dense SWE dataset indicating whether SWE
    exceeds the 90th percentile per station, considering only SWE > threshold_min.
    
    Parameters
    ----------
    dense_ds : xarray.Dataset
        Dense dataset with dimensions (time, station) and variable 'wteq'.
    threshold_min : float
        Minimum SWE value to include when computing the percentile (default 2.54 mm).
    percentile : float
        Percentile to compute per station (default 90).
        
    Returns
    -------
    xarray.Dataset
        Same dataset with an added variable 'wteq_90th_binary' (1 if >90th percentile, 0 otherwise)
    """

    # Initialize array for binary variable
    binary = np.zeros_like(dense_ds.wteq.values, dtype=int)

    # Loop over stations
    for i in range(dense_ds.sizes["station"]):
        # SWE for this station
        wteq_i = dense_ds.wteq[:, i].values
        
        # Mask SWE <= threshold_min or NaN
        mask_valid = wteq_i > threshold_min
        valid_values = wteq_i[mask_valid]

        if len(valid_values) == 0:
            # If no valid values, leave all zeros
            continue
        
        # Compute 90th percentile for this station
        p90 = np.percentile(valid_values, percentile)
        
        # Assign binary: 1 where SWE > 90th percentile
        binary[:, i] = (wteq_i > p90).astype(int)

    # Add as new variable
    dense_ds = dense_ds.assign(wteq_90th_binary=(["time", "station"], binary))
    
    return dense_ds


def get_station(ds, station_idx=None, station_id=None, dropna_var="wteq"):
    """
    Return a clean per-station dataset from a ragged SNOTEL NetCDF.

    Parameters
    ----------
    ds : xarray.Dataset
        Ragged NetCDF dataset with dimensions:
        - obs: observations
        - station: station metadata
        Must include:
        - 'station_index' (obs) mapping obs -> station
        - 'wteq' (obs)
        - 'latitude', 'longitude', 'elevation' (station)
    station_idx : int, optional
        0-based station index to select.
    station_id : str, optional
        Station ID string to select.
    dropna_var : str, default 'wteq'
        Variable name to drop NaN observations.

    Returns
    -------
    xarray.Dataset
        Dataset containing only observations for the requested station,
        with NaNs removed and metadata preserved.
    """

    # Validate input
    if station_idx is None and station_id is None:
        raise ValueError("Must provide either station_idx or station_id.")

    if station_idx is not None:
        if station_idx < 0 or station_idx >= ds.sizes["station"]:
            raise IndexError(f"station_idx {station_idx} out of range")
        # Map index to station_id
        station_id = ds.station.values[station_idx]

    # Get obs for the station
    stn_ds = ds.where(ds.station_index == station_idx if station_idx is not None else None, drop=True)

    # Select metadata for this station
    stn_ds = stn_ds.sel(station=station_id)

    # Drop NaN observations for the variable of interest
    if dropna_var in stn_ds.data_vars:
        stn_ds = stn_ds.dropna(dim="obs", subset=[dropna_var])

    return stn_ds
