# Artifacts and reporting (v0.1)

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

In `agent-access`, you have a `SCRATCH`. Progress, models, in-search evaluation and any other relevant information you want to collect during the tree search should be saved here. 

A run is one launch of a tree with a specific research direction. Before anything else, create `SCRATCH/{RUN_ID}/` (e.g. `run_YYYYMMDD_HHMM`), and before a tree's first node, create `SCRATCH/{RUN_ID}/{TREE_ID}/` (`TREE_ID` = the research-direction filename without `.md`). Pass `RUN_ID` and `TREE_ID` to every in-search evaluation ([5-in-search-eval.MD](5-in-search-eval.MD)).

```
SCRATCH/{RUN_ID}/
  ...                    # run-level files
  {TREE_ID}/
    {node}/              # one folder per node (written by the evaluator)
```

The run folder holds:
- Run manifest and the completed task spec.
- Append-only event log and resumable scheduler state.
- Finalist manifest and descriptions.
- Tree visualization and summary report.
- Potentially additional files created by the in-search agent.

## 3. What to record

**Per run**
- Run ID and timestamps.
- Protocol and task-spec versions.
- Environment.
- Provider/model, when known.
- Tree order and each tree's research direction (source filename).
- Selection settings.
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

**Selection**
- Take the best `n` scored nodes per tree, ranked by the primary metric in `4-task-description.MD`.
- `n` is set in `2-search-specific.MD`.

**Package (per finalist)**
- Frozen Python file in the task's required format.
- Code hash and source candidate ID.
- Validation scores and the evaluation config they came from.
- Environment reference.
- A short description (below).

**Description:** one to two short sentences, written from the frozen code that describe the key methodological choices. Method labels and worker summaries are not proof; check against the code.

> Example: Gradient-boosted regression model using one month of lagged inputs and weekly rolling summary features. Hyperparameters are fixed.

## 6. Tree visualization
Each tree shown separately, with:
- Nodes colored by primary validation score and labelled with the value.
- One labeled color scale shared by all trees in the run. Label whether higher or lower is better.
- Distinct looks for failed, pending and unscored nodes.
- Clear root and finalist markers.
- Parent–child edges.
- Root node labeled with the research direction name.