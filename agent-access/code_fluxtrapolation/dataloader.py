import os
import numpy as np
import pandas as pd
import torch

from sklearn.preprocessing import RobustScaler

TARGET = 'ET'
# Validation sites. Every other site in the data folder is used for training.
VAL_SITES = ['US-Snf', 'US-GLE', 'US-CF2', 'FI-Let', 'CZ-Lnz', 'US-Rls', 'UK-AMo', 'FR-Gri', 'US-xTR', 'US-ALQ', 'CA-ER1', 'US-xBR', 'FI-Hyy', 'IE-Cra', 'DE-Obe', 'AU-War', 'US-RGB', 'CH-Cha', 'US-Syv', 'US-UMB']
NON_FEATURES = ['time', 'year', 'site_id', 'qc_mask', 'tower_lat', 'tower_lon', 'GPP', 'NEE', 'ET']


def load_data(path='data/sites', remove_missing_target=False, keep_lonlat=False,
              standardize=False, astorch=False):
    """Load every site CSV in `path` and split into train/val by site.

    Train: the target is NaN where it is not measured (qc_mask != 1); with
    remove_missing_target those rows are dropped.
    Val: all rows, with gap-filled targets; `qc_val` marks the measured ones.
    keep_lonlat adds tower_lat and tower_lon to the features.
    standardize fits a RobustScaler on xtrain. astorch turns x and y into
    float32 tensors (y of shape (n, 1)).
    Returns (xtrain, ytrain, envs_train, times_train),
    (xval, yval, envs_val, times_val, qc_val), feature_cols,
    where envs are site ids and times are np.datetime64.
    """
    df = pd.concat([pd.read_csv(os.path.join(path, f)).assign(site_id=f.removesuffix('.csv'))
                    for f in sorted(os.listdir(path)) if f.endswith('.csv')],
                   ignore_index=True)

    kept = ['tower_lat', 'tower_lon'] if keep_lonlat else []
    features = [c for c in df.columns if c not in NON_FEATURES or c in kept]
    assert df[features].notna().all().all(), "Missing values in features"
    missing = set(VAL_SITES) - set(df['site_id'])
    assert not missing, f"Val sites missing from {path}: {missing}"

    is_val = df['site_id'].isin(VAL_SITES)
    train, val = df[~is_val].copy(), df[is_val]
    train.loc[train['qc_mask'] != 1, TARGET] = np.nan
    if remove_missing_target:
        train = train.dropna(subset=[TARGET])

    (xtrain, ytrain, envs_train), (xval, yval, envs_val) = [
        (d[features].to_numpy(np.float64), d[TARGET].to_numpy(np.float64), d['site_id'].to_numpy())
        for d in (train, val)
    ]
    times_train, times_val = (pd.to_datetime(d['time']).to_numpy() for d in (train, val))
    assert val.loc[val['qc_mask'] == 1, TARGET].notna().all(), "NaN target where qc_mask == 1"
    qc_val = (val['qc_mask'] == 1).to_numpy()

    if standardize:
        scaler = RobustScaler().fit(xtrain)
        xtrain, xval = scaler.transform(xtrain), scaler.transform(xval)
    if astorch:
        xtrain, xval = (torch.tensor(x, dtype=torch.float32) for x in (xtrain, xval))
        ytrain, yval = (torch.tensor(y, dtype=torch.float32).view(-1, 1) for y in (ytrain, yval))

    return (xtrain, ytrain, envs_train, times_train), (xval, yval, envs_val, times_val, qc_val), features
