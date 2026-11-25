# Artifacts and reporting (v0.2)

## 1. Goal
- Every run can be inspected and resumed.
- Finalists can be evaluated on their own, outside the search.
- Reports focus on: the selected code, its measured scores, what it actually does.
- No written reasons are needed for individual parent choices.

Companion documents:
- [1-search-general.MD](1-search-general.MD)
- [2-search-specific.MD](2-search-specific.MD)
- [4-task-description.MD](4-task-description.MD)
- [5-in-search-eval.MD](5-in-search-eval.MD)

## 2. Folder layout

Save progress, models and in-search evaluation in `agent_access/scratch/`.

A run can contain several trees. Before anything else, create `scratch/{RUN_ID}/` (e.g. `run_YYYYMMDD_HHMM`), and before a tree's first node, create `scratch/{RUN_ID}/{TREE_ID}/` (`TREE_ID` = the research-direction filename without `.md`). Pass `RUN_ID` and `TREE_ID` to every in-search evaluation ([5-in-search-eval.MD](5-in-search-eval.MD)).

```
scratch/{RUN_ID}/
  run_manifest.json
  era_nodes.csv
  best_trials.csv
  finalists/
    manifest.json
    {node}.py
  ...                    # run-level files
  {TREE_ID}/
    {node}/              # one folder per node (written by the evaluator)
```

The run folder holds:
- Run manifest and any run-specific additions to the task spec.
- Append-only event log and resumable scheduler state.
- Finalist export and winning trial summaries.
- Tree visualization and summary report.
- Potentially additional files created by the in-search agent.

## 3. What to record

**Per run**
- Run ID and timestamps.
- In `run_manifest.json`, record `prompt_versions` as a mapping from each numbered prompt filename to the version in its first heading (e.g. `"2-search-specific.MD": "v0.2"`).
- Environment.
- Provider/model, when known.
- Tree order and each tree's research direction (source filename).
- Selection settings.
- `artifact_retention` from `2-search-specific.MD`.
- Budget limits and actual use.
- Status, stopping reason, any deviations.

**Per candidate**
- Candidate ID and tree ID.
- Parent ID (`root` for a root).
- Creation order and timestamp.

**Per evaluation**
- Execution status.
- Primary score and secondary metrics.
- Per-fold/per-seed results (if any) and how they were aggregated.
- Runtime and measured resource use.
- If failed: failure category and a short error summary.

## 4. Search state and events
Log enough structured data to rebuild:
- Which parent was picked.
- Visit counts and S(u) values at dispatch.
- Pending and finished work.
- Stops, resumes and config changes.

No written reasoning needed: the numbers plus the fixed selection rule explain every choice.

## 5. Finalists

A finalist is a candidate picked from the search to be run on the unseen final test.

**Description:** one to two short sentences, written from the frozen code that describe the key methodological choices. Method labels and worker summaries are not proof; check against the code.

**Selection**
- Take up to `n` eligible nodes per tree, ranked by the primary metric in `4-task-description.MD`. Break ties by creation order.
- Eligibility and `n` are set in `2-search-specific.MD`.

**Export**
- Copy each finalist's frozen Python file to `finalists/{node}.py`. Keep the original source in its node folder.
- Write `finalists/manifest.json` with `run_id`, `run_manifest` (`"../run_manifest.json"`, for the evaluation configuration and environment) and a `finalists` list. Each entry has `node` and `tree` from `era_nodes.csv`, the copied file's `sha256`, the winning `params` as a JSON object, a `validation_metrics` object mapping each metric name to its winning validation score, and a `description`.

> Example: Gradient-boosted regression model using one month of lagged inputs and weekly rolling summary features. Hyperparameters are fixed.

## 6. Tree visualization
Each tree shown separately, with:
- Nodes colored by primary validation score and labelled with the value.
- One labeled color scale shared by all trees in the run. Label whether higher or lower is better.
- Distinct looks for failed, pending and unscored nodes.
- Clear root and finalist markers.
- Parent–child edges.
- Root node labeled with the research direction name.

## 7. Retention

- At the end of the run, save `best_trials.csv` with one row for every `ok` node. Include `node`, `tree` and the full winning row from its trials CSV, including the per-scale scores. Use the same winning trial as `era_nodes.csv`.
- With `artifact_retention = all`, keep the original node files.
- With `artifact_retention = compact`, wait until the run is complete with no pending evaluations. Finish the reports and verify that the finalist list, copied source hashes and parameters match the selected nodes. Check that `best_trials.csv` covers every `ok` node with the correct winning row.
- In `compact` mode, after those checks, remove `{node}.log`, `{node}_trials.csv` and `{node}_val_predictions.csv` from the node folders listed in this run's `era_nodes.csv`, where those files exist. Keep each node's source file, the finalist export and all run-level files. If cleanup is interrupted, resume it from verified export and summaries.
