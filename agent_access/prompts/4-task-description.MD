# Task description (v0.1)
## Overview

We want to predict hourly **evapotranspiration (ET)** at places where nothing has been measured.

Ecosystem fluxes such as ET are measured directly only at a few hundred eddy-covariance towers worldwide (FLUXNET). To get global estimates, we train on the towers we have and predict from covariates that are available everywhere: meteorology, satellite indices and vegetation type. This is called *upscaling*. It is hard because the towers we predict for differ systematically from the ones we train on, both in their covariates and in the relation between covariates and flux.

Your task is to write a model that is trained on one set of sites and predicts ET at **other, unseen sites**; we care about typical and tail performance. Validation sites are never seen during training, so a good model has to generalize across sites, not fit the training sites well.

This prompt comes with a research direction. Implement that direction inside the interface described below.

**Do not run any code.** Output code only. It will be run and scored by an automated harness.

## Deliverables

Output exactly the following, in this order:

1. **Method summary.** At most 2 sentences on what the model does and why it should generalize to unseen sites.
2. **Model file** `models/{MODEL_NAME}.py`, as one ```python block. `{MODEL_NAME}` is a valid Python identifier (letters, digits, underscores; no hyphens). Specify the file name. Then, the file must define:
   - `class Model` with:
     - `__init__(self, ...)`: every tunable hyperparameter is a keyword argument with a sensible default.
     - `fit(self, X, y, eval_set=None, envs=None, times=None, feature_names=None) -> self`. The four optional arguments are passed **only if they appear in your signature**, so include only the ones you use.
     - `predict(self, X, envs=None, times=None) -> np.ndarray` of shape `(n_samples,)`, no NaNs. `envs` and `times` are optional in the same way: they are passed only if they appear in your signature.
     - Optional class attributes `standardize`, `astorch` (both default `False`) and `remove_missing_target` (default `True`); see *Data*.
   - A module-level dict `PARAM_SPACE` (see *Search space*).

## Data

**Rows are hourly observations.** Each site is one *environment*. There are about 147 training sites and 20 validation sites, with about **2.1 million** training rows (2,110,614 measured hours; **5,505,528** with `remove_missing_target = False`, see below) and **815,304** validation rows, of which **284,746** have measured ET.

Raw data (one CSV per site) looks like this:

```csv
time,TA,VPD,SW_IN,SW_IN_POT,SW_IN_POT_daily,dSW_IN_POT,dSW_IN_POT_daily,LST_Day,LST_Night,EVI,NIRv,NDWI_SWIR2,PFT_CRO,PFT_CSH,PFT_CVM,PFT_DBF,PFT_DNF,PFT_EBF,PFT_ENF,PFT_GRA,PFT_MF,PFT_OSH,PFT_SAV,PFT_WAT,PFT_WET,PFT_WSA,NEE,GPP,ET,qc_mask,tower_lat,tower_lon,year
2020-01-01 00:00:00,17.7195,0.0,0.0,0.0,517.6262004166666,0.0,-0.4147244791666367,308.463609028477,287.8889552451521,0.43835797905921936,0.18977370858192444,0.12060628086328506,False,False,False,False,False,False,False,True,False,False,False,False,False,False,8.892710000000001,-0.31505600000000006,0.04777345304852437,True,-35.9244,-61.1855,2020
2020-01-01 01:00:00,17.1045,0.0,0.0,0.0,517.6262004166666,0.0,-0.4147244791666367,308.463609028477,287.8889552451521,0.43835797905921936,0.18977370858192444,0.12060628086328506,False,False,False,False,False,False,False,True,False,False,False,False,False,False,8.60604,-0.169605,0.033886966750913766,True,-35.9244,-61.1855,2020
2020-01-01 02:00:00,16.7295,0.0,0.0,0.0,517.6262004166666,0.0,-0.4147244791666367,308.463609028477,287.8889552451521,0.43835797905921936,0.18977370858192444,0.12060628086328506,False,False,False,False,False,False,False,True,False,False,False,False,False,False,8.367014999999999,-0.016132099999999996,0.028599862124126157,True,-35.9244,-61.1855,2020
```

**What your model receives.** `X` has 26 columns in this order:

| Columns | Units | Notes |
|---|---|---|
| `TA` | °C | air temperature |
| `VPD` | hPa | vapour pressure deficit |
| `SW_IN` | W m⁻² | incoming shortwave radiation |
| `SW_IN_POT`, `SW_IN_POT_daily` | W m⁻² | potential (top-of-atmosphere) SW radiation, hourly and daily mean |
| `dSW_IN_POT`, `dSW_IN_POT_daily` | W m⁻² h⁻¹, W m⁻² d⁻¹ | change in potential SW radiation (encodes time of day and season) |
| `LST_Day`, `LST_Night` | K | satellite land surface temperature |
| `EVI`, `NIRv`, `NDWI_SWIR2` | – | satellite vegetation and water indices |
| `PFT_CRO, PFT_CSH, PFT_CVM, PFT_DBF, PFT_DNF, PFT_EBF, PFT_ENF, PFT_GRA, PFT_MF, PFT_OSH, PFT_SAV, PFT_WAT, PFT_WET, PFT_WSA` | 0/1 | plant functional type, one-hot, constant within a site |

The satellite variables change slowly and repeat across the hours of a day.

The arguments are:
- `X`: `np.ndarray`, float64, shape `(n, 26)`, unscaled. It contains **no NaNs**. `time`, `year`, `tower_lat`, `tower_lon`, `qc_mask`, `site_id` and the other fluxes are removed.
- `y`: `np.ndarray`, float64, shape `(n,)`. This is ET in mm h⁻¹. By default, rows with gap-filled (low-quality) ET have already been dropped, so `y` has no NaNs (see `remove_missing_target` below).
- `envs`: `np.ndarray` of site-ID strings (e.g. `'US-Ha1'`), aligned with the rows of `X`.
- `times`: `np.ndarray` of `np.datetime64` timestamps (hourly), aligned with the rows of `X`.
- `eval_set`: `[(X_val, y_val)]`, the hours of the 20 validation sites where ET was **measured** (284,746 rows), in the same format as `X`, `y`. Use it only for early stopping. It comes **without** `envs` or `times`, so any early-stopping predictions you make on it are context-free (no site grouping, no temporal smoothing).
- `feature_names`: list of the 26 column names above.

In `predict`, `envs` and `times` (same types as in `fit`, aligned with the rows passed to `predict`) carry **no labels**: they only say which site and hour each row belongs to. You may use them, e.g. to group rows by site or to smooth predictions over time.

`predict` is called on **all** validation hours (815,304 rows), including the hours where ET was gap-filled, and the score uses all of them. About two-thirds of the scored hours therefore have gap-filled (modelled) targets.

Optional class attributes on `Model`:
- `standardize = True`: the harness applies a `RobustScaler` fitted on the training rows to `X` in `fit`, `eval_set` and `predict`.
- `astorch = True`: the harness passes `X` as a float32 `torch.Tensor` and `y` with shape `(n, 1)`, in `fit`, `eval_set` and `predict`.
- `remove_missing_target = False`: the harness keeps the training hours with gap-filled ET, so every site comes as a complete hourly series (useful for sequence models or temporal features). Their `y` is **NaN**, so you must mask them out of the loss and never train on them as targets. `X`, `envs` and `times` are complete for those rows.

`standardize` and `astorch` default to `False`; `remove_missing_target` defaults to `True`. **Note:** the reference models in `mlp.py`, `gdro.py`, `coral.py` and `mmd.py` set `standardize = astorch = True` and leave `remove_missing_target = True`. A subclass inherits these unless it overrides them.

## Code base

You are writing a file for the `models/` folder of `code_fluxtrapolation/`. You may import the following (skeletons only).

Dataloaders for torch models:

```python
# models/torch_utils.py
class FluxnetDataset(torch.utils.data.Dataset):
    def __init__(self, X: torch.Tensor, y: torch.Tensor, env_indices: np.ndarray[int]): ...
    def __getitem__(self, idx):   # idx may be an int or a list of ints (batched fetch)
        return X[idx], y[idx], env_idx[idx]

