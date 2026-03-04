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

    return drought_wy, drought_melt, drought_diff


# ---------------- SWE Processing ---------------- #

def normalize_swe(ds):

    snow_mask = ds["time"].dt.month.isin(SNOW_MONTHS)
    SWE = ds["SWE"].where(ds["SWE"] > 0)
    SWE = SWE.where(snow_mask)

    annual = SWE.groupby("water_year").sum(dim="time")
    climatology = annual.mean(dim="water_year")

    return SWE / climatology


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