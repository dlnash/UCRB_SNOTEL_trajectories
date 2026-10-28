# processing.py
import numpy as np
import pandas as pd
from config import SNOW_MONTHS, MELT_MONTHS


def add_water_year(df, date_col="MapDate"):
    df = df.copy()
    df["water_year"] = df[date_col].dt.year
    df.loc[df[date_col].dt.month >= 10, "water_year"] += 1
    return df


# ---------------- Drought Processing ---------------- #
def calculate_drought_breaks(df):

    # Boolean flags
    df['below_thresh'] = df['D2_D4_mean'] < 30.
    df['above_thresh'] = df['D2_D4_mean'] >= 30.
    
    # Identify transitions from drought → non-drought
    df['transition'] = (df['above_thresh'].shift(1) == True) & (df['below_thresh'] == True)
    
    # Find all candidate break indices
    candidate_idx = df.index[df['transition']].tolist()
    
    # Confirm persistence ≥ 6 months
    drought_breaks = []
    
    for idx in candidate_idx:
        # Look forward 6 months (including current)
        window = df.loc[idx: idx+5, 'below_thresh']
        # print(window)
        
        if len(window) == 6 and window.all():
            drought_breaks.append(idx)
    
    # Extract event dataframe
    df_breaks = df.loc[drought_breaks].copy()

    return df_breaks
    
def process_drought(df):
    """
    Processes drought metrics and returns:

    - drought_wy       : Annual mean D2+ area
    - drought_melt     : Apr–Sep mean D2+ area
    - drought_diff     : End-of-WY minus Beginning-of-WY D2+ area
    """

    df = df.copy()

    # Compute D2+ area
    df["D2_D4_total"] = df["D2"] + df["D3"] + df["D4"]

    # Add water year
    df = add_water_year(df)

    # Ensure chronological order within WY
    df = df.sort_values("MapDate")

    # -------------------------------------------------
    # 1) Annual mean drought
    # -------------------------------------------------

    drought_wy = (
        df.groupby("water_year")["D2_D4_total"]
        .mean()
    )

    # -------------------------------------------------
    # 2) Melt-season (Apr–Sep) mean drought
    # -------------------------------------------------

    melt_mask = df["MapDate"].dt.month.isin(MELT_MONTHS)

    drought_melt = (
        df[melt_mask]
        .groupby("water_year")["D2_D4_total"]
        .mean()
        .rename("D2_melt_mean")
    )

    # -------------------------------------------------
    # 3) Drought difference (end - start of WY)
    # -------------------------------------------------

    wy_start_end = (
        df.groupby("water_year")
        .agg(
            D2_start=("D2_D4_total", "first"),
            D2_end=("D2_D4_total", "last")
        )
    )

    drought_diff = (
        wy_start_end["D2_end"] - wy_start_end["D2_start"]
    ).rename("D2_change")

    # -------------------------------------------------
    # 4) Monthly Mean Drought and Drought Breaks
    # -------------------------------------------------
    month_df = df.groupby(pd.PeriodIndex(df['MapDate'], freq="M"))['D2_D4_total'].mean()
    month_df = month_df.to_frame(name="D2_D4_mean").reset_index()
    month_df['MapDate'] = month_df['MapDate'].dt.to_timestamp()
    drought_month = month_df
    drought_breaks = calculate_drought_breaks(month_df)

    
    return drought_wy, drought_melt, drought_diff, drought_month, drought_breaks


# ---------------- SWE Processing ---------------- #

def normalize_swe(ds):

    snow_mask = ds["time"].dt.month.isin(SNOW_MONTHS)
    SWE = ds["SWE"].where(ds["SWE"] > 0)
    SWE = SWE.where(snow_mask)

    annual = SWE.groupby("water_year").sum(dim="time")
    climatology = annual.mean(dim="water_year")

    return SWE / climatology

def subset_swe_percent_of_median_peak(ds):

    snow_mask = ds["time"].dt.month.isin(SNOW_MONTHS)
    SWE = ds["SWE_norm"].where(ds["SWE_norm"] > 0)
    SWE = SWE.where(snow_mask)

    return SWE


def compute_swe_categories(ds, SWE_norm):

    AR = ds["AR"].notnull().astype(int)
    extreme = ds["extreme"].fillna(0).astype(int)

    categories = {
        "non-extreme non-AR": SWE_norm.where((extreme==0)&(AR==0)),
        "extreme non-AR":     SWE_norm.where((extreme==1)&(AR==0)),
        "non-extreme AR":     SWE_norm.where((extreme==0)&(AR==1)),
        "extreme AR":         SWE_norm.where((extreme==1)&(AR==1)),
    }

    def seasonal_sum(da):
        return (
            da.groupby("water_year")
              .sum(dim="time")
              .sum(dim="station")
        )

    return {k: seasonal_sum(v) for k,v in categories.items()}