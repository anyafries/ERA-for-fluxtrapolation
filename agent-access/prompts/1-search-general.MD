# Search protocol (v0.1)

## 1. Goal

Our general task is solve a problem as specified in `4-task-description.MD`. Instead of creating programs yourself, your job is to spawn tree searches over programs using sub-agents and deliver a shortlist suitable for evaluation on an unseen final test set.

Companion documents:

- [2-search-specific.MD](2-search-specific.MD)
- [3-saving-general.MD](3-saving-general.MD)
- [4-task-description.MD](4-task-description.MD)
- [5-in-search-eval.MD](5-in-search-eval.MD)

## 2. Roles
- **Coordinator (you):** prepares worker assignments, calls the scheduler and evaluator, reviews final candidates.
- **Workers:** write candidate code from the task contract and a method instruction. When expanding, they also get the parent's code and its evaluation feedback and they also always get the task description `4-task-description.MD`.
- **Scheduler (local):** gives turns to trees, picks parents, enforces budgets, saves resumable state. Selection is computed from recorded data, never chosen by the coordinator.
- **Evaluator:** checks the candidate's interface, runs the task evaluation (specified in `5-in-search-eval.MD`), returns standardized results.
- Workers are temporary; nodes are saved artifacts, so no agent needs to keep running.

## 3. The task spec 
Ensure that the task spec (`4-task-description.MD`) defines:
- Inputs, outputs and allowed information.
- Code interface and formatting.
- Primary metric, its direction and how it is aggregated.
- What search data and evaluation data may be accessed.
- A runnable evaluation harness and a reference baseline.
- Exact environment and resource limits.
- Starting method instructions.
- Search budgets and finalist-selection settings.
- Mark which items are hard requirements and which are only method suggestions.

## 4. Trees and nodes
- A run has several independent trees. Each starts from a different method instruction (may be based on literature).
- Every non-root node has exactly one parent, in the same tree.
- One node = one frozen implementation.
  - Changed code or behavior-affecting config → new node.
  - Re-evaluating unchanged code → extra evaluation record on the same node.
- The reference baseline is not a root, unless the task spec says so.

## 5. Turns across trees
- All trees get the same attempt budget and take turns in a fixed round-robin order.
- One turn = one attempt: create a root, expand, or repair. All three cost the same.
- Generation and evaluation concurrency are set separately. Default: 1 worker, 1 evaluation at a time.
- No overlapping expansions within a tree: finish evaluating the last result before picking its next parent.
- Skip exhausted or stopped trees. Their leftover budget is not given to other trees.
- Actual use may differ from plan (early stopping, resource limits). Report it.

## 6. Parent selection within a tree
For scored, valid nodes, use the rank-based Algorithm 1 from *An AI system to help scientists write expert-level empirical software*, arXiv:2509.06503v1, Methods, p. 17:

$$S(u) = R(u) + \frac{c}{n} \frac{\sqrt{\sum_{v \textrm{ in tree } T} V(v)} }{ (1 + V(u))} $$

- n: number of scored nodes in the tree.
- R(u) = (rank(u) − 1) / (n − 1) if n > 1; R(u) = 1 if n = 1.
- Ranks go from worst to best, respecting the metric's direction.
- V(u): visit count.
- c: exploration constant, fixed before the run. 
- Pick the node with the highest S(u).
- A new scored node starts with 1 visit; each of its ancestors gains 1 visit.
- Ties: equal scores get the average rank; equal S(u) → earliest-created node wins.

## 7. Evaluation and failures
- Every candidate gets a compatibility check first, then the same standard validation evaluation.
- Fixed for the whole run: data splits, seeds, aggregation, resource limits.
- For more specific evaluation information, see `5-in-search-eval.MD`.

## 8. Budgets and stopping
Record and enforce:
- The same max attempts per tree.
- Runtime and memory limit per evaluation.
- Total compute and/or wall-clock ceiling.

Stop when:
- Attempts are used up.
- A resource ceiling is hit.
- The user stops the run.
- An environment or evaluator problem makes fair comparison impossible.
- Early stopping: if scores do not improve for too long/code stagnates, stop the tree.

Save partial results and the stop reason.

## 9. Environment and integrity
- Use the agreed venv interpreter for all validation and evaluation.
- Propose package installs to the user before going ahead. Workers never change the environment.
- Freeze and record dependencies.
- A changed environment or evaluator = a new evaluation configuration. Never silently mix old and new scores.
- Candidates must not modify the evaluator, scoring, splits or other candidates.
- Use separate working and output locations.
- A venv doesn't isolate data or processes. Set up access limits and resource controls separately.

## 10. Saving and portability
- Save state after every dispatch and every finished evaluation.
- On resume, resolve pending work before dispatching new work.
- Record: protocol version, task config, evaluator version, code hashes, environment, prompts, provider/model (when known), all evaluation results.
- Goal: saved code can be re-evaluated reproducibly.
- See `3-saving-general.MD` for more detailed instructions.
