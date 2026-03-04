# plot_correlations.py
import matplotlib.pyplot as plt
import numpy as np
from stats_utils import compute_stats


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