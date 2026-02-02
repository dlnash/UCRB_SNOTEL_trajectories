# Standard Python modules
import os, sys
import glob
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, LineString
import xarray as xr
import re
from datetime import datetime, timedelta

path_to_data = '/cw3e/mead/projects/cwp162/data/'
path_to_out  = '../out/'       # output files (numerical results, intermediate datafiles) -- read & write
path_to_figs = '../figs/'      # figures

task_id = int(os.environ["SLURM_ARRAY_TASK_ID"])
BATCH_SIZE = 25

# Load ARIDs from CSV
arid_df = pd.read_csv(
    f"{path_to_out}unique_ARIDs.csv",
    dtype={"ARID": "int64"}
)

ARID_all = arid_df["ARID"].values

start = task_id * BATCH_SIZE
end = min(start + BATCH_SIZE, len(ARID_all))

ARID_list = ARID_all[start:end]

if len(ARID_list) == 0:
    print(f"Task {task_id}: no ARIDs assigned, exiting")
    sys.exit(0)

print(f"Task {task_id}: processing ARIDs {start}–{end-1}")

def parse_arid(arid):
    arid = int(arid)  # cast defensively
    s = f"{arid:012d}"
    start_time = datetime.strptime(s[:10], "%Y%m%d%H")
    id0 = int(s[-2:])
    return start_time, id0


def get_landfall_vars(ds, arid, start_time, id0):
    # start_time_str = start_time.strftime("%Y-%m-%d %H:%M")
    tmp = ds.sel(time=start_time)

    lf = (
        tmp[["lflat", "lflon", "lfivtx", "lfivty", "lfivtdir"]]
        .isel(lat=id0-1)
        .compute()
    )
    
    landfall = dict(
        lflat     = lf.lflat.item(),
        lflon     = lf.lflon.item(),
        lfivtx    = lf.lfivtx.item(),
        lfivty    = lf.lfivty.item(),
        lfivtdir  = lf.lfivtdir.item(),
    )

    return landfall
    
def get_ar_lifetime(ds, arid, start_time, max_hours=14*24):
    
    end_time_guess = start_time + timedelta(hours=max_hours)
    end_time_guess = end_time_guess.strftime("%Y-%m-%d %H:%M")

    start_time_str = start_time.strftime("%Y-%m-%d %H:%M")

    ds_window = ds.sel(time=slice(start_time_str, end_time_guess))

    present = ds_window.kidmap == arid
    present = present.any(dim=("lat", "lon"))

    present = present.load()
    times = ds_window.time.where(present, drop=True)

    if len(times) == 0:
        return None, None, None

    return times.min().values, times.max().values, ds_window.sel(time=times)

def get_ar_trajectory(ds_life, arid):
    mask = ds_life.kidmap == arid

    shapemap = ds_life.shapemap.where(mask)

    # IMPORTANT: compute indexers first
    ids = (
        shapemap
        .max(dim=("lat", "lon"), skipna=True)
        .astype(int)
        .values - 1
    )

    clat = ds_life.clat.isel(lat=ids)
    clon = ds_life.clon.isel(lat=ids)

    traj = xr.Dataset(
        data_vars=dict(
            clat=clat,
            clon=clon,
        ),
        coords=dict(time=ds_life.time)
    )

    return traj


def process_arid(ds, arid):
    start_time, id0 = parse_arid(arid)

    t0, t1, ds_life = get_ar_lifetime(ds, arid, start_time)
    if ds_life is None:
        return None, None
    print(t0)
    landfall = get_landfall_vars(ds, arid, t0, id0)
    traj = get_ar_trajectory(ds_life, arid)

    event = {
        "ARID": arid,
        "start_time": t0,
        "end_time": t1,
        **landfall
    }

    return event, traj


## Load tARgetv4 AR data
fname = path_to_data + 'downloads/globalARcatalog_ERA5_1940-2024_v4.0.nc'
vars_needed = [
    "kidmap", "shapemap",
    "clat", "clon",
    "lflat", "lflon",
    "lfivtx", "lfivty", "lfivtdir"
]

ds = xr.open_dataset(fname, decode_times=True)[vars_needed]
ds = ds.isel(lev=0, ens=0).squeeze()
ds = ds.chunk({"time": 24})

events = []
trajectories = []

for arid in ARID_list:
    event, traj = process_arid(ds, arid)
    if event is None:
        continue

    events.append(event)

    df_traj = traj.to_dataframe().reset_index()
    df_traj["ARID"] = arid
    trajectories.append(df_traj)

events_df = pd.DataFrame(events)
events_df.to_csv(
    f"{path_to_out}/events_task{task_id:03d}.csv",
    index=False
)

traj_df = pd.concat(trajectories, ignore_index=True)

traj_df.to_parquet(
    f"{path_to_out}/traj_task{task_id:03d}.parquet"
)

ds.close()