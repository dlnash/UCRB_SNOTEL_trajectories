# plot_ar_vs_nonar_scatter.py

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec


def plot_ar_vs_nonar_scatter(
    swe_df,
    drought_vals,
    drought_name,
    cmap="viridis",
    save_path=None
):
    """
    Four-panel scatter plot (2x2):

        1) Extreme AR vs Extreme non-AR
        2) Non-Extreme AR vs Non-Extreme non-AR
        3) Total AR vs Total non-AR
        4) All Extreme vs All Non-Extreme

    Color = drought metric (D2+ %)
    """

    # -------------------------------------------------
    # Build precipitation categories
    # -------------------------------------------------

    extreme_AR = swe_df["extreme AR"]
    extreme_nonAR = swe_df["extreme non-AR"]

    nonextreme_AR = swe_df["non-extreme AR"]
    nonextreme_nonAR = swe_df["non-extreme non-AR"]

    total_AR = extreme_AR + nonextreme_AR
    total_nonAR = extreme_nonAR + nonextreme_nonAR

    all_extreme = extreme_AR + extreme_nonAR
    all_nonextreme = nonextreme_AR + nonextreme_nonAR

    panels = [
        {
            "title": "Extreme (AR vs Non-AR)",
            "x": extreme_AR,
            "y": extreme_nonAR,
            "xlabel": "Extreme AR Precipitation (Oct–Mar)",
            "ylabel": "Extreme Non-AR Precipitation (Oct–Mar)",
        },
        {
            "title": "Non-Extreme (AR vs Non-AR)",
            "x": nonextreme_AR,
            "y": nonextreme_nonAR,
            "xlabel": "Non-Extreme AR Precipitation (Oct–Mar)",
            "ylabel": "Non-Extreme Non-AR Precipitation (Oct–Mar)",
        },
        {
            "title": "Total (AR vs Non-AR)",
            "x": total_AR,
            "y": total_nonAR,
            "xlabel": "Total AR Precipitation (Oct–Mar)",
            "ylabel": "Total Non-AR Precipitation (Oct–Mar)",
        },
        {
            "title": "All Extreme vs Non-Extreme",
            "x": all_extreme,
            "y": all_nonextreme,
            "xlabel": "All Extreme Precipitation (Oct–Mar)",
            "ylabel": "All Non-Extreme Precipitation (Oct–Mar)",
        },
    ]

    # -------------------------------------------------
    # Align vals
    # -------------------------------------------------
    # Align years
    common_years = swe_df.index.intersection(drought_vals.index)
    swe_df = swe_df.loc[common_years]
    drought_vals = drought_vals.loc[common_years]
    
    vmin = drought_vals.min()
    vmax = drought_vals.max()

    # -------------------------------------------------
    # Create 2x2 GridSpec + colorbar column
    # -------------------------------------------------

    fig = plt.figure(figsize=(12, 10))

    gs = GridSpec(
        nrows=2,
        ncols=3,
        width_ratios=[1, 1, 0.05],
        wspace=0.2,
        hspace=0.2
    )

    axes = [
        fig.add_subplot(gs[0, 0]),
        fig.add_subplot(gs[0, 1]),
        fig.add_subplot(gs[1, 0]),
        fig.add_subplot(gs[1, 1]),
    ]

    cax = fig.add_subplot(gs[:, 2])

    # -------------------------------------------------
    # Plot Panels
    # -------------------------------------------------

    for ax, panel in zip(axes, panels):

        x = panel["x"].loc[common_years].values
        y = panel["y"].loc[common_years].values
        c = drought_vals.values

        sc = ax.scatter(
            x,
            y,
            c=c,
            cmap=cmap,
            vmin=vmin,
            vmax=vmax,
            s=80,
            edgecolor="k",
            alpha=0.85,
        )

        # 1:1 reference line
        min_val = min(np.min(x), np.min(y))
        max_val = max(np.max(x), np.max(y))

        ax.plot(
            [min_val, max_val],
            [min_val, max_val],
            linestyle="--",
            linewidth=1
        )

        ax.set_title(panel["title"])
        ax.set_xlabel(panel["xlabel"])
        ax.set_ylabel(panel["ylabel"])

        ax.set_aspect("equal", adjustable="box")

        # ax.set_ylim(0, 90)
        # ax.set_xlim(0,90)

    # -------------------------------------------------
    # Colorbar
    # -------------------------------------------------

    cbar = fig.colorbar(sc, cax=cax)
    cbar.set_label(f"{drought_name} (% Area D2+)")

    # -------------------------------------------------
    # Final Layout
    # -------------------------------------------------

    fig.suptitle(
        f"Oct–March Precipitation Partitioning and {drought_name} Response",
        fontsize=16
    )

    fig.subplots_adjust(top=0.92)

    if save_path:
        fig.savefig(save_path, dpi=300, bbox_inches="tight")

    return fig