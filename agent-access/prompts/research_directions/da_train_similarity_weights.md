# Similarity-weighted training towards the target sites

## Idea
At prediction time, use `envs` to group the validation rows by site and describe each
site's covariate distribution P_X (for example a kernel mean embedding or summary
statistics). Then fit a model on the training sites with weights that favour training
sites (or rows) whose covariate distribution is similar to the target's, so the model
spends its capacity on the part of the training data that resembles the new site. This
can be done per target site, or once for groups of similar target sites.

Why this should help at unseen sites: a pooled model fits the average training site,
which can be far from a given new site. Weighting towards similar training sites reduces
that mismatch, and only needs the target's covariates, not its labels.

## Additional notes
- This fits models inside `predict`, which counts towards the time limit. Keep the
  number of weighted fits small (for example group the target sites, subsample rows,
  or warm-start from a pooled model).
- Very concentrated weights leave only a few training sites; keep some weight on all sites.
