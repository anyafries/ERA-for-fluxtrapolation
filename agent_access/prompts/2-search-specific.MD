# Run config (v0.1)

## Trees
- 1 tree for each MD file in `prompts/research_directions`

## Selection
- c = 1.5.

## Budgets
- Attempts per tree: 4 
- Per evaluation (i.e., fitting the model, making predictions, and scoring them): 30 min timeout. Memory: not enforced, log it if measurable.
- Total cap: 2 h of evaluation wall-clock. Don't start a new evaluation with < 30 min left.
- Concurrency: 1 worker, 1 evaluation at a time.
- If Claude usage limits reach >80% pause, notify, and ask if you should continue or stop the search.

## Shortlist
- Max 3 finalists per tree, ranked by the primary metric given in `4-task-description.MD`.
- Eligible: status `ok`.