# plot_stacked_swe.py

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd
from matplotlib.patches import Patch
from config import COLORS


def plot_stacked(df_plot, drought_plot):

    fig, ax1 = plt.subplots(figsize=(12, 6))

    bottom = np.zeros(len(df_plot))
    bar_handles = []

    # -----------------------------
    # Stacked bars
    # -----------------------------
    for i, col in enumerate(df_plot.columns):
        bars = ax1.bar(
            df_plot.index,
            df_plot[col],
            bottom=bottom,
            color=COLORS[i],
        )

        # Create legend patch manually for consistency
        bar_handles.append(
            Patch(facecolor=COLORS[i], label=col)
        )

        bottom += df_plot[col].values

    ax1.set_xlabel("Water Year")
    ax1.set_ylabel("Normalized Seasonal SWE")

    # -----------------------------
    # Drought shading
    # -----------------------------
    ax2 = ax1.twinx()

    drought_poly = ax2.fill_between(
        drought_plot.index,
        0,
        drought_plot.values,
        color="#c49a6c",
        alpha=0.25,
    )

    ax2.set_ylabel("% Area in D2–D4")

    # -----------------------------
    # Combined legend
    # -----------------------------

    drought_patch = Patch(
        facecolor="#c49a6c",
        alpha=0.25,
        label="Drought Severity (D2–D4)"
    )

    all_handles = bar_handles + [drought_patch]

    ax1.legend(
        handles=all_handles,
        loc="upper left",
        frameon=False
    )

    plt.tight_layout()

    return fig

def plot_stacked_drought_below(df_plot, drought_plot, drought_breaks):

    df_plot = df_plot.copy()
    df_plot.index = pd.to_datetime(df_plot.index.astype(str) + "-09-30")

    # --- Figure layout ---
    fig = plt.figure(figsize=(8,8), dpi=300)
    
    gs = fig.add_gridspec(
        nrows=2,
        ncols=1,
        width_ratios=[1],
        height_ratios=[1,1],
        hspace=0.05,
        wspace=0.05
    )

    # --- Map axes ---
    ax1 = fig.add_subplot(gs[0,0])
    ax2 = fig.add_subplot(gs[1,0], sharex=ax1)

    # -----------------------------
    # Stacked bars
    # -----------------------------
    bottom = np.zeros(len(df_plot))
    bar_handles = []
    
    for i, col in enumerate(df_plot.columns):
        bars = ax1.bar(
            df_plot.index,
            df_plot[col],
            bottom=bottom,
            color=COLORS[i],
            width=300,   # days
        )

        # Create legend patch manually for consistency
        bar_handles.append(
            Patch(facecolor=COLORS[i], label=col)
        )

        bottom += df_plot[col].values

    ax1.set_ylabel("Cumulative SWE Gain (% Median Peak SWE)")
    ax1.set_xlim(pd.to_datetime('1999-10-01'), pd.to_datetime('2026-10-01'))
    ax1.tick_params(labelbottom=False)

    # -----------------------------
    # Legend
    # -----------------------------
    ax1.legend(
        handles=bar_handles,
        loc="upper left",
        frameon=False
    )

    # -----------------------------
    # Drought time series
    # -----------------------------
    # Main line
    ax2.plot(drought_plot['MapDate'], drought_plot['D2_D4_mean'], color='black', linewidth=1.5)
    
    # Fill to zero
    ax2.fill_between(
        drought_plot['MapDate'],
        drought_plot['D2_D4_mean'],
        0,
        where=(drought_plot['D2_D4_mean'] >= 0),
        interpolate=True,
        color='black'
    )
    
    # Reference line at -2
    ax2.axhline(30., color='red', linestyle='--', linewidth=1)
    
    # Drought break markers (triangles at -2 line)
    ax2.plot(
        drought_breaks['MapDate'],
        [30]*len(drought_breaks),
        '^',
        color='red',
        markersize=8,
        label='Drought Break'
    )

    # -----------------------------
    # X-ticks
    # -----------------------------
    years = pd.date_range(
        "2000-10-01",
        "2025-10-01",
        freq="YS-OCT"
    )
    
    ax2.set_xticks(years)
    
    labels = [
        d.strftime("%Y") if i % 2 == 0 else ""
        for i, d in enumerate(years)
    ]
    
    ax2.set_xticklabels(labels)
    
    # Formatting
    ax2.set_ylabel('U.S. Drought Monitor (% Area in D2–D4)')
    ax2.grid(True, alpha=0.3)
    ax2.legend()
    ax2.set_xlim(pd.to_datetime('1999-10-01'), pd.to_datetime('2026-10-01'))


    plt.tight_layout()

    return fig