# After-search reporting (v0.2)

## Tree visualisation
Produce one interactive page (published as an artifact when available) with every tree of the run.

**Views**
- Default to the primary metric defined in `4-task-description.MD`. Add a selector for any additional metrics designated for a separate view that have results.
- Draw each tree separately with parent–child edges. Mark roots and finalists distinctly and label each root with its research direction.

**Colour**
- Use one colour scale per metric across all trees. When the task defines a reference value for that metric, centre a diverging scale on it. Use grey for the reference, red for worse scores and green for better ones according to the metric's direction. Use a sequential scale when there is no reference value.
- The legend shows the range, the reference value if present, and whether higher or lower is better.
- Failed, cancelled/not-evaluated and pending nodes use outline styles (dotted/dashed, no fill), never a colour from the score scale.
- Each node is labelled with its ID and its value for the current metric.

**Node details (on click or keyboard select)**
- Status, turn type (root/expand/repair), available validation metrics and evaluation time.
- The worker's method summary, plus (for finalists) the code-derived description from `3-saving-general.MD`, labelled separately.
- Where a matching reference score exists, show it next to the candidate's score and show the difference. Use the metric's direction to mark whether the difference is better or worse, when that direction is defined.
