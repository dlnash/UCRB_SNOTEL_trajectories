import pandas as pd
import glob

events = pd.concat(
    [pd.read_csv(f) for f in glob.glob("../out/events_task*.csv")],
    ignore_index=True
)

events.to_csv("../out/events_all.csv", index=False)

traj = pd.concat(
    [pd.read_parquet(f) for f in glob.glob("../out/traj_task*.parquet")],
    ignore_index=True
)

traj.to_parquet("../out/traj_all.parquet")