from xgboost import XGBRegressor


class Model(XGBRegressor):
    def fit(self, X, y, eval_set=None):
        return super().fit(X, y, eval_set=eval_set, verbose=False)


PARAM_SPACE = {
    'n_estimators': ('int', 100, 1000),
    'max_depth': ('int', 3, 10),
    'learning_rate': ('loguniform', 0.01, 0.3),
    'subsample': ('uniform', 0.6, 1.0),
    'objective': 'reg:squarederror',
    'early_stopping_rounds': 10,
    'n_jobs': 4,
    'random_state': 42,
}
