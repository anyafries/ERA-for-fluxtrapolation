from sklearn.linear_model import HuberRegressor


class Model(HuberRegressor):
    standardize = True


PARAM_SPACE = {
    'alpha': ('loguniform', 1e-3, 1e2),
    'epsilon': ('uniform', 1.1, 2.0),
}
