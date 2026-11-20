# FLUXtrapolation (ET)

Predict hourly evapotranspiration (ET) at eddy-covariance sites the model has never seen.

## Setup

```bash
python -m venv venv_flux_era
source venv_flux_era/bin/activate
pip install -r requirements.txt
```

- `lgbm` also needs `pip install lightgbm`.
- PyTorch runs on CPU by default. For GPU, install the CUDA build of PyTorch.
- On macOS, xgboost needs `brew install libomp`.

## Data

- `data/sites/` has one CSV per site. The file name is the site id.
- One row per hour.
- Target: `ET`.
- `qc_mask`: True if ET was measured, False if it was gap-filled.
- Features: every column except `time`, `year`, `qc_mask`, `tower_lat`, `tower_lon`, `GPP`, `NEE`, `ET`.
  - Meteorology: `TA`, `VPD`, `SW_IN`, potential radiation (`SW_IN_POT`, ...).
  - Satellite: `LST_Day`, `LST_Night`, `EVI`, `NIRv`, `NDWI_SWIR2`.
  - Vegetation type: one-hot `PFT_*` columns.
- Split by site, in [dataloader.py](dataloader.py):
  - Val: the 20 sites in `VAL_SITES`. All hours are kept.
  - Train: all other sites. Hours without a measured ET are dropped, unless the model sets `remove_missing_target = False` (then they are kept with `y = NaN`).

## Run

```bash
python train_model.py --model_name lr   # only if results/lr_trials.csv is missing (skill baseline)
python train_model.py --model_name xgb
python eval.py
```

| Argument | Default | Meaning |
|---|---|---|
| `--model_name` | `lr` | File name in `models/`, without `.py` |
| `--n_iter` | `5` | Number of configs to try |
| `--path` | `data/sites` | Data folder |
| `--rerun` | off | Overwrite existing results |
| `--model_file` | none | Load the model from this `.py` file instead of `models/<model_name>.py` |
| `--out_dir` | `results` | Folder for `<model>_trials.csv` and `<model>_val_predictions.csv`. The `lr` baseline is always read from `results/lr_trials.csv`. |

`train_model.py`:
- samples `n_iter` configs from the model's `PARAM_SPACE`,
- fits each config on train,
- scores each config on val,
- keeps the config with the highest skill.

## Scoring

- RMSE per val site at six scales:
  - `hourly`
  - `weekly`
  - `seasonal`: mean seasonal cycle
  - `anom`: daily anomaly from the seasonal cycle
  - `iav`: yearly anomaly from the site mean
  - `spatial`: site mean, one value per site
- Per scale: median over sites.
- `skill`: mean over scales of `1 - median RMSE / median RMSE of lr`.
  - The `lr` values are read from `results/lr_trials.csv`.
  - 0 means as good as `lr`. Higher is better.
- `skill_q90`: the same with the 90th percentile over sites instead of the median. Logged, not used for selection.
- Also saved: `mean`, `max` and `disc` (max - min) of the hourly site RMSEs.
- Scores use all val hours, including gap-filled ones.
- Early stopping (`eval_set`) only sees measured val hours.

## Outputs

In `results/`:
- `<model>_trials.csv`: one row per config with `skill`, `skill_q90`, `mean`, `max`, `disc`, the median and 90th-percentile RMSE per scale (`<scale>`, `<scale>_q90`), and `params`.
- `<model>_val_predictions.csv`: val predictions of the best config, with `site_id`, `time`, `qc_mask`, `y_true`, `y_pred`.

`python eval.py` prints the best config of every model, sorted by skill.

## Add a model

Create `models/<name>.py` with a `Model` class and a `PARAM_SPACE` dict:

```python
class Model:
    standardize = True  # optional: scale X with a RobustScaler fit on train
    astorch = False     # optional: pass X, y as float32 torch tensors, y of shape (n, 1)
    remove_missing_target = True  # optional: False keeps gap-filled train hours, with y = NaN

    def __init__(self, alpha=1.0):
        self.alpha = alpha

    def fit(self, X, y, eval_set=None, envs=None, times=None, feature_names=None):
        ...
        return self

    def predict(self, X, envs=None, times=None):
        ...  # np.ndarray of shape (n,)


PARAM_SPACE = {
    'alpha': ('loguniform', 1e-3, 1e2),
    'n_epochs': 100,
}
```

- `fit` must take `X` and `y`. The other arguments are optional. They are passed only if `fit` has them:
  - `eval_set`: `[(X_val, y_val)]` with the measured val hours, for early stopping.
  - `envs`: site id of each train row.
  - `times`: `np.datetime64` timestamp of each train row.
  - `feature_names`: list of feature names.
- `predict` must take `X`. It also gets `envs` and `times` of the val rows (no labels), only if it has them.
- `PARAM_SPACE` maps each `__init__` argument to:
  - a fixed value, or
  - `('uniform', lo, hi)`, `('loguniform', lo, hi)`, `('int', lo, hi)` (inclusive), or `('choice', [options])`.
- If `PARAM_SPACE` has no distributions, only one config is run.
- Run it with `python train_model.py --model_name <name>`.

## Existing models

| Name | Model |
|---|---|
| `lr` | Linear regression |
| `constant` | Predicts the training mean |
| `ridge` | Ridge regression |
| `robust_lr` | Huber regression |
| `xgb` | XGBoost |
| `lgbm` | LightGBM |
| `mlp` | Multi-layer perceptron (PyTorch) |
| `gdro` | Group DRO: minimizes the worst site loss (PyTorch) |
| `coral` | CORAL: aligns feature statistics across sites (PyTorch) |
| `mmd` | MMD: aligns feature distributions across sites (PyTorch) |

`models/lstm.py` does not run yet.
