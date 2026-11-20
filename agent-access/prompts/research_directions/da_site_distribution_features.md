# Site-level descriptors of the covariate distribution as features

## Idea
Describe each site by summaries of its covariate distribution P_X (for example means,
standard deviations, quantiles, correlations between covariates, or low-dimensional
kernel embedding coordinates), computed from that site's own covariates only, and add
them as extra columns on every row of the site. For validation sites, compute the same
summaries at prediction time from their rows, grouped by `envs`.

Why this should help at unseen sites: the same weather can produce different ET at
different sites (climate, soils, vegetation). Site-level descriptors let the model learn
how the covariate-to-ET relation changes with the site, and they need no labels.

## Additional notes
- The descriptors are constant within a site, so with ~150 training sites they can act
  as a site ID and the model overfits the training sites. Regularise them more strongly
  than the hourly covariates, for example by restricting their interactions, sampling
  them less often, or computing them from random subsets or time windows of each site.
