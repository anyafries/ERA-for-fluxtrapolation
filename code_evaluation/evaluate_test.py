"""Score ERA nodes on the 40 TA40 test sites.

ERA's train/val split is TA40's train/val split, so a node's best config only
needs to be refit and asked to predict on the TA40 test sites.

For each node:
  1. Load the model and its best validation config from the finalist export
     or the training checkout's models/ and results/ directories.
  2. Refit it on the train sites, exactly as train_model.py does.
  3. Predict on val (reproducibility check) and on the 40 test sites.
  4. Score with eval.evaluate on all test hours, relative to lr refit
     on the same test sites.

Usage:
    python evaluate_test.py --finalists /path/to/run/finalists
    python evaluate_test.py                 # best ERA node (top 1 in era_nodes.csv)
    python evaluate_test.py --topk 5        # 5 best ERA nodes
    python evaluate_test.py --node xgb      # one model, e.g. a baseline

Finalist test results are saved under code_evaluation/results/{run_id}/.
"""

import argparse
import hashlib
import json
import logging
import math
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from sklearn.preprocessing import RobustScaler

HERE = os.path.dirname(os.path.abspath(__file__))
TRAIN_REPO = os.path.join(HERE, '..', 'code_fluxtrapolation_training')
if not os.path.isdir(TRAIN_REPO):
    TRAIN_REPO = os.path.join(HERE, '..', 'agent_access', 'code_fluxtrapolation')
sys.path.insert(0, TRAIN_REPO)

from dataloader import load_data, NON_FEATURES, TARGET  # noqa: E402
from eval import evaluate  # noqa: E402
from models import load  # noqa: E402
from tests.test_models import test_model  # noqa: E402

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

torch.backends.cudnn.deterministic = True
torch.backends.cudnn.benchmark = False

# TA40 test sites: the 40 warmest sites (FLUXtrapolation dataloader.py, upstream/main).
TEST_SITES = ['AU-Dry', 'AU-DaS', 'AU-Lit', 'BR-Npw', 'AU-Lon', 'AU-ASM', 'US-xDS', 'US-ONA',
              'US-SP1', 'US-xJE', 'US-SRM', 'US-HB2', 'AU-GWW', 'US-SRS', 'US-SRG', 'IL-Yat',
              'US-HB3', 'US-HB1', 'US-xDL', 'US-RGA', 'AU-Cum', 'US-xTA', 'AU-Cpr', 'US-Whs',
              'US-Cst', 'US-Wkg', 'IT-BCi', 'US-Jo2', 'IT-Cp2', 'US-RGo', 'ES-Abr', 'US-NC4',
              'ES-Agu', 'US-Akn', 'US-xJR', 'ES-Pdu', 'US-Ton', 'ES-LM2', 'IT-Noe', 'ES-LM1']

# The 40 TA40 test site CSVs.
DEFAULT_TEST_PATH = os.path.join(HERE, 'data', 'sites')


def load_test(path, features):
    """All hours of the test sites (gap-filled ones included, as for val)."""
    missing = [s for s in TEST_SITES if not os.path.exists(os.path.join(path, f'{s}.csv'))]
    assert not missing, f"Test sites missing from {path}: {missing}"
    df = pd.concat([pd.read_csv(os.path.join(path, f'{s}.csv')).assign(site_id=s) for s in TEST_SITES],
                   ignore_index=True)
    test_features = [c for c in df.columns if c not in NON_FEATURES]
    assert test_features == features, f"Feature mismatch:\n{test_features}\nvs\n{features}"
    assert df[features].notna().all().all(), "Missing values in test features"
    qc = (df['qc_mask'] == 1).to_numpy()
    assert df.loc[qc, TARGET].notna().all(), "NaN target where qc_mask == 1"
    return (df[features].to_numpy(np.float64), df[TARGET].to_numpy(np.float64),
            df['site_id'].to_numpy(), pd.to_datetime(df['time']).to_numpy(), qc)


def prepare(mod, train_path):
    """Train/val as train_model.py gets them, but unscaled, so test can be scaled the same way."""
    attr = lambda a, d: getattr(mod.Model, a, d)  # noqa: E731
    (xtr, ytr, etr, ttr), (xva, yva, eva, tva, qva), features = load_data(
        train_path, remove_missing_target=attr('remove_missing_target', True))
    leaked = set(TEST_SITES) & set(etr) | set(TEST_SITES) & set(eva)
    assert not leaked, f"Test sites found in the ERA data: {leaked}"
    return (xtr, ytr, etr, ttr), (xva, yva, eva, tva, qva), features


