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
percentile = 0

# Load ARIDs from CSV
arid_df = pd.read_csv(
    f"{path_to_out}unique_ARIDs_{percentile}-percentile.csv",
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
    times = ds_life.time.values

    clat_list = []
    clon_list = []

    for t in times:
        tmp = ds_life.sel(time=t)

        # Find ID for THIS timestep
        new_id = (
            tmp.shapemap
            .where(tmp.kidmap == arid)
            .max(skipna=True)
            .compute()
        )

        if np.isnan(new_id):
            clat_list.append(np.nan)
            clon_list.append(np.nan)
            continue

        idx = int(new_id) - 1

        clat_list.append(tmp.clat.isel(lat=idx).compute().item())
        clon_list.append(tmp.clon.isel(lat=idx).compute().item())

    traj = xr.Dataset(
        data_vars=dict(
            clat=("time", clat_list),
            clon=("time", clon_list),
        ),
        coords=dict(time=times)
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
    f"{path_to_out}/trajs_{percentile}-percentile/events_task{task_id:03d}.csv",
    index=False
)

traj_df = pd.concat(trajectories, ignore_index=True)

traj_df.to_parquet(
    f"{path_to_out}/trajs_{percentile}-percentile/traj_task{task_id:03d}.parquet"
)

ds.close()