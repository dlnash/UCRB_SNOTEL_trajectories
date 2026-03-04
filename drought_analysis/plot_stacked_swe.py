# plot_stacked_swe.py

import matplotlib.pyplot as plt
import numpy as np
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