class ProportionateBatchSampler:  # every batch keeps the sites' proportions
    def __init__(self, env_indices, batch_size, drop_last=True, seed=42): ...
    # pure-Python, slow on millions of rows — prefer vectorized sampling
```

**Existing models** in `models/`, already benchmarked on this task:

| Name | Model |
|---|---|
| `lr` | Linear regression (the skill-score reference) |
| `constant` | Predicts the training mean |
| `ridge` | Ridge regression |
| `robust_lr` | Huber regression |
| `xgb` | XGBoost |
| `mlp` | Multi-layer perceptron (PyTorch) |
| `gdro` | Group DRO: minimizes the worst site loss (PyTorch) |
| `coral` | CORAL: aligns feature statistics across sites (PyTorch) |
| `mmd` | MMD: aligns feature distributions across sites (PyTorch) |

You may import only `models.torch_utils` and the reference models `mlp`, `gdro`, `coral` and `mmd` (e.g. `from models.gdro import Model`). The other models are listed for information only.

**Libraries:** `numpy`, `pandas`, `scipy`, `scikit-learn==1.5.2`, `torch`, `xgboost` and the Python standard library. Nothing else, and no downloads.

**Search space.** At the bottom of your model file, define `PARAM_SPACE`, a dict mapping `__init__` argument names to either:
- a fixed value, e.g. `'n_epochs': 30`, or
- a distribution tuple:
  - `('uniform', lo, hi)`
  - `('loguniform', lo, hi)`
  - `('int', lo, hi)`: integer, both ends inclusive
  - `('choice', [option1, option2, ...])`: options may be lists, e.g. layer sizes

The harness draws **5 configurations** from `PARAM_SPACE` with a fixed seed (42). Every distribution is sampled independently in each draw. Arguments missing from `PARAM_SPACE` keep their `__init__` default. If `PARAM_SPACE` contains no distributions, the model is fitted only once. With only 5 independent draws, tune only the 2–4 hyperparameters that matter most, over ranges narrow enough to be useful.

### Example code outline

You must output a python file which must define:

```python
"""Model name/short description"""

