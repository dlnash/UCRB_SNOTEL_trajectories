# main.py

import argparse
import pandas as pd

from data_loader import load_drought_data, load_swe_data
from processing import (
    process_drought,
    normalize_swe,
    compute_swe_categories,
)
from stats_utils import build_stats_table
from plot_stacked_swe import plot_stacked
from plot_correlations import plot_panel
from plot_ar_vs_nonar_scatter import plot_ar_vs_nonar_scatter

import matplotlib.pyplot as plt


# -------------------------------
# Core workflow
# -------------------------------

def run_analysis(make_stacked=True,
                 make_correlations=True,
                 make_scatter=False,
                 save_figures=False,
                 output_stats=False):

    print("Loading data...")
    drought_df = load_drought_data()
    ds = load_swe_data()

    print("Processing drought metrics...")
    drought_wy, drought_melt, drought_diff = process_drought(drought_df)

    print("Processing SWE...")
    SWE_norm = normalize_swe(ds)
    swe_categories = compute_swe_categories(ds, SWE_norm)

    # Convert SWE dict to pandas DataFrame
    swe_df = pd.DataFrame({
        k: v.values
        for k, v in swe_categories.items()
    }, index=list(swe_categories.values())[0]["water_year"].values)

    swe_df = swe_df.sort_index()

    # Align years
    common_years = swe_df.index.intersection(drought_wy.index)
    swe_df = swe_df.loc[common_years]
    drought_wy = drought_wy.loc[common_years]

    # -------------------------------
    # Stacked Bar Plot
    # -------------------------------
    if make_stacked:
        print("Creating stacked SWE plot...")
        fig = plot_stacked(swe_df, drought_wy)

        if save_figures:
            fig.savefig("figs/stacked_swe.png", dpi=300)

        plt.show()
        
    # -------------------------------
    # AR vs. non-AR scatter plot
    # -------------------------------
    if make_scatter:
        drought_dict = {
            "Same-Year Drought": drought_wy,
            "Lagged Melt-Season Drought": drought_melt,
            "Drought Difference": drought_diff
        }

        for drought_name, drought_vals in drought_dict.items():
            if "Difference" in drought_name:
                cmap = "BrBG_r"
            else:
                cmap = "viridis"
        
            print("Creating AR vs Non-AR scatter plot...")
            fig = plot_ar_vs_nonar_scatter(
                swe_df,
                drought_vals,
                drought_name,
                cmap=cmap,
                save_path="figs/ar_vs_nonar_scatter_" + drought_name.replace(" ", "_") + ".png" if save_figures else None
            )
            plt.show()

    # -------------------------------
    # Correlation Panels
    # -------------------------------
    if make_correlations:

        print("Creating correlation plots...")

        swe_dict = {
            "Extreme AR": swe_df["extreme AR"].values,
            "Extreme Non-AR": swe_df["extreme non-AR"].values,
            "Total AR": (
                swe_df["extreme AR"].values +
                swe_df["non-extreme AR"].values
            ),
            "Total Non-AR": (
                swe_df["extreme non-AR"].values +
                swe_df["non-extreme non-AR"].values
            ),
        }

        drought_dict = {
            "Same-Year Drought": drought_wy.values,
            "Lagged Melt-Season Drought": drought_melt.values,
            "Drought Difference": drought_diff.values
        }

        for drought_name, drought_vals in drought_dict.items():

            fig, axes = plt.subplots(2, 2, figsize=(12, 10))
            axes = axes.flatten()

            for i, (swe_name, swe_vals) in enumerate(swe_dict.items()):

                if "Lagged" in drought_name:
                    x = swe_vals[:-1]
                    y = drought_vals
                else:
                    x = swe_vals
                    y = drought_vals

                plot_panel(
                    axes[i],
                    x,
                    y,
                    f"Normalized {swe_name} SWE",
                    "Percent Area in D2+ (%)"
                )

                axes[i].set_title(swe_name)

            fig.suptitle(drought_name)

            if save_figures:
                fname = "figs/" + drought_name.replace(" ", "_") + ".png"
                fig.savefig(fname, dpi=300)

            plt.tight_layout()
            plt.show()

    # -------------------------------
    # Statistics Table
    # -------------------------------
    if output_stats:

        print("Building statistics table...")

        stats_df = build_stats_table(swe_dict, drought_dict)

        print(stats_df)

        if save_figures:
            stats_df.to_csv("correlation_statistics.csv", index=False)

    print("Done.")

# -------------------------------
# Command Line Interface
# -------------------------------

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Run SWE–Drought Analysis"
    )

    parser.add_argument("--no-stacked",
                        action="store_true",
                        help="Skip stacked SWE plot")

    parser.add_argument("--no-correlations",
                        action="store_true",
                        help="Skip correlation plots")

    parser.add_argument("--scatter",
                    action="store_true",
                    help="Create AR vs non-AR precipitation scatter plot")

    parser.add_argument("--save",
                        action="store_true",
                        help="Save figures to disk")

    parser.add_argument("--stats",
                        action="store_true",
                        help="Output statistics table")

    args = parser.parse_args()

    run_analysis(
        make_stacked=not args.no_stacked,
        make_correlations=not args.no_correlations,
        make_scatter=args.scatter,
        save_figures=args.save,
        output_stats=args.stats,
    )