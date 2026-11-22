# Specific details for after the search (v0.1)

## on the tree visualization
Produce one interactive page (published as an artifact when available) with every tree of the run.

**Views**
- One view per metric: `skill` and `skill_q90`, with a toggle between them.
- Each tree drawn separately with parent–child edges; root marked and labelled with its research direction.

**Colour**
- Diverging scale centred on the reference baseline named in `4-task-description.MD` (i.e., XGBoost): neutral grey = reference, red = worse, green = better.
- Legend shows the low end, the reference value and the high end, and states that higher is better.
- Failed, cancelled/not-evaluated and pending nodes use outline styles (dotted/dashed, no fill), never a colour from the score scale.
- Each node is labelled with its ID and its value for the current metric.

**Node details (on click or keyboard select)**
- Status, turn type (root/expand/repair), primary and tail scores, evaluation minutes.
- The worker's method summary, plus (for finalists) the code-derived description from §5, labelled separately.
- Per-scale scores next to the reference, with a `node − reference` column coloured green/red.