# Evaluate one candidate node (v0.2)

Your job is to put the file received into the scratch code base, run the harness and record the score. 
**Do not improve, debug or rewrite the model.** If it crashes, that is its result. **Only read-only git commands (e.g. `git diff`) are allowed; never run any other git command.**

## Inputs

- `RUN_ID`, `TREE_ID`: given by the search agent. The search agent creates `agent_access/scratch/{RUN_ID}/{TREE_ID}/` before the first node of a tree. If that folder is missing, stop and ask.
- `PARENT`, `DIRECTION`: given by the search agent (`empty` for root children or if there is no direction).
- The python file containing the model.

## Layout

Run every command from `code_fluxtrapolation/` with the project venv active. You will use the following paths below, given relative to it.

```
../scratch/{RUN_ID}/
  era_nodes.csv                      # one row per node, all trees of the run
  {TREE_ID}/
    {MODEL_NAME}/                    # NODE_DIR, one folder per node
      {MODEL_NAME}.py
      {MODEL_NAME}.log
      {MODEL_NAME}_trials.csv
      {MODEL_NAME}_val_predictions.csv
```

Write candidate artefacts only to the node folder. The coordinator exports finalists after the search, as described in `3-saving-general.MD`.

Evaluate one node at a time, because the 30-minute limit assumes the machine is otherwise idle.

## Steps

1. **Extract.** Take `MODEL_NAME` (from the python file as `{MODEL_NAME}.py`) and the single ```python block. Ignore all other text. If there is no python block, or more than one, the status is `invalid`.
2. **Name.** `MODEL_NAME` must be a valid Python identifier and must not exist yet in `models/`, `results/`, or as a node folder anywhere in `../scratch/{RUN_ID}/`. If it is taken, append `_2`, `_3`, and so on. Never overwrite a file. Set `NODE_DIR=../scratch/{RUN_ID}/{TREE_ID}/{MODEL_NAME}`.
3. **Snapshot.** Save `{ git diff; git status --porcelain; } | shasum` so step 7 can check that no repo file was changed or added.
4. **Save** the code verbatim to `$NODE_DIR/{MODEL_NAME}.py` (create `NODE_DIR`).
5. **Rule check.** Read the file without running it. The status is `invalid` (skip to step 8) if the file:
   - imports anything other than numpy, pandas, scipy, sklearn, torch, xgboost, the standard library, `models.torch_utils` or the reference models (`mlp`, `gdro`, `coral`, `mmd`). A node must be standalone: it may not import other nodes (including its parent); copied code is fine;
   - reads files, environment variables or the network, or touches harness code (`train_model.py`, `eval.py`, `dataloader.py`, `models/__init__.py`, `utils/`, `tests/`);
   - hard-codes site IDs or coordinates;
   - uses `eval_set` targets for anything except early stopping;
   - has no `class Model` or no `PARAM_SPACE`.
6. **Run** the file. If `results/lr_trials.csv` is missing, first run `python train_model.py --model_name lr` (this is the shared skill baseline and stays in the main repo). Then run:
   `SECONDS=0; PYTHONDONTWRITEBYTECODE=1 timeout 1800 python train_model.py --model_name {MODEL_NAME} --model_file $NODE_DIR/{MODEL_NAME}.py --out_dir $NODE_DIR > $NODE_DIR/{MODEL_NAME}.log 2>&1; echo "exit=$? seconds=$SECONDS"`
   macOS has no built-in `timeout`: use `gtimeout` if `timeout` is missing. If neither exists, stop and ask the user. Do not install packages.
   - exit code 124: `timeout`
   - any other non-zero exit, a missing `$NODE_DIR/{MODEL_NAME}_trials.csv`, or a NaN best skill: `crash`
   - otherwise: `ok`
7. **Integrity.** `{ git diff; git status --porcelain; } | shasum` must equal the snapshot from step 3. If it doesn't, the status is `invalid`. Report which files changed or appeared and leave them for the user to inspect.
8. **Record.** Append one row to `../scratch/{RUN_ID}/era_nodes.csv` (create it with a header if it is missing) and reply with the same fields:

   `node, tree, parent, direction, status, skill, skill_q90, best_params, minutes, summary, note`

   - `node`: `MODEL_NAME`; `tree`: `TREE_ID`
   - `parent`, `direction`: as given in the inputs
   - `skill`, `skill_q90`, `best_params`: from the trial with the highest `skill` in `$NODE_DIR/{MODEL_NAME}_trials.csv` (empty unless `ok`)
   - `minutes`: wall-clock time of step 6
   - `summary`: the inner LLM's method summary, at most 2 sentences
   - `note`: for a node that is not `ok`, the rule broken or the last line of the traceback
