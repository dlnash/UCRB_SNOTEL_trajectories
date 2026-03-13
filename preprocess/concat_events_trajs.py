import pandas as pd
import glob
percentile=0
path=f"../out/trajs_{percentile}-percentile/"

events = pd.concat(
    [pd.read_csv(f) for f in glob.glob(path+"events_task*.csv")],
    ignore_index=True
)

events.to_csv(f"../out/events_all_{percentile}-percentile.csv", index=False)

traj = pd.concat(
    [pd.read_parquet(f) for f in glob.glob(path+"traj_task*.parquet")],
    ignore_index=True
)

traj.to_parquet(f"../out/traj_all_{percentile}-percentile.parquet")