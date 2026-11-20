"""Val scores. Run directly to print the best trial (highest skill) of every model in results/."""

import glob
import os
import numpy as np
import pandas as pd

from utils.aggregation import AGGREGATIONS

SCALES = ['hourly', 'weekly', 'seasonal', 'anom', 'iav', 'spatial']


def evaluate(y, pred, envs, times, base=None):
    """Score val predictions on all rows.

    Per scale: RMSE per site, then the median (<scale>) and 90th percentile
    (<scale>_q90) over sites.
    skill / skill_q90: mean over scales of 1 - RMSE / base RMSE (0 without base).
    mean, max, disc: of the hourly site RMSEs.
    """
    df = pd.DataFrame({'env': envs, 'time': times, 'y_true': y, 'y_pred': pred})
    rmse = {}
    for scale in SCALES:
        agg = AGGREGATIONS[scale](df)
        rmse[scale] = ((agg['y_pred'] - agg['y_true']) ** 2).groupby(agg['env']).mean() ** 0.5
    med = {s: r.median() for s, r in rmse.items()}
    q90 = {f'{s}_q90': r.quantile(0.9) for s, r in rmse.items()}
    base = {**med, **q90} if base is None else base
    h = rmse['hourly']
    return {'skill': float(np.nanmean([1 - med[s] / base[s] for s in med])),
            'skill_q90': float(np.nanmean([1 - q90[s] / base[s] for s in q90])),
            'mean': h.mean(), 'max': h.max(), 'disc': h.max() - h.min(), **med, **q90}


if __name__ == "__main__":
    best = {}
    for f in sorted(glob.glob('results/*_trials.csv')):
        trials = pd.read_csv(f)
        best[os.path.basename(f).removesuffix('_trials.csv')] = trials.loc[trials['skill'].idxmax()]

    pd.set_option('display.max_colwidth', None)
    print(pd.DataFrame(best).T.sort_values('skill', ascending=False).to_string())
