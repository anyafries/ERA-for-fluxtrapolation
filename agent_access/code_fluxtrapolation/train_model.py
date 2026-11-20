import argparse
import json
import logging
import os
import numpy as np
import pandas as pd
import torch

from dataloader import load_data
from eval import evaluate
from models import load, sample_params
from tests.test_models import test_model

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

torch.backends.cudnn.deterministic = True
torch.backends.cudnn.benchmark = False

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_name", default='lr', help="Module name in models/")
    parser.add_argument("--n_iter", type=int, default=5, help="Number of sampled configs")
    parser.add_argument("--path", default='data/sites', help="Folder with one CSV per site")
    parser.add_argument("--rerun", action='store_true', help="Overwrite existing results")
    parser.add_argument("--model_file", default=None, help="Load the model from this .py file instead of models/")
    parser.add_argument("--out_dir", default='results', help="Folder for the trials and predictions CSVs")
    args = parser.parse_args()

    out = os.path.join(args.out_dir, args.model_name)
    if os.path.exists(f'{out}_trials.csv') and not args.rerun:
        logger.info(f"{out}_trials.csv exists. Use --rerun to overwrite.")
        raise SystemExit

    mod = load(args.model_name, args.model_file)
    (xtrain, ytrain, envs_train, times_train), (xval, yval, envs_val, times_val, qc_val), features = load_data(
        args.path, remove_missing_target=getattr(mod.Model, 'remove_missing_target', True),
        standardize=getattr(mod.Model, 'standardize', False),
        astorch=getattr(mod.Model, 'astorch', False))
    yval_np = np.asarray(yval).ravel()
    eval_set = [(xval[qc_val], yval[qc_val])]  # early stopping uses measured val rows only

    # Skill is relative to lr.
    base = None
    if args.model_name != 'lr':
        if not os.path.exists('results/lr_trials.csv'):
            raise FileNotFoundError("results/lr_trials.csv not found. Run `python train_model.py --model_name lr` first.")
        base = pd.read_csv('results/lr_trials.csv').iloc[0]

    # Random search; a space without distributions needs only one trial.
    is_random = any(isinstance(v, tuple) for v in mod.PARAM_SPACE.values())
    rng = np.random.default_rng(42)
    trials, best_pred = [], None
    for i in range(args.n_iter if is_random else 1):
        params = sample_params(mod.PARAM_SPACE, rng)
        model = mod.Model(**params)
        fit_opt, predict_opt = test_model(model)
        fit_avail = {'eval_set': eval_set, 'envs': envs_train, 'times': times_train,
                     'feature_names': features}
        model.fit(X=xtrain, y=ytrain, **{k: v for k, v in fit_avail.items() if k in fit_opt})

        predict_avail = {'envs': envs_val, 'times': times_val}
        pred = model.predict(xval, **{k: v for k, v in predict_avail.items() if k in predict_opt})
        scores = evaluate(yval_np, pred, envs_val, times_val, base)
        logger.info(f"Trial {i}: skill={scores['skill']:.4f}, skill_q90={scores['skill_q90']:.4f}, params={params}")
        if not trials or scores['skill'] > max(t['skill'] for t in trials):
            best_pred = pred
        trials.append({'trial': i, **scores, 'params': json.dumps(params)})

    os.makedirs(args.out_dir, exist_ok=True)
    pd.DataFrame(trials).to_csv(f'{out}_trials.csv', index=False)
    pd.DataFrame({'site_id': envs_val, 'time': times_val, 'qc_mask': qc_val, 'y_true': yval_np,
                  'y_pred': best_pred}).to_csv(f'{out}_val_predictions.csv', index=False)
    logger.info(f"Saved {out}_trials.csv and {out}_val_predictions.csv")
