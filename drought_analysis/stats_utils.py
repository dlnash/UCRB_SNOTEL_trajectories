# stats_utils.py
import numpy as np
import pandas as pd
from scipy import stats


def compute_stats(x, y):

    mask = np.isfinite(x) & np.isfinite(y)
    x = x[mask]
    y = y[mask]

    rho, p_rho = stats.spearmanr(x, y)
    slope, intercept, r_value, p_lin, _ = stats.linregress(x, y)

    return {
        "Spearman_rho": rho,
        "Spearman_p": p_rho,
        "Linear_R2": r_value**2,
        "Linear_p": p_lin,
        "Slope": slope,
    }


def build_stats_table(swe_dict, drought_dict):

    results = []

    for dname, dvals in drought_dict.items():
        for sname, svals in swe_dict.items():

            if "Lagged" in dname:
                x = svals[:-1]
                y = dvals
            else:
                x = svals
                y = dvals

            stats_dict = compute_stats(x, y)
            stats_dict.update({
                "Drought Metric": dname,
                "SWE Metric": sname
            })

            results.append(stats_dict)

    return pd.DataFrame(results).sort_values("Linear_R2", ascending=False)