import libraries
from library import module


class Model:
    # Optional class attributes, read by the harness before the model is created.
    standardize = False
    astorch = False
    remove_missing_target = True

    def __init__(self, parameter1=1, parameter2=2, random_state=42):
        self.params = dict(
            parameter1=parameter1, parameter2=parameter2,
            random_state=random_state,
        )

    def fit(self, X, y):  # optional args: eval_set, envs, times, feature_names
        self.model = ...
        self.model.fit(X, y)
        return self

    def predict(self, X):  # optional args: envs, times
        return np.asarray(self.model.predict(X), dtype=np.float64).ravel()

# example of a PARAM_SPACE
PARAM_SPACE = {
    'n_estimators': ('int', 200, 1000),
    'learning_rate': ('loguniform', 0.01, 0.3),
    'subsample': ('uniform', 0.6, 1.0),
}
```

## Evaluation

**How you are scored:**
1. For each of the 5 hyperparameter draws, the harness calls `Model(**params).fit(...)` on the training sites and then `predict` on the 20 validation sites.
2. The best draw is selected by the validation score below. Your node's fitness is that draw's validation score. **Higher is better.**

**Validation score: skill relative to linear regression, averaged over six temporal scales.**
- Hourly predictions are aggregated per site to six scales:
  - **hourly**
  - **weekly** means
  - **seasonal**: mean seasonal cycle
  - **anomalies**: daily deviations from the mean seasonal cycle
  - **IAV**: deviations of yearly means from the site's long-term mean
  - **spatial**: long-term mean per site
- For each scale c, let E_c be the **median over validation sites** of the per-site RMSE.
- Let E_c⁰ be the same quantity for an ordinary linear regression on the 26 raw covariates, trained on the same training rows.
- Score = (1/6) Σ_c (1 − E_c / E_c⁰). A score of 0 equals linear regression; 1 is perfect; negative is worse than linear regression.
- For reference, current baselines score: linear regression 0 (by definition); XGBoost (`xgb`) 0.265 (q90 score: 0.195).

**Compute limits:**
- The **whole run** (loading the data, 5 fits and predictions) must finish within **30 minutes** on a MacBook Pro M3 (Apple-silicon GPU via `torch` MPS). Otherwise the node fails. Loading counts toward the limit, and with `remove_missing_target = False` there are 5.5 million training rows.
- Plan on about 5 minutes per draw and add a wall-clock guard to iterative training.
- On MPS, use float32 only (no float64), fall back to CPU if MPS is unavailable, and expect some ops to be unsupported or non-deterministic. Predict in batches.
- A crash, NaN output, wrong output shape or timeout means the node fails.

**Rules (violations mean the node is discarded):**
- The model file must be **self-contained**. The harness passes nothing beyond what is described here, so no extra fit kwargs, callbacks or `verbose` flags.
- Use only the arguments given to `fit` and `predict`. Do not read files, data or environment variables, and do not use the network.
- Do not hard-code site IDs, coordinates or anything else about particular sites.
- Do not use `eval_set` targets for anything beyond early stopping, and never train on them.
- Do not modify, monkeypatch or import from the harness, evaluation or other repo files beyond those listed under *Code base*.
- Fix all random seeds: the same hyperparameters must give the same predictions.