def transform(mod, xtr, ytr, xs, ys):
    """Apply standardize / astorch exactly like load_data, to train and every other split."""
    if getattr(mod.Model, 'standardize', False):
        scaler = RobustScaler().fit(xtr)
        xtr, xs = scaler.transform(xtr), [scaler.transform(x) for x in xs]
    if getattr(mod.Model, 'astorch', False):
        tx = lambda x: torch.tensor(x, dtype=torch.float32)  # noqa: E731
        ty = lambda y: torch.tensor(y, dtype=torch.float32).view(-1, 1)  # noqa: E731
        xtr, ytr, xs, ys = tx(xtr), ty(ytr), [tx(x) for x in xs], [ty(y) for y in ys]
    return xtr, ytr, xs, ys


def best_params(node):
    trials = pd.read_csv(os.path.join(TRAIN_REPO, 'results', f'{node}_trials.csv'))
    best = trials.loc[trials['skill'].idxmax()]
    return json.loads(best['params']), float(best['skill'])


def load_finalists(directory):
    """Read the exported configuration and verify each frozen model file."""
    directory = Path(directory)
    with (directory / 'manifest.json').open(encoding='utf-8') as handle:
        manifest = json.load(handle)
    run_id = manifest['run_id']
    if not isinstance(run_id, str) or run_id in ('', '.', '..') or Path(run_id).name != run_id:
        raise ValueError(f"Invalid finalist run ID: {run_id!r}")

    finalists = {}
    for entry in manifest['finalists']:
        node = entry['node']
        if not isinstance(node, str) or not node.isidentifier() or node == 'lr' or node in finalists:
            raise ValueError(f"Invalid or duplicate finalist name: {node!r}")
        model_file = directory / f'{node}.py'
        if hashlib.sha256(model_file.read_bytes()).hexdigest() != entry['sha256']:
            raise ValueError(f"Source hash mismatch for finalist {model_file}")
        params, skill = entry['params'], entry['validation_metrics']['skill']
        if not isinstance(params, dict) or type(skill) not in (int, float) or not math.isfinite(skill):
            raise ValueError(f"Invalid params or validation skill for finalist {node}")
        finalists[node] = {'model_file': model_file, 'params': params, 'val_skill': skill}
    return run_id, finalists


def run_node(node, train_path, test_path, base_val, base_test, *, model_file=None, params=None, val_skill=None):
    """Refit the node's best config, predict val and test. Returns (row, test predictions)."""
    t0 = time.time()
    mod = load(node) if model_file is None else load(f'models.{node}', model_file)
    if params is None:
        params, val_skill = best_params(node)
    logger.info(f"[{node}] params={params}")

    (xtr, ytr, etr, ttr), (xva, yva, eva, tva, qva), features = prepare(mod, train_path)
    xte, yte, ete, tte, qte = load_test(test_path, features)
    xtr, ytr_m, (xva_m, xte_m), (yva_m,) = transform(mod, xtr, ytr, [xva, xte], [yva])
    eval_set = [(xva_m[qva], yva_m[qva])]  # measured val hours only, as in train_model.py

    model = mod.Model(**params)
    fit_opt, predict_opt = test_model(model)
    fit_avail = {'eval_set': eval_set, 'envs': etr, 'times': ttr, 'feature_names': features}
    model.fit(X=xtr, y=ytr_m, **{k: v for k, v in fit_avail.items() if k in fit_opt})

    def predict(x, envs, times):
        avail = {'envs': envs, 'times': times}
        pred = np.asarray(model.predict(x, **{k: v for k, v in avail.items() if k in predict_opt}),
                          dtype=np.float64).ravel()
        assert pred.shape == (len(envs),) and np.isfinite(pred).all(), "Bad predictions"
        return pred

    pred_va = predict(xva_m, eva, tva)
    pred_te = predict(xte_m, ete, tte)
    val_refit = evaluate(yva, pred_va, eva, tva, base_val)
    scores = evaluate(yte, pred_te, ete, tte, base_test)

    if base_val is not None and abs(val_refit['skill'] - val_skill) > 1e-3:
        logger.warning(f"[{node}] refit val skill {val_refit['skill']:.4f} != stored {val_skill:.4f}")
    minutes = (time.time() - t0) / 60
    logger.info(f"[{node}] test skill={scores['skill']:.4f}, skill_q90={scores['skill_q90']:.4f}, "
                f"val skill stored={val_skill:.4f} refit={val_refit['skill']:.4f}, {minutes:.1f} min")

    row = {'node': node, **scores, 'val_skill': val_skill, 'val_skill_refit': val_refit['skill'],
           'minutes': minutes, 'params': json.dumps(params)}
    preds = pd.DataFrame({'site_id': ete, 'time': tte, 'qc_mask': qte, 'y_true': yte, 'y_pred': pred_te})
    return row, preds


