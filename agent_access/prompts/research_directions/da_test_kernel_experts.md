# Similarity-weighted combination of site models at test time

## Idea
Fit one model per training site (or per group of similar training sites). At prediction
time, use `envs` to group the validation rows by site, compare each validation site's
covariate distribution P_X with those of the training sites (for example via kernel mean
embeddings and MMD), and predict with a similarity-weighted combination of the site
models.

Why this should help at unseen sites: a site's relation between covariates and ET is
best captured by models of sites that look like it. Weighting the experts by
distributional similarity adapts the prediction to the new site without needing its
labels.

## Additional notes
- Fitting ~150 site models takes time and would be repeated in every hyperparameter
  draw. Keep the fitted site models in an in-memory cache (for example a module-level
  dict keyed by the site and the site-model settings), check whether a fit exists before
  fitting, and reuse it.
- If the one-hot PFT block is standardised like the other features, it dominates the
  distances between sites; consider scaling it down or leaving it out of the similarity.
- How many site models to keep (all, top-k, weight sharpness) is a key choice.
