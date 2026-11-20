# Temporal context from each site's own time series

## Idea
Use `envs` and `times` to put each site's rows in time order and give the model
information about the recent conditions at the same site, for example lagged or rolling
summaries of the meteorological and satellite covariates, cumulative dryness indicators,
or a sequence model over each site's time series.

Why this should help at unseen sites: ET depends on antecedent conditions such as soil
moisture and canopy state, which the covariates of a single hour do not capture.
Features of the recent past act as proxies for this memory and are available at any site.

## Additional notes
- By default, training hours with gap-filled ET are dropped, while at predict time all
  hours are present. Set `remove_missing_target = False` to get complete hourly series in
  `fit` as well, so temporal features are computed the same way in training and
  prediction; mask the NaN targets out of the loss.
