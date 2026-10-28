# plot_ar_vs_nonar_scatter.py

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import matplotlib.patheffects as path_effects

def plot_ar_vs_nonar_scatter(
    swe_df,
    mean_drought_vals,
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

    Color = drought difference (end of WY - start of WY) (positive value indicates increase in drought severity)

    Size = average drought % during the WY
    """

    # -------------------------------------------------
    # Build SWE categories
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
            "xlabel": "Extreme AR SWE (Oct–Mar)",
            "ylabel": "Extreme Non-AR SWE (Oct–Mar)",
        },
        {
            "title": "Non-Extreme (AR vs Non-AR)",
            "x": nonextreme_AR,
            "y": nonextreme_nonAR,
            "xlabel": "Non-Extreme AR SWE (Oct–Mar)",
            "ylabel": "Non-Extreme Non-AR SWE (Oct–Mar)",
        },
        {
            "title": "Total (AR vs Non-AR)",
            "x": total_AR,
            "y": total_nonAR,
            "xlabel": "Total AR SWE (Oct–Mar)",
            "ylabel": "Total Non-AR SWE (Oct–Mar)",
        },
        {
            "title": "All Extreme vs Non-Extreme",
            "x": all_extreme,
            "y": all_nonextreme,
            "xlabel": "All Extreme SWE (Oct–Mar)",
            "ylabel": "All Non-Extreme SWE (Oct–Mar)",
        },
    ]

    # -------------------------------------------------
    # Align vals
    # -------------------------------------------------
    # Align years
    common_years = swe_df.index.intersection(drought_vals.index)
    swe_df = swe_df.loc[common_years]
    drought_vals = drought_vals.loc[common_years]
    mean_drought_vals = mean_drought_vals.loc[common_years]
    
    vmin = drought_vals.min()
    vmax = drought_vals.max()

    # -------------------------------------------------
    # Create 2x2 GridSpec + colorbar column
    # -------------------------------------------------

    fig = plt.figure(figsize=(11,9.5))

    gs = GridSpec(
        nrows=2,
        ncols=3,
        width_ratios=[1.05, 1, 0.05],
        wspace=0.1,
        hspace=0.2
    )

    axes = [
        fig.add_subplot(gs[0, 1]),
        fig.add_subplot(gs[0, 0]),
        fig.add_subplot(gs[1, 0]),
        fig.add_subplot(gs[1, 1]),
    ]

    cax = fig.add_subplot(gs[0, 2])

    # -------------------------------------------------
    # Plot Panels
    # -------------------------------------------------

    for ax, panel in zip(axes, panels):

        x = panel["x"].loc[common_years].values
        y = panel["y"].loc[common_years].values
        c = drought_vals.values
        s = mean_drought_vals.values

        sc = ax.scatter(
            x,
            y,
            c=c,
            cmap=cmap,
            vmin=vmin,
            vmax=vmax,
            s=s*15,
            edgecolor='black',
            alpha=0.75,
        )

        # Highlight years with red outlines
        highlight_years = [2005, 2008, 2013, 2015, 2019, 2023]
        
        highlight_mask = np.isin(common_years, highlight_years)
        
        ax.scatter(
            x[highlight_mask],
            y[highlight_mask],
            facecolors='none',     # hollow circle
            edgecolors='red',      # red outline
            s=s[highlight_mask]*16,  # slightly larger than base points
            linewidths=1.5,
            zorder=3               # draw on top
        )
        
        for year in highlight_years:
            if year in common_years:

                x_pt = panel["x"].loc[year]
                y_pt = panel["y"].loc[year]
        
                ann = ax.annotate(
                    str(year)[2:],
                    xy=(x_pt, y_pt),
                    xytext=(-6, -3),  # offset text
                    textcoords="offset points",
                    fontsize=9,
                    weight="bold"
                )
                ann.set_path_effects([path_effects.withStroke(linewidth=1, foreground="white")])

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
        f"Oct–March SWE and {drought_name}",
        fontsize=16
    )

    fig.subplots_adjust(top=0.92)

    if save_path:
        fig.savefig(save_path, dpi=300, bbox_inches="tight")

    return fig