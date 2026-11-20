"""
Each model lives in models/<name>.py and defines:
  - `Model`: class with fit(X, y[, eval_set][, envs][, times][, feature_names])
      and predict(X[, envs][, times]) -> np.ndarray. Optional arguments are
      passed only if they are in the signature; times are np.datetime64.
      Optional class attributes: `standardize = True` (RobustScaler on X),
      `astorch = True` (X, y passed as float32 torch tensors),
      `remove_missing_target = False` (keep train hours with gap-filled ET;
      their y is NaN, so fit must mask them).
  - `PARAM_SPACE`: dict of Model.__init__ kwargs. A value is either fixed or a
      distribution: ('uniform', lo, hi), ('loguniform', lo, hi),
      ('int', lo, hi) (inclusive) or ('choice', [options]).
"""

import importlib
import importlib.util
import sys
import numpy as np


def load(name, path=None):
    """Import models/<name>.py, or the file at `path` if given."""
    if path is None:
        return importlib.import_module(f'models.{name}')
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def sample_params(space, rng):
    def draw(v):
        if not isinstance(v, tuple):
            return v
        kind, *args = v
        if kind == 'uniform':
            return float(rng.uniform(*args))
        if kind == 'loguniform':
            return float(np.exp(rng.uniform(np.log(args[0]), np.log(args[1]))))
        if kind == 'int':
            return int(rng.integers(args[0], args[1] + 1))
        if kind == 'choice':
            return args[0][rng.integers(len(args[0]))]
        raise ValueError(f"Unknown distribution `{kind}`")
    return {k: draw(v) for k, v in space.items()}
