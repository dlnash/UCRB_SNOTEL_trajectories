# plot_correlations.py
import os
import matplotlib.pyplot as plt
import numpy as np
from stats_utils import compute_stats
from config import COLORS, prec_metrics


def plot_panel(ax, x, y, xlbl, ylbl):

    stats_dict = compute_stats(x, y)

    ax.scatter(x, y)

    slope = stats_dict["Slope"]
    intercept = np.mean(y) - slope*np.mean(x)

    x_line = np.linspace(min(x), max(x), 100)
    ax.plot(x_line, slope*x_line + intercept)

    textstr = (
        f"ρ = {stats_dict['Spearman_rho']:.2f}\n"
        f"R² = {stats_dict['Linear_R2']:.2f}"
    )

    ax.text(0.05, 0.95, textstr,
            transform=ax.transAxes,
            verticalalignment='top')

    ax.set_xlabel(xlbl)
    ax.set_ylabel(ylbl)

def plot_single_panel_progressive(
    swe_df,
    drought_vals,
    drought_name,
    save_figures=False,
    out_dir="figs/"
):

    
    if save_figures and not os.path.exists(out_dir):
        os.makedirs(out_dir)

    for i in range(len(prec_metrics)):

        fig, ax = plt.subplots(figsize=(8,6))

        for j in range(i+1):

            metric = prec_metrics[j]
            color = COLORS[j]

            x = swe_df[metric].values
            
            # Align lagged case
            if "Lagged" in drought_name:
                x = x[:-1]
                y = drought_vals
            else:
                y = drought_vals

            stats_dict = compute_stats(x, y)

            slope = stats_dict["Slope"]
            intercept = np.mean(y) - slope*np.mean(x)
        
            x_line = np.linspace(min(x), max(x), 100)
            ax.plot(x_line, slope*x_line + intercept, color=color)
        
            rhostr = f"ρ = {stats_dict['Spearman_rho']:.2f}"
            rsqstr = f"R² = {stats_dict['Linear_R2']:.2f}"

            # Scatter
            label=f"{metric} ({rsqstr})"
            ax.scatter(x, y, color=color, label=label, alpha=0.85)

        ax.set_xlabel("Normalized SWE (Oct–Mar)")
        ax.set_ylabel("Percent Area in D2+ (%)")
        ax.set_title(f"{drought_name}")

        ax.legend()
        plt.tight_layout()

        # Save progressive figures
        if save_figures:
            fname = f"{out_dir}{drought_name.replace(' ', '_')}_step_{i+1}.png"
            fig.savefig(fname, dpi=300)

        plt.show()