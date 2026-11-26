# Evaluate one candidate node (v0.3)

Your job is to put the file received into the scratch code base, run the harness and record the score. 
**Do not improve, debug or rewrite the model.** If it crashes, that is its result. **Only read-only git commands (e.g. `git diff`) are allowed; never run any other git command.**

## Inputs

- `RUN_ID`, `TREE_ID`: given by the search agent. The search agent creates `agent_access/scratch/{RUN_ID}/{TREE_ID}/` before the first node of a tree. If that folder is missing, stop and ask.
- `PARENT` is the parent node's ID, or `root` for a root node. `DIRECTION` is the assigned research direction, empty if none.
- The model file and the worker's method summary for step 8.

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

Set `TIMEOUT_SECONDS` to the per-evaluation limit from `2-search-specific.MD`, in seconds.

## Steps

1. **Extract.** Take `MODEL_NAME` (from the python file as `{MODEL_NAME}.py`) and the single Python code block. If there is no python block, or more than one, the status is `invalid`.
2. **Name.** `MODEL_NAME` must be a valid Python identifier. Treat `root` and names already used in `models/`, `results/`, this run's `era_nodes.csv` or its node folders as taken. If it is taken, append `_2`, `_3`, and so on. Never overwrite a file. Set `NODE_DIR=../scratch/{RUN_ID}/{TREE_ID}/{MODEL_NAME}`. Record invalid submissions under an unused ID in step 8.
3. **Snapshot.** Save `{ git diff; git status --porcelain; } | shasum` so step 7 can check that no repo file was changed or added.
4. **Save** the code verbatim to `$NODE_DIR/{MODEL_NAME}.py` (create `NODE_DIR`).
5. **Rule check.** Read the file without running it. If it violates the interface, import or data-use rules in `4-task-description.MD`, mark it `invalid` and skip to step 8.
6. **Run** the file. If `results/lr_trials.csv` is missing, first run `python train_model.py --model_name lr` (this is the shared skill baseline and stays in the main repo). Then run:
   `SECONDS=0; PYTHONDONTWRITEBYTECODE=1 timeout "$TIMEOUT_SECONDS" python train_model.py --model_name {MODEL_NAME} --model_file "$NODE_DIR/{MODEL_NAME}.py" --out_dir "$NODE_DIR" > "$NODE_DIR/{MODEL_NAME}.log" 2>&1; echo "exit=$? seconds=$SECONDS"`
   macOS has no built-in `timeout`: use `gtimeout` if `timeout` is missing. If neither exists, stop and ask the user. Do not install packages.
   - exit code 124: `timeout`
   - any other non-zero exit, a missing `$NODE_DIR/{MODEL_NAME}_trials.csv`, or a non-finite best skill: `crash`
   - otherwise: `ok`
7. **Integrity.** `{ git diff; git status --porcelain; } | shasum` must equal the snapshot from step 3. If it doesn't, the status is `invalid`. Report which files changed or appeared and leave them for the user to inspect.
8. **Record.** Append one row to `../scratch/{RUN_ID}/era_nodes.csv` (create it with a header if it is missing) and reply with the same fields:

   `node, tree, parent, direction, status, skill, skill_q90, best_params, minutes, summary, note`

   - `node`: `MODEL_NAME`; `tree`: `TREE_ID`
   - `parent`, `direction`: as given in the inputs
   - `skill`, `skill_q90`, `best_params`: from the first trial with the highest `skill` in `$NODE_DIR/{MODEL_NAME}_trials.csv` (empty unless `ok`)
   - `minutes`: wall-clock time of step 6
   - `summary`: the inner LLM's method summary, at most 2 sentences
   - `note`: for a node that is not `ok`, the rule broken or the last line of the traceback