def topk_nodes(k):
    path = os.path.join(TRAIN_REPO, 'results', 'era_nodes.csv')
    if not os.path.exists(path):
        raise FileNotFoundError(f"{path} not found. Use --node NAME instead.")
    nodes = pd.read_csv(path)
    nodes = nodes[nodes['status'] == 'ok'].sort_values('skill', ascending=False)
    return nodes['node'].head(k).tolist()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--finalists", type=Path, help="Evaluate a run's exported finalists/ directory")
    parser.add_argument("--node", help="Evaluate one model by name (overrides --topk)")
    parser.add_argument("--topk", type=int,
                        help="Limit evaluation to the k best nodes (default: all exported finalists or one legacy node)")
    parser.add_argument("--train_path", default=os.path.join(TRAIN_REPO, 'data', 'sites'),
                        help="ERA data folder (train + val sites)")
    parser.add_argument("--test_path", default=DEFAULT_TEST_PATH,
                        help="Folder with the TA40 test site CSVs (e.g. the full data folder)")
    parser.add_argument("--rerun", action='store_true', help="Overwrite existing results")
    args = parser.parse_args()

    if args.topk is not None and args.topk < 1:
        parser.error('--topk must be positive')

    results_dir = os.path.join(HERE, 'results')
    finalists = {}
    if args.finalists is not None:
        run_id, finalists = load_finalists(args.finalists)
        if not finalists:
            parser.error(f'No finalists in {args.finalists}')
        if args.node and args.node not in finalists:
            parser.error(f'{args.node!r} is not in {args.finalists}')
        results_dir = os.path.join(results_dir, run_id)
        nodes = list(finalists)
        if args.topk is not None:
            nodes = sorted(nodes, key=lambda node: finalists[node]['val_skill'], reverse=True)[:args.topk]
    else:
        nodes = [] if args.node else topk_nodes(args.topk or 1)
    if args.node:
        nodes = [args.node]

    os.makedirs(results_dir, exist_ok=True)
    scores_path = os.path.join(results_dir, 'test_scores.csv')
    done = pd.read_csv(scores_path) if os.path.exists(scores_path) else pd.DataFrame(columns=['node'])

    def save(row, preds):
        global done
        done = pd.concat([done[done['node'] != row['node']], pd.DataFrame([row])], ignore_index=True)
        done.sort_values('skill', ascending=False).to_csv(scores_path, index=False)
        preds.to_csv(os.path.join(results_dir, f"{row['node']}_test_predictions.csv"), index=False)

    # lr is the skill reference on the test sites; its val reference is lr_trials.csv.
    base_val = pd.read_csv(os.path.join(TRAIN_REPO, 'results', 'lr_trials.csv')).iloc[0]
    if 'lr' not in set(done['node']) or (args.rerun and args.node == 'lr'):
        save(*run_node('lr', args.train_path, args.test_path, None, None))
    base_test = done.set_index('node').loc['lr']

    for node in nodes:
        if node == 'lr':
            continue
        if node in set(done['node']) and not args.rerun:
            logger.info(f"[{node}] already in {scores_path}. Use --rerun to overwrite.")
            continue
        save(*run_node(node, args.train_path, args.test_path, base_val, base_test, **finalists.get(node, {})))

    cols = ['node', 'skill', 'skill_q90', 'val_skill', 'val_skill_refit', 'minutes']
    print(done.sort_values('skill', ascending=False)[cols].to_string(index=False))
