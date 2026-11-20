import lightgbm as lgb  # pip install lightgbm


class Model(lgb.LGBMRegressor):
    def fit(self, X, y, eval_set=None):
        return super().fit(X, y, eval_set=eval_set, eval_metric='rmse', callbacks=[
            lgb.early_stopping(stopping_rounds=10), lgb.log_evaluation(period=0)])


PARAM_SPACE = {
    'n_estimators': ('int', 100, 500),
    'learning_rate': ('loguniform', 0.05, 0.2),
    'num_leaves': ('int', 15, 65),
    'max_depth': ('int', 3, 12),
    'min_child_samples': ('int', 5, 30),
    'colsample_bytree': ('uniform', 0.6, 1.0),
    'objective': 'regression',
    'boosting_type': 'goss',
    'verbosity': -1,
    'n_jobs': 4,
    'random_state': 42,
}
