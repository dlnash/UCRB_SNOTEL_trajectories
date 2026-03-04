# data_loader.py
import pandas as pd
import xarray as xr
from config import USDM_FILE, SWE_FILE

def load_drought_data():
    df = pd.read_csv(USDM_FILE)
    df["MapDate"] = pd.to_datetime(df["MapDate"], format="%Y%m%d")
    return df

def load_swe_data():
    return xr.open_dataset(SWE_FILE)