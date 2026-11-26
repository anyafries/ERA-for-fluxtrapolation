# Artifacts and reporting (v0.3)

## 1. Goal
- Every run can be inspected and resumed.
- Finalists can be evaluated on their own, outside the search.
- Reports focus on: the selected code, its measured scores, what it actually does.
- No written reasons are needed for individual parent choices.

Companion documents:
- [1-search-general.MD](1-search-general.MD)
- [2-search-specific.MD](2-search-specific.MD)
- [4-task-description.MD](4-task-description.MD)
- [6-after-search-eval.MD](6-after-search-eval.MD)

## 2. Folder layout

Save progress, models and in-search evaluation in `agent_access/scratch/`.

A run can contain several trees. Before anything else, create `scratch/{RUN_ID}/` (e.g. `run_YYYYMMDD_HHMM`), and before a tree's first node, create `scratch/{RUN_ID}/{TREE_ID}/` (`TREE_ID` = the research-direction filename without `.md`). Pass `RUN_ID` and `TREE_ID` to every in-search evaluation.

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
    {node}/              # reserved for this candidate and its evaluation outputs
      {node}.py          # frozen candidate source
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
- In `run_manifest.json`, map each numbered prompt's filename to the version in its first heading under `prompt_versions`.
- Environment.
- Provider/model, when known.
- Tree order and each tree's research direction (source filename).
- Selection settings.
- The primary metric, metric directions and any reporting references defined in `4-task-description.MD`.
- `artifact_retention` from `2-search-specific.MD`.
- Budget limits and actual use.
- Status, stopping reason, any deviations.

**Per candidate**
- Record `node` (a Python identifier unique across the run), `tree` and `parent` in `era_nodes.csv`. Reserve `root` for the parent field of a root node.
- Creation order and timestamp.

**Per evaluation**
- Execution status (`ok` for a successful evaluation).
- Primary score and secondary metrics.
- If there is just one trial, use it as the winning result. Record `{}` for parameters when there are none.
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
- Take up to `n` eligible nodes per tree, ranked by the primary metric in the direction specified in `4-task-description.MD`. Break ties by creation order.
- Eligibility and `n` are set in `2-search-specific.MD`.

**Export**
- Copy each finalist's frozen Python file to `finalists/{node}.py`. Keep the original source in its node folder.
- Write `finalists/manifest.json` with `run_id`, `run_manifest` (`"../run_manifest.json"`, for the evaluation configuration and environment) and a `finalists` list. Each entry has `node` and `tree` from `era_nodes.csv`, the copied file's `sha256`, the winning `params` as a JSON object, a `validation_metrics` object mapping each metric name to its winning validation score, and a `description`.

## 6. Tree visualisation
Save the interactive report in the run folder using `6-after-search-eval.MD`.

## 7. Retention

- At the end of the run, save `best_trials.csv` with one row for every `ok` node. Include `node`, `tree` and the full winning result, with all its metrics and parameters. Use the same winning result as `era_nodes.csv`.
- With `artifact_retention = all`, keep the original node files.
- With `artifact_retention = compact`, wait until the run is complete with no pending evaluations. Finish the reports and verify that the finalist list, copied source hashes and parameters match the selected nodes. Check that `best_trials.csv` covers every `ok` node with the correct winning row.
- In `compact` mode, once those checks pass, clean only node folders inside this run that are listed in `era_nodes.csv` and contain their frozen `{node}.py`. Keep that file and remove the other contents of the node folder without following symlinks. Keep the finalist export and all run-level files. If cleanup is interrupted, resume from the verified export and summaries.
