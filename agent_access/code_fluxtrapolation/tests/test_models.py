import inspect

def test_model(model):
    """
    Checks model capabilities.
    Returns: (fit_args, predict_args), the sets of optional argument names
    that fit (eval_set, envs, times, feature_names) and predict (envs, times)
    accept.
    """
    # 1. Basic sanity check
    if not (hasattr(model, "fit") and hasattr(model, "predict")):
        raise AttributeError(f"Model {type(model)} missing fit/predict methods.")

    # 2. Introspect the fit method signature
    params = inspect.signature(model.fit).parameters

    if not 'X' in params or not 'y' in params:
        raise ValueError(f"Model {type(model)} fit method must have 'X' and 'y' parameters.")

    # OOD models (CORAL, GDRO, MMD) usually require 'envs'
    fit_args = {a for a in ('eval_set', 'envs', 'times', 'feature_names') if a in params}

    # 3. Introspect the predict method signature
    params = inspect.signature(model.predict).parameters
    predict_args = {a for a in ('envs', 'times') if a in params}

    return fit_args, predict_args
