# Temporal smoothing of a pooled model's daily predictions

## Idea
Train a strong pooled model (for example hist XGBoost) on the hourly rows. At prediction
time, use `envs` and `times` to group its predictions by site and day, and smooth each
site's daily mean prediction over neighbouring days. Specifically, blend the smoothed daily
mean with the raw one, and shift every hour of the day by the difference: the diurnal shape
stays as predicted and only the daily level moves.

Why this should help at unseen sites: ET has memory (soil moisture, canopy state) that the
covariates of a single hour do not capture, so hour-by-hour predictions are noisy at the
daily scale. Averaging over neighbouring days removes part of that noise and needs no
labels at the new site.

Fit the smoothing parameters on the training sites, never on `eval_set` targets. In-sample
predictions of the pooled model are close to perfect, so parameters fitted on them would be
≈ no smoothing. Instead, split the training sites into a few groups, refit the base model
without each group, predict the held-out group, and choose the parameters to minimise the
mean daily RMSE over training sites on these out-of-fold predictions.

## Additional notes
- By default, training hours with gap-filled ET are dropped, while at predict time all
  hours are present. Set `remove_missing_target = False` to get complete hourly series in
  `fit` as well, so daily means are computed over the same hours in training and
  prediction; mask the NaN targets out of the loss.
